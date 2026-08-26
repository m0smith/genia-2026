from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "docs/releases/R11.md"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _run_fixture(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "hosts.python.exec_model_fixture", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_r11_status_is_synchronized_after_e11_7() -> None:
    required = {
        "GENIA_STATE.md": "E11-1 through E11-7",
        "README.md": "E11-1 through E11-7",
        "GENIA_REPL_README.md": "E11-1 through E11-7",
        "GENIA_RULES.md": "E11-1 through E11-7",
        "docs/ai/LLM_CONTRACT.md": "E11-1 through E11-7",
        "docs/design/README.md": "E11-1 through E11-7",
        "docs/design/r11-ai-composition-contract.md": "E11-1 through E11-7",
        "docs/releases/R11.md": "E11-1 through E11-7 delivered",
        "docs/releases/README.md": "E11-1 through E11-7 delivered",
        "docs/strategy/release-roadmap.md": "E11-1 through E11-7 implemented",
    }
    for path, expected in required.items():
        assert expected in _read(path), f"{path} must record completed E11-7 truth sync"

    release = RELEASE.read_text(encoding="utf-8")
    assert "E11-8 remains planned" in release
    assert "E11-7 through E11-8 remain planned" not in release


def test_r11_public_truth_keeps_maturity_portability_and_exclusions_explicit() -> None:
    release = RELEASE.read_text(encoding="utf-8")
    normalized = release.lower()
    for required in (
        "experimental",
        "portable semantics",
        "python-host-only",
        "messages are ordinary values",
        "prompts are functions",
        "models are callable",
        "chains are pipelines",
        "conversations are application composition over `scan`",
        "tools",
        "agents",
        "streaming",
        "retries",
        "provider registry",
        "rag",
    ):
        assert required in normalized, f"R11 release truth is missing {required!r}"


def test_r11_text_and_structured_release_examples_execute_exactly() -> None:
    text_source = (
        'm = model(model_provider_fixture, {id: "fixture-text", timeout_ms: 1000}, '
        "model_credential_fixture, model_authority_fixture)\n"
        'm({messages: [{role: quote(user), content: {kind: quote(text), text: "hello"}}], '
        "output: {kind: quote(text)}})"
    )
    result = _run_fixture(text_source)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == (
        "some({message: {role: assistant, content: {kind: text, text: \"fixture reply\"}}, "
        "finish_reason: stop, usage: some({input_tokens: 2, output_tokens: 3, total_tokens: 5})})\n"
    )

    structured_source = (
        'schema = json_decode("{\\\"type\\\":\\\"integer\\\"}") |> unwrap_or({})\n'
        'Integer = json_schema(schema) |> unwrap_or((_) -> none("compile-failed"))\n'
        'm = model(model_provider_fixture, {id: "fixture-json", timeout_ms: 1000}, '
        "model_credential_fixture, model_authority_fixture)\n"
        'response = m({messages: [{role: quote(user), content: {kind: quote(text), text: "Return 7"}}], '
        "output: {kind: quote(json), schema: schema, template: Integer}}) |> unwrap_or({})\n"
        'response("message")("content")("value") |> representation_match("json") |> unwrap_or(-1)'
    )
    result = _run_fixture(structured_source)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == "7\n"


def test_r11_flow_and_validated_pipeline_examples_execute_exactly() -> None:
    flow = _run_fixture("--file", "examples/r11_flow_conversation.genia")
    assert flow.returncode == 0, flow.stderr
    assert flow.stderr == ""
    assert flow.stdout == "<function conversation_step/4>\n"

    pipeline = _run_fixture(
        "--file", "examples/r11_validated_pipeline_proving_case.genia"
    )
    assert pipeline.returncode == 0, pipeline.stderr
    assert pipeline.stderr == ""
    assert pipeline.stdout == (
        "{clean: [<represented>, <represented>], diagnostics: "
        '[{index: 1, kind: skipped, reason: "blank_line", context: some({kind: jsonl_record, '
        'status: skipped, reason: blank_line, line: ""})}, {index: 2, kind: error, '
        "reason: invalid_jsonl_record, context: some({kind: jsonl_record, status: error, "
        'reason: invalid_jsonl_record, line: "not-json", message: "Expecting value", column: 1})}, '
        '{index: 3, kind: error, reason: record_validation_failed, context: some({diagnostics: '
        '[{field: "name", status: error, reason: "missing required field", context: '
        '{field: "name", reason: "missing required field"}}]})}]}\n'
    )
