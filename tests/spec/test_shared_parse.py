from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs


def test_issue_838_exact_numeric_parse_shared_cases() -> None:
    specs, invalid = discover_specs()
    assert invalid == []
    selected = [
        spec
        for spec in specs
        if spec.category == "parse" and spec.name.startswith("exact-numeric-")
    ]
    assert len(selected) == 8
    for spec in selected:
        assert compare_spec(spec, execute_spec(spec)) == []
