"""Host-only RED contract for #1285 offline wheel validation and installation.

Infrastructure only: no Genia syntax, semantics, host capability or MCP profile
change. Existing design preflight applies; M1/M2 and low corrections are authorized
by issuecomment-6644232395. Tests use unittest and already acquired hash-pinned
tools, never network/resolution. GENIA_FRONTEND_INPUTS selects that wheel directory;
GENIA_FRONTEND_UV selects the exact pinned uv executable. No image is involved.
"""

import base64
import csv
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'frontend'))


def make_wheel(folder, name='alpha', files=None, extra=(), mutate_record=None):
    """Create a tiny valid wheel, with optional malicious members/RECORD mutation.

    Returns an artifact row including actual archive hash/size, so malformed
    content controls cannot stop solely at an outdated outer hash.
    """
    stem = f'{name}-1.0'
    content = {
        f'{name}/__init__.py': (b'value = 1\n', 0o100644),
        f'{stem}.dist-info/METADATA': (f'Metadata-Version: 2.1\nName: {name}\nVersion: 1.0\n'.encode(), 0o100644),
        f'{stem}.dist-info/WHEEL': (b'Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n', 0o100644),
    }
    content.update(files or {})
    rows = []
    for path, (data, _) in content.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('=')
        rows.append([path, 'sha256=' + digest, str(len(data))])
    rows.append([f'{stem}.dist-info/RECORD', '', ''])
    if mutate_record:
        mutate_record(rows)
    stream = io.StringIO(newline='')
    csv.writer(stream, lineterminator='\n').writerows(rows)
    content[f'{stem}.dist-info/RECORD'] = (stream.getvalue().encode(), 0o100644)
    path = folder / f'{stem}-py3-none-any.whl'
    with warnings.catch_warnings(), zipfile.ZipFile(path, 'w') as wheel:
        warnings.simplefilter('ignore', UserWarning)
        for member, (data, mode) in [*content.items(), *extra]:
            info = zipfile.ZipInfo(member)
            info.create_system = 3
            info.external_attr = mode << 16
            wheel.writestr(info, data)
    return {'name': name, 'version': '1.0', 'filename': path.name,
            'path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


class FrontendContract(unittest.TestCase):
    """Exercise real destination writes, not a mock installer or resolver."""

    def setUp(self):
        """Each test owns a fresh tree; import failure is the initial RED signal."""
        self.temp = tempfile.TemporaryDirectory(prefix='genia-frontend-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old_umask = os.umask(0o022)
        self.addCleanup(os.umask, self.old_umask)
        self.api = importlib.import_module('offline_install')
        self.prefix = self.root / 'venv'

    def tools(self):
        """Bootstrap only the pinned installer into the test's own tools root."""
        pins = json.loads((HERE / 'pins.json').read_text())
        inputs = Path(os.environ['GENIA_FRONTEND_INPUTS'])
        row = {**pins['installer'], 'path': str(inputs / pins['installer']['filename'])}
        target = self.root / 'installer-tools'
        self.api.bootstrap(row, target)
        return target

    def install(self, rows, editable_source=None):
        """Prepare the complete batch before any venv/scaffold writes."""
        plan = self.api.prepare(rows, self.prefix, editable_source=editable_source)
        self.api.install(plan, self.tools(), Path(os.environ['GENIA_FRONTEND_UV']), Path(sys.executable))
        return plan

    def assert_rejected(self, row):
        """A valid first wheel plus malformed last input must leave no output."""
        good = make_wheel(self.root, name='aaa')
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.api.prepare([good, row], self.prefix)
        self.assertFalse(self.prefix.exists())

    def test_safe_unrecorded_directory_is_nonpayload_and_creates_nothing(self):
        row = make_wheel(self.root, extra=[('empty/', (b'', 0o040755))])
        self.install([row])
        self.assertFalse((self.prefix / 'lib/python3.12/site-packages/empty').exists())

    def test_unsafe_members_rejected_before_any_output(self):
        cases = [('../escape', b'x', 0o100644), ('/escape', b'x', 0o100644),
                 ('alpha/../escape', b'x', 0o100644), ('alpha//x', b'x', 0o100644),
                 ('alpha/./x', b'x', 0o100644), ('alpha\\x', b'x', 0o100644),
                 ('C:/x', b'x', 0o100644), ('alpha/link', b'target', 0o120777),
                 ('alpha/device', b'', 0o020644), ('alpha/setuid', b'x', 0o104755),
                 ('empty/', b'x', 0o040755), ('empty/', b'', 0o040777),
                 ('empty/', b'', 0o100644), ('alpha/no-slash', b'', 0o040755)]
        for member, data, mode in cases:
            with self.subTest(member=member, mode=mode):
                row = make_wheel(self.root, extra=[(member, (data, mode))])
                self.assert_rejected(row)

    def test_duplicate_regular_and_directory_entries_rejected(self):
        for extras in [[('alpha/__init__.py', (b'bad', 0o100644))],
                       [('empty/', (b'', 0o040755)), ('empty/', (b'', 0o040755))]]:
            with self.subTest(extras=extras):
                self.assert_rejected(make_wheel(self.root, extra=extras))

    def test_record_bidirectional_coverage_duplicate_and_digest_controls(self):
        def remove(rows):
            rows.pop(0)

        def duplicate(rows):
            rows.append(rows[0])

        def phantom(rows):
            rows.append(['missing.py', 'sha256=' + 'A' * 43, '1'])

        def tamper(rows):
            rows[0][1] = 'sha256=' + 'A' * 43

        def size(rows):
            rows[0][2] = '999'

        def self_hash(rows):
            rows[-1][1] = 'sha256=' + 'A' * 43

        for mutation in [remove, duplicate, phantom, tamper, size, self_hash]:
            with self.subTest(mutation=mutation.__name__):
                self.assert_rejected(make_wheel(self.root, mutate_record=mutation))

    def test_bad_last_wheel_hash_missing_and_wrong_identity_zero_writes(self):
        row = make_wheel(self.root, name='zzz')
        for changed in [{'sha256': '0' * 64}, {'path': str(self.root/'missing.whl')},
                        {'name': 'other'}, {'version': '2.0'}, {'bytes': row['bytes']+1}]:
            with self.subTest(changed=changed):
                self.assert_rejected({**row, **changed})

    def test_data_scheme_bad_tag_and_generated_metadata_rejected(self):
        for files in [
            {'alpha-1.0.data/unknown/x': (b'x', 0o100644)},
            {'alpha-1.0.data/scripts/../x': (b'x', 0o100644)},
            {'alpha-1.0.dist-info/INSTALLER': (b'pretend', 0o100644)},
            {'alpha-1.0.dist-info/WHEEL': (b'Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: cp311-cp311-win_amd64\n', 0o100644)},
        ]:
            with self.subTest(files=list(files)):
                self.assert_rejected(make_wheel(self.root, files=files))

    def test_collisions_file_parents_scripts_and_scaffold_rejected(self):
        first = make_wheel(self.root, files={'shared/x.py': (b'a', 0o100644)})
        for path in ['shared/x.py', 'shared', 'shared/x.py/child']:
            second = make_wheel(self.root, name='zzz', files={path: (b'a', 0o100644)})
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.api.prepare([first, second], self.prefix)
            self.assertFalse(self.prefix.exists())
        row = make_wheel(self.root, files={'alpha-1.0.data/scripts/python': (b'bad', 0o100755)})
        with self.assertRaises(ValueError):
            self.api.prepare([row], self.prefix)

    def test_existing_prefix_and_symlink_parent_rejected(self):
        row = make_wheel(self.root)
        self.prefix.mkdir()
        with self.assertRaises(ValueError):
            self.api.prepare([row], self.prefix)
        link = self.root/'link'; link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.api.prepare([row], link/'destination')

    def test_umask_override_fails_before_writes(self):
        row = make_wheel(self.root)
        for mask in [0o077, 0o002, 0o027]:
            with self.subTest(mask=oct(mask)):
                os.umask(mask)
                with self.assertRaises(ValueError):
                    self.api.prepare([row], self.prefix)
                self.assertFalse(self.prefix.exists())
        os.umask(0o022)

    def test_modes_wrappers_data_scripts_symlinks_and_record_validation(self):
        files = {'alpha/run.py': (b'print(1)\n', 0o100755),
                 'alpha-1.0.data/scripts/raw': (b'#!python\nprint(1)\n', 0o100755),
                 'alpha-1.0.dist-info/entry_points.txt': (b'[console_scripts]\nalpha = alpha:main\n', 0o100644)}
        self.install([make_wheel(self.root, files=files)])
        manifest = self.api.inventory(self.prefix)
        for name, item in manifest.items():
            expected = 0o755 if item['kind']=='directory' or name in ['bin/raw','bin/alpha','lib/python3.12/site-packages/alpha/run.py'] else 0o644
            if item['kind']=='symlink':
                self.assertEqual(item['mode'], 0o777)
            elif name.startswith('bin/activate'):
                self.assertEqual(item['mode'], 0o644)
            else:
                self.assertEqual(item['mode'], expected, name)
        self.assertGreater(self.api.verify_records(self.prefix), 5)
        self.assertFalse(list(self.prefix.rglob('*.pyc')))

    def test_explicit_posix_prefix_ignores_default_scheme(self):
        from unittest.mock import patch
        with patch('sysconfig.get_default_scheme', return_value='posix_local'):
            plan = self.api.prepare([make_wheel(self.root)], self.prefix)
        self.assertEqual(plan.scheme['purelib'], str(self.prefix/'lib/python3.12/site-packages'))
        self.assertEqual(plan.scheme['data'], str(self.prefix))
        self.assertEqual(plan.scheme['scripts'], str(self.prefix/'bin'))

    def test_live_editable_metadata_exact_bytes_and_no_reinstall(self):
        source = self.root/'source'; (source/'src/alpha').mkdir(parents=True)
        (source/'src/alpha/__init__.py').write_text('value=41\n')
        row = make_wheel(self.root, name='genia', files={'_editable.pth': (str(source/'src').encode()+b'\n', 0o100644)})
        self.install([row], editable_source=source)
        direct = self.prefix/'lib/python3.12/site-packages/genia-1.0.dist-info/direct_url.json'
        self.assertEqual(direct.read_bytes(), json.dumps({'dir_info':{'editable':True},'url':source.as_uri()},sort_keys=True,separators=(',',':')).encode())
        python = self.prefix/'bin/python'
        self.assertEqual(subprocess.check_output([python,'-I','-B','-c','import alpha;print(alpha.value)']), b'41\n')
        (source/'src/alpha/new.py').write_text('value=42\n')
        self.assertEqual(subprocess.check_output([python,'-I','-B','-c','import alpha.new;print(alpha.new.value)']), b'42\n')
        self.api.verify_records(self.prefix)

    def test_different_input_timestamps_and_reversed_wheel_order_are_equal(self):
        rows = [make_wheel(self.root), make_wheel(self.root, name='zzz')]
        plan = self.install(list(reversed(rows)))
        first = self.api.inventory(self.prefix)
        self.assertEqual([r.row['name'] for r in plan.wheels], ['alpha','zzz'])
        shutil.rmtree(self.prefix)
        for row in rows:
            data = Path(row['path']).read_bytes(); Path(row['path']).unlink(); Path(row['path']).write_bytes(data)
            os.utime(row['path'], (1000000000,1000000000))
        # Tools were validated once; no need to replace their read-only extraction.
        plan = self.api.prepare(rows,self.prefix)
        self.api.install(plan,self.root/'installer-tools',Path(os.environ['GENIA_FRONTEND_UV']),Path(sys.executable))
        self.assertEqual(first,self.api.inventory(self.prefix))

    def test_all_47_pins_and_15_executable_members_match_plan(self):
        pins=json.loads((HERE/'pins.json').read_text()); inputs=Path(os.environ['GENIA_FRONTEND_INPUTS'])
        runtime=[{**r,'path':str(inputs/r['filename'])} for r in pins['runtime_wheels'] if r['target_selected']]
        backend=[{**r,'path':str(inputs/r['filename'])} for r in pins['backend_wheels']]
        plan=self.api.prepare(runtime,self.prefix)
        self.api.prepare(backend,self.root/'builder')
        executables=[]
        for row in runtime:
            with zipfile.ZipFile(row['path']) as wheel:
                executables.extend((row['filename'],i.filename) for i in wheel.infolist() if stat.S_ISREG(i.external_attr>>16) and (i.external_attr>>16)&0o111)
        self.assertEqual(len(executables),15)
        self.assertEqual(sum(v['mode']==0o755 for v in plan.files.values()),29)  # 15 ZIP executable payloads + 14 generated runtime wrappers
        expected=json.loads((HERE/'frontend/expected-modes.json').read_text())
        self.assertEqual(expected['runtime_files'],plan.files)

    def tearDown(self):
        """Make only owned read-only test tool directories removable by cleanup."""
        for path in self.root.rglob('*'):
            if path.is_dir() and not path.is_symlink():
                path.chmod(0o755)


if __name__ == '__main__':
    unittest.main()
