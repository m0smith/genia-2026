"""Public-only installation spike, not a production runner or benchmark.

Use already downloaded, hash-verified pins. Recreate only owned scratch paths,
compare complete installed trees under the same absolute prefix, and preserve
all results. No network, image construction, dependency resolution by the
alternative, third-party source builds, metadata deletion or normalization.
The sole source build is the approved Genia PEP-660 editable wheel.
"""

import argparse
import base64
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import sysconfig
import tarfile
import zipfile

SOURCE_SHA = '9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90'
UV_SHA256 = '8a70db72685b7138121bfcda71fa1a00cb709ed9f1fdc4ecf1dd871e8e167e52'
INSTALLER_SHA256 = '05d1933f0a5ba7d8d6296bb6d5018e7c94fa473ceb10cf198a92ccea19c27b53'


def sha(data):
    """Return exact-byte SHA256 without interpreting package contents."""
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    """Persist public evidence immediately so failures survive later assertions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def reset(root, name):
    """Recreate one named scratch child, refusing roots and arbitrary paths."""
    assert name in {'prefix', 'build-env', 'stage', 'source', 'editable-wheel'}
    assert (root / 'spike-owned-directory').is_file()
    path = root / name
    assert path.parent == root and not path.is_symlink()
    if path.exists():
        shutil.rmtree(path)
    path.mkdir()
    return path


def unpack_wheel(archive, destination):
    """Extract a verified tool wheel into isolated scratch, rejecting traversal."""
    with zipfile.ZipFile(archive) as wheel:
        for name in wheel.namelist():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
        wheel.extractall(destination)


def wheel_worker(config):
    """Install exact wheels with PyPA installer API and no bytecode/resolver.

    Archive SHA256 and every wheel RECORD entry are checked before writes.
    INSTALLER is declared at initial installation. The Genia editable wheel
    additionally receives standard PEP-610 source-dir metadata at install time;
    no existing installed metadata is patched or discarded.
    """
    sys.path.insert(0, config['installer_library'])
    import installer
    from installer.destinations import SchemeDictionaryDestination
    from installer.sources import WheelFile

    assert installer.__version__ == '0.7.0'
    prefix = config['prefix']
    scheme = sysconfig.get_paths(vars={'base': prefix, 'platbase': prefix})
    scheme['headers'] = prefix + '/include/python3.12'
    for row in config['wheels']:
        archive = Path(row['path'])
        assert sha(archive.read_bytes()) == row['sha256']
        metadata = {'INSTALLER': b'installer\n'}
        if row.get('editable_source'):
            metadata['direct_url.json'] = json.dumps({
                'url': Path(row['editable_source']).as_uri(),
                'dir_info': {'editable': True}}, sort_keys=True, separators=(',', ':')).encode() + b'\n'
        with WheelFile.open(archive) as source:
            source.validate_record(validate_contents=True)
            destination = SchemeDictionaryDestination(
                scheme_dict=scheme, interpreter=prefix + '/bin/python',
                script_kind='posix', bytecode_optimization_levels=())
            installer.install(source, destination, metadata)
    print(json.dumps({'installer': installer.__version__, 'wheels_installed': len(config['wheels'])}))


def tree_manifest(directory):
    """List every file/link with mode/hash, plus relevant generated metadata."""
    files, metadata = {}, {}
    for path in sorted(directory.rglob('*')):
        relative = path.relative_to(directory).as_posix()
        if path.is_symlink():
            files[relative] = {'kind': 'symlink', 'target': os.readlink(path)}
        elif path.is_file():
            data = path.read_bytes()
            files[relative] = {'kind': 'file', 'bytes': len(data), 'sha256': sha(data),
                               'mode': stat.S_IMODE(path.stat().st_mode)}
            if path.name in {'RECORD', 'INSTALLER', 'direct_url.json', 'uv_cache.json', 'uv_build.json'} or path.suffix == '.pth':
                metadata[relative] = data.decode('utf-8')
    return {'files': files, 'metadata': metadata}


def compare(left, right):
    """Compare all path sets, file bytes and modes, excluding nothing."""
    a, b = tree_manifest(left), tree_manifest(right)
    changed = []
    for name in sorted(set(a['files']) | set(b['files'])):
        if a['files'].get(name) != b['files'].get(name):
            changed.append(name)
        elif a['files'][name]['kind'] == 'file':
            assert (left / name).read_bytes() == (right / name).read_bytes()
    return {'strict_equal': not changed, 'paths_a': len(a['files']), 'paths_b': len(b['files']),
            'changed_paths': changed,
            'change_categories': {key: sum(Path(p).name == key for p in changed)
                                  for key in ['RECORD', 'INSTALLER', 'direct_url.json', 'uv_cache.json', 'uv_build.json']}}


def verify_installed_records(prefix):
    """Validate every nonempty installed RECORD hash and size within the prefix."""
    count = 0
    site = prefix / 'lib/python3.12/site-packages'
    for record in site.glob('*.dist-info/RECORD'):
        for name, checksum, size in csv.reader(io.StringIO(record.read_text())):
            path = (site / name).resolve()
            assert path.is_relative_to(prefix.resolve()), name
            assert path.is_file(), name
            if checksum:
                algorithm, expected = checksum.split('=', 1)
                digest = base64.urlsafe_b64encode(hashlib.new(algorithm, path.read_bytes()).digest()).decode().rstrip('=')
                assert digest == expected and path.stat().st_size == int(size), name
            count += 1
    return count


def main(args):
    """Run independent uv/installer pairs and retain full file/difference evidence."""
    repo, root = args.repo.resolve(), args.work.resolve()
    assert root != repo and root.is_relative_to(Path('/workspace/work'))
    root.mkdir(parents=True, exist_ok=True)
    (root / 'spike-owned-directory').touch()
    assert sha(args.uv.read_bytes()) == UV_SHA256
    assert sha(args.installer.read_bytes()) == INSTALLER_SHA256
    pins = json.loads((repo / '.genia/experiments/issue-1285/public-runner/pins.json').read_text())
    backend = pins['backend_wheels']
    runtime = [row for row in pins['runtime_wheels'] if row['target_selected']]
    union = {(row['name'], row['version']): row for row in [*runtime, *backend]}
    assert len(runtime) == 43 and len(union) == 47
    tool_lib = root / 'installer-library'
    tool_lib.mkdir(exist_ok=True)
    unpack_wheel(args.installer, tool_lib)
    env = os.environ.copy()
    for key in ['PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV', 'CONDA_PREFIX', 'UV_PROJECT', 'UV_PYTHON', 'UV_PROJECT_ENVIRONMENT', 'UV_WORKING_DIRECTORY']:
        env.pop(key, None)
    env.update(UV_OFFLINE='1', UV_PYTHON_DOWNLOADS='never', PYTHONDONTWRITEBYTECODE='1',
               PYTHONNOUSERSITE='1', PYTHONHASHSEED='0', TZ='UTC', LANG='C.UTF-8',
               SOURCE_DATE_EPOCH=str(pins['source']['source_date_epoch']))
    results = {'scope': 'host scratch, no image or strategy adoption', 'host_python': sys.version,
               'commands': [], 'cases': {}, 'comparisons': {}}
    manifests = {}

    def command(label, argv, cwd=None):
        """Capture bounded argv/results immediately; any unexpected failure stops."""
        proc = subprocess.run([str(a) for a in argv], cwd=cwd or root, env=env,
                              capture_output=True, timeout=90)
        row = {'label': label, 'argv': [str(a) for a in argv], 'cwd': str(cwd or root),
               'exit_code': proc.returncode, 'stdout': proc.stdout.decode(), 'stderr': proc.stderr.decode()}
        results['commands'].append(row)
        write_json(root / 'results.json', results)
        assert proc.returncode == 0, row
        return proc.stdout

    def install_uv(label, python, rows):
        """Use local hashed wheels only; no dependency resolution or source builds."""
        req = root / (label + '.requirements.txt')
        req.write_text(''.join(f"{row['path']} --hash=sha256:{row['sha256']}\n" for row in rows))
        command(label, [args.uv, '--no-config', 'pip', 'install', '--python', python,
                        '--offline', '--no-index', '--require-hashes', '--only-binary', ':all:',
                        '--no-deps', '--link-mode', 'copy', '-r', req])

    def snapshot(label, prefix):
        """Retain complete copies within measured 1 GiB / 200000-path caps."""
        destination = root / 'snapshots' / label
        assert not destination.exists(), 'Use a fresh work root; never replace evidence'
        shutil.copytree(prefix, destination, symlinks=True)
        manifests[label] = tree_manifest(destination)
        total = sum(row.get('bytes', 0) for value in manifests.values() for row in value['files'].values())
        assert total <= 1024 * 1024 * 1024 and sum(len(v['files']) for v in manifests.values()) <= 200000
        raw = json.dumps(manifests, sort_keys=True, separators=(',', ':')).encode()
        (root / 'file-manifests.json.gz').write_bytes(gzip.compress(raw, mtime=0))

    for strategy in ['uv', 'installer']:
        for trial in ['A', 'B']:
            case = strategy + '-' + trial
            env['UV_CACHE_DIR'] = str(root / ('cache-' + case))
            stage = reset(root, 'stage')
            source = reset(root, 'source')
            prefix = reset(root, 'prefix')
            reset(root, 'build-env')
            editable_dir = reset(root, 'editable-wheel')
            archive = subprocess.check_output(['git', 'archive', SOURCE_SHA], cwd=repo)
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                tar.extractall(source, filter='data')
            lock = (repo / pins['source']['lock_path']).read_bytes()
            assert sha(lock) == pins['source']['lock_sha256']
            (source / 'uv.lock').write_bytes(lock)
            (source / 'uv.lock').chmod(0o444)
            source_before = tree_manifest(source)['files']
            staged = []
            for row in sorted(union.values(), key=lambda value: value['filename']):
                origin = args.wheels / row['filename']
                if not origin.exists():
                    origin = args.backend / row['filename']
                data = origin.read_bytes()
                assert len(data) == row['bytes'] and sha(data) == row['sha256']
                target = stage / row['filename']
                target.write_bytes(data)
                os.utime(target, ns=(int(env['SOURCE_DATE_EPOCH']) * 10**9,) * 2)
                staged.append({**row, 'path': str(target), 'ctime_ns': target.stat().st_ctime_ns,
                               'mtime_ns': target.stat().st_mtime_ns})
            case_data = {'wheels': [{'name': r['name'], 'version': r['version'], 'sha256': r['sha256'],
                                     'ctime_ns': r['ctime_ns'], 'mtime_ns': r['mtime_ns']} for r in staged],
                         'source_pyproject_ctime_ns': (source / 'pyproject.toml').stat().st_ctime_ns,
                         'source_src_ctime_ns': (source / 'src').stat().st_ctime_ns}
            results['cases'][case] = case_data
            python = prefix / 'bin/python'
            command(case + '-venv', [args.uv, '--no-config', 'venv', '--offline', '--no-python-downloads',
                                    '--python', sys.executable, prefix])
            if strategy == 'uv':
                install_uv(case + '-wheels', python, staged)
            else:
                config = {'prefix': str(prefix), 'installer_library': str(tool_lib),
                          'wheels': [r for r in staged if (r['name'], r['version']) in
                                     {(v['name'], v['version']) for v in runtime}]}
                write_json(root / 'worker-config.json', config)
                command(case + '-wheels', [sys.executable, '-I', '-S', '-B', Path(__file__).resolve(),
                                          '--worker', root / 'worker-config.json'])
            snapshot(case + '-wheels', prefix)
            if strategy == 'uv':
                command(case + '-editable', [args.uv, '--no-config', 'pip', 'install', '--python', python,
                                            '--offline', '--no-index', '--no-deps', '--no-build-isolation', '-e', source])
                command(case + '-remove-backend', [args.uv, '--no-config', 'pip', 'uninstall', '--python', python,
                                                  '--offline', 'editables', 'hatchling', 'tomlkit', 'trove-classifiers'])
            else:
                builder_python = root / 'build-env/bin/python'
                command(case + '-builder-venv', [args.uv, '--no-config', 'venv', '--offline', '--no-python-downloads',
                                               '--python', sys.executable, root / 'build-env'])
                install_uv(case + '-backend', builder_python, [r for r in staged if r['name'] in {b['name'] for b in backend}])
                code = 'import hatchling.build,json,sys; print(json.dumps({"requires":hatchling.build.get_requires_for_build_editable({}),"wheel":hatchling.build.build_editable(sys.argv[1])}))'
                output = command(case + '-build-editable-wheel', [builder_python, '-I', '-B', '-c', code, editable_dir], cwd=source)
                build = json.loads(output)
                assert build['requires'] == ['editables~=0.3']
                wheel = editable_dir / build['wheel']
                case_data['editable_wheel_sha256'] = sha(wheel.read_bytes())
                config['wheels'] = [{'path': str(wheel), 'sha256': case_data['editable_wheel_sha256'],
                                     'editable_source': str(source)}]
                write_json(root / 'worker-config.json', config)
                command(case + '-install-editable-wheel', [sys.executable, '-I', '-S', '-B', Path(__file__).resolve(),
                                                         '--worker', root / 'worker-config.json'])
                case_data['installed_RECORD_entries_verified'] = verify_installed_records(prefix)
            command(case + '-pip-check', [args.uv, '--no-config', 'pip', 'check', '--python', python, '--offline'])
            code = 'import genia,importlib.metadata,json,sys,site; print(json.dumps({"genia_file":genia.__file__,"sys_path":sys.path,"user_site":site.ENABLE_USER_SITE,"distributions":sorted((d.metadata["Name"].lower().replace("_","-"),d.version) for d in importlib.metadata.distributions())}))'
            imported = json.loads(command(case + '-import', [python, '-I', '-B', '-c', code]))
            assert Path(imported['genia_file']).is_relative_to(source / 'src') and not imported['user_site']
            expected = sorted([(r['name'], r['version']) for r in runtime] + [('genia', '0.1.14')])
            assert imported['distributions'] == [list(pair) for pair in expected]
            case_data['import_check'] = imported
            command(case + '-cli', [python, '-I', '-B', '-m', 'genia.interpreter', '-c', '1 + 1'])
            command(case + '-public-demo', [python, '-I', '-B', '-m', 'genia.interpreter', source / 'examples/validated_pipeline_demo.genia'])
            assert tree_manifest(source)['files'] == source_before, 'Approved exported source/lock mutated'
            snapshot(case + '-editable', prefix)
            write_json(root / 'results.json', results)
        for stage_name in ['wheels', 'editable']:
            results['comparisons'][strategy + '-' + stage_name] = compare(
                root / 'snapshots' / (strategy + '-A-' + stage_name),
                root / 'snapshots' / (strategy + '-B-' + stage_name))
        a = {r['name']: r for r in results['cases'][strategy + '-A']['wheels']}
        b = {r['name']: r for r in results['cases'][strategy + '-B']['wheels']}
        assert all(a[n]['ctime_ns'] != b[n]['ctime_ns'] and a[n]['mtime_ns'] == b[n]['mtime_ns'] for n in a)
        write_json(root / 'results.json', results)
    raw = json.dumps(manifests, sort_keys=True, separators=(',', ':')).encode()
    compressed = gzip.compress(raw, mtime=0)
    (root / 'file-manifests.json.gz').write_bytes(compressed)
    results['file_evidence'] = {'filename': 'file-manifests.json.gz', 'sha256': sha(compressed),
                               'uncompressed_sha256': sha(raw), 'bytes': len(compressed),
                               'cases': list(manifests)}
    write_json(root / 'results.json', results)
    print(json.dumps(results['comparisons'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--repo', type=Path, default=Path('/workspace/genia-2026'))
    parser.add_argument('--work', type=Path, default=Path('/workspace/work/issue-1285-deterministic/run'))
    parser.add_argument('--uv', type=Path, default=Path('/workspace/work/issue-1285-pins/tools/uv'))
    parser.add_argument('--installer', type=Path, default=Path('/workspace/work/issue-1285-deterministic/installer-0.7.0-py3-none-any.whl'))
    parser.add_argument('--wheels', type=Path, default=Path('/workspace/work/issue-1285-pins/wheelhouse'))
    parser.add_argument('--backend', type=Path, default=Path('/workspace/work/issue-1285-public-runner'))
    arguments = parser.parse_args()
    if arguments.worker:
        wheel_worker(json.loads(arguments.worker.read_text()))
    else:
        main(arguments)
