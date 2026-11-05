"""Run isolated validator-removal mutants against the strengthened #1285 tests.

Each child process bypasses exactly one require diagnostic in memory. Production
sources remain unchanged. A mutant is killed only by an assertion failure (not
an import/runtime error); baseline must pass first. No network/images involved.
"""

import importlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

CASES = {
    "unsafe member type/mode": "test_record_listed_member_validations",
    "untyped executable member": "test_record_listed_member_validations",
    "bytecode payload forbidden": "test_record_listed_member_validations",
    "unexpected generated metadata/signature": "test_record_listed_member_validations",
    "dist-info prefix alias": "test_record_listed_member_validations",
    "unexpected .data directory": "test_record_listed_member_validations",
    "unsupported WHEEL format": "test_wheel_and_metadata_headers",
    "METADATA identity mismatch": "test_wheel_and_metadata_headers",
    "unsafe entrypoint name": "test_entrypoint_diagnostics",
    "unsupported entrypoint target": "test_entrypoint_diagnostics",
    "malformed entrypoint identifier": "test_entrypoint_diagnostics",
    "duplicate distribution": "test_duplicate_distribution",
    "archive size mismatch/limit": "test_archive_limits",
    "expanded archive limit": "test_archive_limits",
    "batch archive limit": "test_archive_limits",
    "WHEEL/filename tag mismatch": "test_tag_checks_independent",
    "incompatible target tag": "test_tag_checks_independent",
}


def child(diagnostic):
    """Execute only the associated test, retaining assertion/error discrimination."""
    tests = importlib.import_module("test_revision")
    api = importlib.import_module("offline_install")
    original = api.require

    def require(condition, message):
        """Remove one validation while preserving every other check verbatim."""
        if message != diagnostic:
            original(condition, message)

    stream = io.StringIO()
    with patch.object(api, "require", require):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
            unittest.TestSuite([tests.RevisionContract(CASES[diagnostic])])
        )
    print(
        json.dumps(
            {
                "diagnostic": diagnostic,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "output": stream.getvalue(),
            }
        )
    )


def main():
    """Check passing baselines, then require every isolated mutant to be killed."""
    if len(sys.argv) > 1:
        child(sys.argv[1])
        return
    tests = importlib.import_module("test_revision")
    baseline = unittest.TextTestRunner(verbosity=2).run(
        unittest.TestSuite(tests.RevisionContract(name) for name in sorted(set(CASES.values())))
    )
    if not baseline.wasSuccessful():
        raise SystemExit("mutation baseline failed")
    rows = []
    for diagnostic in CASES:
        result = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve()), diagnostic],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode:
            raise RuntimeError(result.stderr)
        row = json.loads(result.stdout)
        rows.append(row)
    print(json.dumps(rows, indent=2))
    if any(r["failures"] == 0 or r["errors"] != 0 for r in rows):
        raise SystemExit("surviving mutant or invalid mutation; inspect retained output")


if __name__ == "__main__":
    main()
