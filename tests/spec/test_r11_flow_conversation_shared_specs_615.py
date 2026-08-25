from pathlib import Path

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import load_spec


ROOT = Path(__file__).resolve().parents[2]
CASES = (
    ROOT / "spec/eval/r11-flow-conversation-list.yaml",
    ROOT / "spec/flow/r11-flow-conversation-flow.yaml",
    ROOT / "spec/error/r11-flow-conversation-model-failure.yaml",
)


def test_issue_615_shared_spec_inventory_is_present():
    assert all(path.is_file() for path in CASES)


def test_issue_615_shared_specs_execute_as_contract():
    failures = []
    for path in CASES:
        spec = load_spec(path)
        result = compare_spec(spec, execute_spec(spec))
        if result:
            failures.append(f"{path.name}: {result}")
    assert not failures, "\n".join(failures)
