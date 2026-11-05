"""RECORD-listed R1–R5 regression controls, authorized by #1285 comment6658033204.

Host infrastructure only; no language or MCP change. Each rejected batch must
leave its destination absent. Real uv/build probes require the exact pinned
artifacts selected by the same environment variables as the original suite.
"""

import hashlib
import importlib
import os
from pathlib import Path
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_offline_install as original
from test_offline_install import HERE, make_wheel


class RevisionContract(unittest.TestCase):
    """Discriminate individual validators without generic RECORD coverage masking."""

    setUp = original.FrontendContract.setUp
    tearDown = original.FrontendContract.tearDown
    tools = original.FrontendContract.tools
    install = original.FrontendContract.install

    def reject(self, row, diagnostic, **kwargs):
        """Validate a genuine bad-last batch and assert its precise error/no writes."""
        good = make_wheel(self.root, name="aaa")
        with self.assertRaisesRegex(ValueError, diagnostic):
            self.api.prepare([good, row], self.prefix, **kwargs)
        self.assertFalse(self.prefix.exists())
        self.assertFalse((self.root / "installer-tools").exists())

    def test_record_listed_member_validations(self):
        """Reject unsafe recorded members at their individual validator."""
        cases = [
            ("alpha/setuid", b"x", 0o104755, "unsafe member type/mode"),
            ("alpha/setgid", b"x", 0o102755, "unsafe member type/mode"),
            ("alpha/sticky", b"x", 0o101644, "unsafe member type/mode"),
            ("alpha/link", b"target", 0o120777, "unsafe member type/mode"),
            ("alpha/device", b"x", 0o020644, "unsafe member type/mode"),
            ("alpha/untyped", b"x", 0o755, "untyped executable member"),
            ("alpha/a.pyc", b"x", 0o100644, "bytecode payload forbidden"),
            ("alpha/a.pyo", b"x", 0o100644, "bytecode payload forbidden"),
            (
                "alpha-1.0.dist-info/REQUESTED",
                b"",
                0o100644,
                "unexpected generated metadata/signature",
            ),
            (
                "alpha-1.0.dist-info/INSTALLER",
                b"x",
                0o100644,
                "unexpected generated metadata/signature",
            ),
            ("alpha-1.0.dist-info.alias/x", b"x", 0o100644, "dist-info prefix alias"),
            ("alpha-1.0.data.alias/data/x", b"x", 0o100644, r"unexpected .data directory"),
            ("other-1.0.data/data/x", b"x", 0o100644, r"unexpected .data directory"),
            ("alpha-1.0.data/unknown/x", b"x", 0o100644, r"invalid .data scheme"),
            ("../escape", b"x", 0o100644, "noncanonical path"),
            ("alpha//x", b"x", 0o100644, "noncanonical path"),
            ("alpha\\x", b"x", 0o100644, "unsafe path"),
        ]
        for name, content, mode, diagnostic in cases:
            with self.subTest(member=name, diagnostic=diagnostic):
                self.reject(make_wheel(self.root, files={name: (content, mode)}), diagnostic)

    def test_wheel_and_metadata_headers(self):
        """Reject unsupported and ambiguous identity/format metadata."""
        cases = [
            (
                "WHEEL",
                b"Wheel-Version: 2.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
                "unsupported WHEEL format",
            ),
            (
                "WHEEL",
                b"Wheel-Version: 1.0\nRoot-Is-Purelib: maybe\nTag: py3-none-any\n",
                "unsupported WHEEL format",
            ),
            (
                "WHEEL",
                b"Root-Is-Purelib: true\nTag: py3-none-any\n",
                "missing/duplicate Wheel-Version",
            ),
            ("METADATA", b"Name: other\nVersion: 1.0\n", "METADATA identity mismatch"),
            ("METADATA", b"Name: alpha\nVersion: 2.0\n", "METADATA identity mismatch"),
            ("METADATA", b"Name: alpha\nName: alpha\nVersion: 1.0\n", "missing/duplicate Name"),
            ("METADATA", b"Name: alpha\n", "missing/duplicate Version"),
        ]
        for name, content, diagnostic in cases:
            with self.subTest(header=name, content=content):
                self.reject(
                    make_wheel(
                        self.root, files={f"alpha-1.0.dist-info/{name}": (content, 0o100644)}
                    ),
                    diagnostic,
                )

    def test_entrypoint_diagnostics(self):
        """Reject unsafe names, targets, identifiers and duplicate entries."""
        for content, diagnostic in [
            (b"[console_scripts]\n../escape = alpha:main\n", "unsafe entrypoint name"),
            (b"[console_scripts]\nalpha = alpha.main\n", "unsupported entrypoint target"),
            (b"[console_scripts]\nalpha = alpha:1main\n", "malformed entrypoint identifier"),
            (b"[console_scripts]\nalpha = alpha:main\nalpha = alpha:main\n", "malformed wheel:"),
        ]:
            with self.subTest(content=content):
                self.reject(
                    make_wheel(
                        self.root,
                        files={"alpha-1.0.dist-info/entry_points.txt": (content, 0o100644)},
                    ),
                    diagnostic,
                )

    def test_duplicate_distribution(self):
        """Reject repeated identities before reserving any destination."""
        row = make_wheel(self.root, name="aaa")
        self.reject(row, "duplicate distribution")

    def test_archive_limits(self):
        """Exercise compressed, expanded and aggregate size limits independently."""
        row = make_wheel(self.root)
        with patch.object(self.api, "MAX_ARCHIVE", row["bytes"] - 1):
            self.reject(row, "archive size mismatch/limit")
        with patch.object(self.api, "MAX_BATCH", 1):
            self.reject(row, "expanded archive limit")
        # Individual expanded archives fit; compressed batch total does not.
        good = make_wheel(self.root, name="aaa")
        with patch.object(self.api, "MAX_BATCH", max(row["bytes"], good["bytes"])):
            self.reject(row, "batch archive limit")

    def test_tag_checks_independent(self):
        """Separate filename agreement from actual target compatibility."""
        row = make_wheel(
            self.root,
            files={
                "alpha-1.0.dist-info/WHEEL": (
                    b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: cp311-cp311-win_amd64\n",
                    0o100644,
                )
            },
        )
        self.reject(row, "WHEEL/filename tag mismatch")
        path = Path(row["path"])
        changed = path.with_name("alpha-1.0-cp311-cp311-win_amd64.whl")
        path.rename(changed)
        self.reject(
            {**row, "path": str(changed), "filename": changed.name}, "incompatible target tag"
        )
        for tag in (
            "cp311-cp311-any",
            "py3-none-win_amd64",
            "cp313-abi3-manylinux_2_17_x86_64",
            "cp312-cp312-manylinux_2_42_x86_64",
        ):
            with self.subTest(tag=tag):
                self.assertFalse(self.api.compatible_tag(tag))

    def test_scaffold_directories_reserved_before_writes(self):
        """Reserve uv scaffold directories even without a planned bin child."""
        for name in ("bin", "lib", "lib/python3.12", self.api.SITE):
            with self.subTest(name=name):
                row = make_wheel(self.root, files={f"alpha-1.0.data/data/{name}": (b"x", 0o100644)})
                self.reject(row, "destination collision: " + name)

    def test_unsupported_compression_normalized(self):
        """Fail closed with ValueError for an actual unsupported ZIP method."""
        row = make_wheel(self.root)
        path = Path(row["path"])
        data = bytearray(path.read_bytes())
        # Patch both headers for a real unsupported compression, not a mock read.
        for signature, offset in ((b"PK\x03\x04", 8), (b"PK\x01\x02", 10)):
            start = data.index(signature)
            struct.pack_into("<H", data, start + offset, 99)
        path.write_bytes(data)
        row.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
        self.reject(row, "malformed wheel:.*compression")

    def test_root_harness_rejected_before_writes(self):
        """Reject root before accessing other arguments or creating work."""
        harness = importlib.import_module("verify_frontend")
        with patch.object(harness.os, "geteuid", return_value=0):
            with self.assertRaisesRegex(ValueError, "verification requires non-root"):
                harness.verify(type("Args", (), {"work": self.root / "work"})())
        self.assertFalse((self.root / "work").exists())

    def test_readonly_primary_error_preserved_and_modes_restored(self):
        """Keep the probe error when cleanup verification also fails."""
        harness = importlib.import_module("verify_frontend")
        self.prefix.mkdir()
        (self.prefix / "file").write_bytes(b"unchanged")
        original = self.api.inventory(self.prefix)
        real_inventory = self.api.inventory
        calls = []

        def inventory(path):
            """Force a cleanup discrepancy independently of the primary probe error."""
            calls.append(path)
            value = real_inventory(path)
            return value if len(calls) < 3 else {}

        with (
            patch.object(harness.frontend, "inventory", side_effect=inventory),
            patch.object(harness, "run", side_effect=RuntimeError("primary sentinel")),
        ):
            with self.assertRaisesRegex(RuntimeError, "primary sentinel"):
                harness.probe_readonly(self.prefix, self.root, Path("uv"), {}, [])
        self.assertEqual(original, self.api.inventory(self.prefix))

    def test_real_install_fresh_home_no_ambient_cache(self):
        """Exercise real pinned uv scaffold writes with a fresh HOME."""
        home = self.root / "home"
        home.mkdir()
        env = self.api.clean_environment() | {"HOME": str(home)}
        env.pop("UV_CACHE_DIR", None)
        with patch.dict(os.environ, env, clear=True):
            self.install([make_wheel(self.root)])
        self.assertEqual(list(home.rglob("*")), [], "uv persisted undeclared HOME bytes")

    def test_real_build_cache_argument_without_ambient_cache(self):
        """Exercise all real build calls with cache supplied only as an argument."""
        stage = Path(os.environ["GENIA_FRONTEND_STAGE"])
        home = self.root / "home"
        home.mkdir()
        # Host orchestration explicitly permits only /workspace/work children.
        root = HERE.parents[3] / ".genia/process/tmp" / self.root.name
        self.addCleanup(shutil_remove_owned, root)
        env = self.api.clean_environment() | {"HOME": str(home), "TMPDIR": str(self.root)}
        env.pop("UV_CACHE_DIR", None)
        receipt = self.root / "receipt.json"
        argv = [sys.executable, "-I", "-S", "-B", str(stage / "frontend/build_frontend.py")]
        for name, value in {
            "pins": stage / "pins.json",
            "inputs": stage / "wheels",
            "source-archive": stage / "source.tar",
            "lock": stage / "uv.lock",
            "uv": stage / "uv",
            "receipt": receipt,
            "cache": self.root / "cache",
            "input-manifest": stage / "input-sha256.txt",
            "input-manifest-sha256": hashlib.sha256(
                (stage / "input-sha256.txt").read_bytes()
            ).hexdigest(),
            "root": root,
            "python": sys.executable,
        }.items():
            argv.extend(["--" + name, str(value)])
        result = subprocess.run([*argv, "--host-test"], env=env, capture_output=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(list(home.rglob("*")), [], "--cache failed to contain uv HOME writes")
        self.assertEqual(
            {p.name for p in self.root.iterdir()},
            {"home", "receipt.json"},
            "unexpected retained scratch/cache bytes",
        )


def shutil_remove_owned(root):
    """Remove only this test's exclusively owned host scratch tree."""
    import shutil

    if root.exists():
        for path in root.rglob("*"):
            if path.is_dir() and not path.is_symlink():
                path.chmod(0o755)
        shutil.rmtree(root)
