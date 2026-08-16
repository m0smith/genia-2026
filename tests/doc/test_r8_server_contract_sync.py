from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_r8_server_contract_is_planned_and_not_implemented() -> None:
    state = _read("GENIA_STATE.md")
    rules = _read("GENIA_RULES.md")

    assert "## 9.7) R8 server execution contract (planned, not implemented)" in state
    assert "No behavior in this section is implemented yet." in state
    assert "## 25) R8 server execution invariants (planned, not implemented)" in rules
    assert "`genia serve` remains unavailable" in rules


def test_r8_contract_preserves_activation_and_bind_down_boundaries() -> None:
    state = _read("GENIA_STATE.md")

    required = (
        "`genia serve <file>` is the only server-lifecycle activation boundary",
        "not a generalized lifecycle runner or action registry",
        "passes them to `route_request`",
        "wraps the result once with `cors`",
        "activates the existing `serve_http` boundary",
        "`with_headers`",
        "The lifecycle core returns one deterministic result map",
        "Python remains the only R8 server execution host",
    )
    for fact in required:
        assert fact in state


def test_r8_architecture_docs_defer_to_the_canonical_contract() -> None:
    lifecycle = _read("docs/architecture/lifecycle.md")
    execution_modes = _read("docs/architecture/execution-mode-lifecycle.md")

    for text in (lifecycle, execution_modes):
        assert "`GENIA_STATE.md` section 9.7" in text
        assert "unimplemented" in text

    assert "startup:" in execution_modes
    assert "request:" in execution_modes
    assert "shutdown:" in execution_modes
