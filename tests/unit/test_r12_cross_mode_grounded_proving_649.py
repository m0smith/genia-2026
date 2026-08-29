from pathlib import Path

from genia.interpreter import run_source
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionNone, GeniaOptionSome, GeniaRepresented

from hosts.python.exec_r12_grounded_fixture import _build_env


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/r12_cross_mode_grounded_proving.genia"
SHARED_CASES = (
    ROOT / "spec/eval/r12-grounded-cross-mode.yaml",
    ROOT / "spec/flow/r12-grounded-bounded-flow.yaml",
    ROOT / "spec/error/error-r12-grounded-provider-failure.yaml",
    ROOT / "spec/cli/r12-grounded-proving-case.yaml",
    ROOT / "spec/parse/parse-r12-grounded-existing-forms.yaml",
    ROOT / "spec/ir/r12-grounded-existing-ir.yaml",
)


def test_e12_7_proving_example_and_shared_inventory_exist():
    assert EXAMPLE.is_file()
    assert all(path.is_file() for path in SHARED_CASES)


def test_e12_7_example_keeps_every_provider_stage_explicit():
    source = EXAMPLE.read_text(encoding="utf-8")
    for required in (
        "chunk(",
        "apply_raw(embed_call",
        "apply_raw(index_call",
        "apply_raw(retrieve_call",
        "apply_raw(rerank_call",
        "grounding.assemble_grounded_context",
        "grounding.generate_grounded_answer",
        "validate_record",
        "collect_validated",
    ):
        assert required in source
    for forbidden in (
        "retry(",
        "sleep(",
        "grounded_pipeline(",
        "hidden_embed",
    ):
        assert forbidden not in source


def test_e12_7_shared_cases_use_only_explicit_fixture_authority():
    for path in SHARED_CASES[:4]:
        source = path.read_text(encoding="utf-8")
        assert "fixtures: [r12_grounded]" in source
        assert "_retry" not in source
        assert "sleep(" not in source


def _strings(value, seen=None):
    seen = set() if seen is None else seen
    if isinstance(value, str):
        return [value]
    if id(value) in seen:
        return []
    seen.add(id(value))
    if isinstance(value, GeniaMap):
        return [text for key, item in value.items() for text in _strings(key, seen) + _strings(item, seen)]
    if isinstance(value, (list, tuple, dict)):
        items = value.items() if isinstance(value, dict) else enumerate(value)
        return [text for key, item in items for text in _strings(key, seen) + _strings(item, seen)]
    if isinstance(value, (GeniaOptionSome, GeniaOptionNone, GeniaOptionErr)):
        return _strings(vars(value), seen)
    if isinstance(value, GeniaRepresented):
        return _strings(value.value, seen)
    return [repr(value)]


def test_complete_proving_case_preserves_provenance_and_exact_concern_audits():
    observations = {}
    env = _build_env(observations=observations)
    result = run_source(EXAMPLE.read_text(encoding="utf-8"), env, filename=str(EXAMPLE))

    assert result.get("answer").get("text") == "Ada wrote notes."
    assert result.get("sources")[0].get("doc_id") == "doc-ada"
    assert result.get("evidence")[0].get("chunk").get("meta").facet == "json"
    assert [concern for concern, _event in observations["audits"]] == [
        "embed_call", "index_call", "embed_call", "retrieve_call", "rerank_call", "model_call"
    ]
    assert {name: provider.attempt_count for name, provider in observations["providers"].items()} == {
        "embed_call": 2, "index_call": 1, "retrieve_call": 1, "rerank_call": 1, "model_call": 1
    }


def test_bounded_flow_consumption_makes_no_hidden_provider_attempts():
    observations = {}
    env = _build_env(observations=observations)
    result = run_source(
        'e = embed(embed_provider_fixture, {id: "e", space: "fixture-space-v1", timeout_ms: 1000}, embed_credential_fixture, embed_authority_fixture)\n'
        'evolve("first", (_) -> "later") |> map((text) -> e({kind: quote(query), text: text}) |> "text" |> unwrap_or("")) |> take(1) |> collect',
        env,
    )
    assert result == ["first"]
    assert observations["providers"]["embed_call"].attempt_count == 1
    assert [concern for concern, _event in observations["audits"]] == ["embed_call"]


def test_recursive_sink_scan_finds_no_fixture_credentials_or_payloads():
    observations = {}
    env = _build_env(observations=observations)
    result = run_source(EXAMPLE.read_text(encoding="utf-8"), env, filename=str(EXAMPLE))
    rendered = "\n".join(_strings({"result": result, "observations": observations}))
    for sentinel in (
        "fixture-embed_call", "fixture-index_call", "fixture-retrieve_call",
        "fixture-rerank_call", "fixture-model_call",
    ):
        assert sentinel not in rendered


def test_fixture_runner_has_no_nondeterministic_or_retry_dependency():
    source = (ROOT / "hosts/python/exec_r12_grounded_fixture.py").read_text(encoding="utf-8")
    for forbidden in ("import requests", "import random", "import time", "import os", "sleep(", "retry(", "Thread"):
        assert forbidden not in source
