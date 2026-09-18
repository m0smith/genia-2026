"""Tests proving parse specs are integrated into the main shared spec runner.

These tests assert behavior introduced in issue-147:
  - parse is in SPEC_CATEGORIES
  - load_spec accepts category: parse with expected.parse
  - discover_specs includes parse specs from spec/parse/
  - execute_spec handles category: parse via parse_and_normalize
  - compare_spec handles category: parse results
  - the main runner total includes parse spec cases
"""
from __future__ import annotations

from pathlib import Path

import pytest

import tools.spec_runner.runner as runner_module
from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import ActualResult, execute_spec
from tools.spec_runner.loader import LoadedSpec, discover_specs, load_spec

pytestmark = [pytest.mark.spec, pytest.mark.slow]


REPO = Path(__file__).resolve().parents[2]
PARSE_DIR = REPO / "spec" / "parse"



def _parse_spec(
    *,
    name: str,
    source: str,
    expected_parse: object,
    path: Path | None = None,
) -> LoadedSpec:
    return LoadedSpec(
        name=name,
        category="parse",
        source=source,
        stdin="",
        expected_stdout=None,
        expected_stderr=None,
        expected_exit_code=None,
        expected_ir=None,
        expected_parse=expected_parse,
        path=path or (PARSE_DIR / f"{name}.yaml"),
    )


# ---------------------------------------------------------------------------
# Loader tests
# ---------------------------------------------------------------------------

def test_loader_accepts_parse_category_ok_spec() -> None:
    """load_spec must accept a parse spec with kind: ok without raising."""
    spec = load_spec(PARSE_DIR / "parse-literal-number.yaml")
    assert spec.category == "parse"
    assert spec.source == "42"
    assert spec.expected_parse == {"kind": "ok", "ast": {"kind": "Literal", "value": 42}}


def test_loader_accepts_parse_category_error_spec() -> None:
    """load_spec must accept a parse spec with kind: error without raising."""
    spec = load_spec(PARSE_DIR / "parse-error-unclosed-paren.yaml")
    assert spec.category == "parse"
    assert spec.source == "(1 + 2"
    assert spec.expected_parse["kind"] == "error"
    assert spec.expected_parse["type"] == "SyntaxError"
    assert "Expected RPAREN" in spec.expected_parse["message"]


def test_loader_rejects_parse_spec_with_missing_parse_field(tmp_path: Path) -> None:
    """load_spec must reject a parse spec missing expected.parse."""
    p = tmp_path / "bad-parse.yaml"
    p.write_text(
        "name: bad-parse\ncategory: parse\ninput:\n  source: \"42\"\nexpected: {}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing required field: expected.parse"):
        load_spec(p)


