from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


ISSUE_405_EVAL_SPECS = [
    "validation-record-diagnostic-context-layers.yaml",
    "validation-record-diagnostic-without-context.yaml",
]


def _assert_spec_passes(path: str) -> None:
    spec = load_spec(Path(path))
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)
    assert failures == []


def test_issue_405_shared_spec_inventory_is_present() -> None:
    specs, invalid_specs = discover_specs()
    names = {spec.path.name for spec in specs}

    assert invalid_specs == []
    for fname in ISSUE_405_EVAL_SPECS:
        assert fname in names


@pytest.mark.parametrize("fname", ISSUE_405_EVAL_SPECS)
def test_issue_405_validation_diagnostic_context_specs_execute_as_contract(fname: str) -> None:
    _assert_spec_passes(f"spec/eval/{fname}")