def test_loader_rejects_parse_spec_with_invalid_kind(tmp_path: Path) -> None:
    """load_spec must reject expected.parse.kind values other than ok or error."""
    p = tmp_path / "bad-kind.yaml"
    p.write_text(
        "name: bad-kind\ncategory: parse\ninput:\n  source: \"42\"\nexpected:\n  parse:\n    kind: unknown\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="kind must be 'ok' or 'error'"):
        load_spec(p)


# ---------------------------------------------------------------------------
# Discovery tests
# ---------------------------------------------------------------------------

def test_discover_specs_includes_parse_specs() -> None:
    """discover_specs must include parse specs from spec/parse/ in the specs list."""
    specs, invalid_specs = discover_specs()
    parse_specs = [s for s in specs if s.category == "parse"]
    assert len(parse_specs) >= 1, (
        f"Expected at least one parse spec; found 0. "
        f"invalid_specs={[str(i.path) + ': ' + i.message for i in invalid_specs]}"
    )


def test_discover_specs_parse_names_present() -> None:
    """discover_specs must include the expected parse spec names."""
    specs, _ = discover_specs()
    parse_names = {s.name for s in specs if s.category == "parse"}
    expected = {"parse-literal-number", "parse-assignment-simple", "parse-error-unclosed-paren"}
    assert expected.issubset(parse_names), f"Missing parse specs: {expected - parse_names}"


def test_discover_specs_has_no_invalid_specs_after_parse_integration() -> None:
    """After integration, discover_specs must not put parse specs in invalid_specs."""
    _, invalid_specs = discover_specs()
    parse_invalids = [i for i in invalid_specs if "parse" in str(i.path)]
    assert parse_invalids == [], f"Parse specs reported as invalid: {parse_invalids}"


# ---------------------------------------------------------------------------
# Executor tests
# ---------------------------------------------------------------------------

def test_execute_spec_parse_ok() -> None:
    """execute_spec must handle category=parse and return a parse result."""
    spec = _parse_spec(
        name="parse-literal-number",
        source="42",
        expected_parse={"kind": "ok", "ast": {"kind": "Literal", "value": 42}},
    )
    actual = execute_spec(spec)
    assert actual.parse is not None
    assert actual.parse["kind"] == "ok"
    assert actual.parse["ast"] == {"kind": "Literal", "value": 42}


def test_execute_spec_parse_error() -> None:
    """execute_spec must handle a parse failure spec and return kind: error."""
    spec = _parse_spec(
        name="parse-error-unclosed-paren",
        source="(1 + 2",
        expected_parse={"kind": "error", "type": "SyntaxError", "message": "Expected RPAREN"},
    )
    actual = execute_spec(spec)
    assert actual.parse is not None
    assert actual.parse["kind"] == "error"
    assert actual.parse["type"] == "SyntaxError"
    assert "Expected RPAREN" in actual.parse["message"]


# ---------------------------------------------------------------------------
# Comparator tests
# ---------------------------------------------------------------------------

def test_compare_spec_parse_ok_match() -> None:
    """compare_spec must return no failures when the parse result matches exactly."""
    spec = _parse_spec(
        name="parse-literal-number",
        source="42",
        expected_parse={"kind": "ok", "ast": {"kind": "Literal", "value": 42}},
    )
    actual = ActualResult(parse={"kind": "ok", "ast": {"kind": "Literal", "value": 42}})
    failures = compare_spec(spec, actual)
    assert failures == []


def test_compare_spec_parse_ok_ast_mismatch() -> None:
    """compare_spec must report a parse.ast failure on mismatch."""
    spec = _parse_spec(
        name="parse-literal-number",
        source="42",
        expected_parse={"kind": "ok", "ast": {"kind": "Literal", "value": 42}},
    )
    actual = ActualResult(parse={"kind": "ok", "ast": {"kind": "Literal", "value": 99}})
    failures = compare_spec(spec, actual)
    assert len(failures) == 1
    assert failures[0].field == "parse.ast"


def test_compare_spec_parse_ok_kind_mismatch() -> None:
    """compare_spec must report a parse.kind failure when ok was expected but error occurred."""
    spec = _parse_spec(
        name="parse-literal-number",
        source="42",
        expected_parse={"kind": "ok", "ast": {"kind": "Literal", "value": 42}},
    )
    actual = ActualResult(parse={"kind": "error", "type": "SyntaxError", "message": "oops"})
    failures = compare_spec(spec, actual)
    assert any(f.field == "parse.kind" for f in failures)


def test_compare_spec_parse_error_match() -> None:
    """compare_spec must return no failures when error parse result matches."""
    spec = _parse_spec(
        name="parse-error-unclosed-paren",
        source="(1 + 2",
        expected_parse={"kind": "error", "type": "SyntaxError", "message": "Expected RPAREN"},
    )
    actual = ActualResult(parse={"kind": "error", "type": "SyntaxError", "message": "Expected RPAREN at line 1"})
    failures = compare_spec(spec, actual)
    assert failures == []


def test_compare_spec_parse_error_message_mismatch() -> None:
    """compare_spec must report parse.message failure when message substring is absent."""
    spec = _parse_spec(
        name="parse-error-unclosed-paren",
        source="(1 + 2",
        expected_parse={"kind": "error", "type": "SyntaxError", "message": "Expected RPAREN"},
    )
    actual = ActualResult(parse={"kind": "error", "type": "SyntaxError", "message": "something else"})
    failures = compare_spec(spec, actual)
    assert any(f.field == "parse.message" for f in failures)


# ---------------------------------------------------------------------------
# End-to-end runner test
# ---------------------------------------------------------------------------

def test_runner_includes_parse_specs_in_total(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The runner counts a discovered parse spec without running the full suite."""
    parse_spec = _parse_spec(
        name="bounded-parse-integration",
        source="42",
        expected_parse={"kind": "ok", "ast": {"kind": "Literal", "value": 42}},
    )
    executed: list[str] = []

    monkeypatch.setattr(runner_module, "discover_specs", lambda: ([parse_spec], []))

    def execute_bounded_spec(spec: LoadedSpec) -> ActualResult:
        executed.append(spec.name)
        return ActualResult(parse=spec.expected_parse)

    monkeypatch.setattr(runner_module, "execute_spec", execute_bounded_spec)

    exit_code = runner_module.main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert executed == ["bounded-parse-integration"]
    assert "Summary: total=1 passed=1 failed=0 invalid=0" in captured.out
