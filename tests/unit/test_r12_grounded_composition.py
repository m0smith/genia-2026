from pathlib import Path

import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


PROBE = str((Path("examples") / "issue_648_probe.genia").resolve())


def run_grounding(source: str):
    env = make_global_env([])
    return run_source(
        "import r12_grounded_context_answer as grounding\n" + source,
        env,
        filename=PROBE,
    )


def evidence_source(
    *, doc_id: str = "doc-1", offset: int = 0, length: int = 4, score: str = "0.9"
) -> str:
    return (
        "{chunk: {text: \"Ada!\", "
        f"source: {{doc_id: \"{doc_id}\", offset: {offset}, length: {length}}}, "
        'meta: json_decode("{}") |> unwrap_or({})}, '
        f"score: {score}}}"
    )


def test_context_assembly_is_exact_and_accepts_empty_evidence():
    result = run_grounding(
        'grounding.assemble_grounded_context("What?", '
        '{kind: quote(text), text: "No evidence"}, [])'
    )
    assert format_debug(result) == (
        '{question: "What?", content: {kind: text, text: "No evidence"}, evidence: []}'
    )


def test_context_preserves_exact_evidence_order_and_values():
    first = evidence_source(doc_id="doc-a", offset=0)
    second = evidence_source(doc_id="doc-b", offset=5)
    result = run_grounding(
        f"evidence = [{first}, {second}]\n"
        'context = grounding.assemble_grounded_context("Who?", '
        '{kind: quote(text), text: "Use evidence"}, evidence)\n'
        "[context.evidence == evidence, context.evidence]"
    )
    assert result[0] is True
    assert [item.get("chunk").get("source").get("doc_id") for item in result[1]] == [
        "doc-a",
        "doc-b",
    ]


def test_answer_uses_success_content_exact_evidence_and_first_exact_sources():
    repeated = evidence_source(doc_id="doc-a", offset=0, score="0.9")
    same_source_new_score = evidence_source(doc_id="doc-a", offset=0, score="0.2")
    distinct_span = evidence_source(doc_id="doc-a", offset=5, score="0.1")
    result = run_grounding(
        f"evidence = [{repeated}, {same_source_new_score}, {distinct_span}]\n"
        'context = grounding.assemble_grounded_context("Who?", '
        '{kind: quote(text), text: "Use evidence"}, evidence)\n'
        'response = some({message: {role: quote(assistant), content: '
        '{kind: quote(text), text: "Ada"}}, finish_reason: quote(stop), '
        'usage: none("model-usage-unavailable")})\n'
        "answer = grounding.assemble_grounded_answer(context, response)\n"
        "[answer.evidence == evidence, answer.answer, answer.sources]"
    )
    assert result[0] is True
    assert format_debug(result[1]) == '{kind: text, text: "Ada"}'
    assert format_debug(result[2]) == (
        '[{doc_id: "doc-a", offset: 0, length: 4}, '
        '{doc_id: "doc-a", offset: 5, length: 4}]'
    )


@pytest.mark.parametrize(
    "outcome,expected",
    [
        ('none("retrieval-no-results")', 'none("retrieval-no-results")'),
        (
            'err("model-timeout", {timeout_ms: 1000})',
            'err("model-timeout", {timeout_ms: 1000})',
        ),
    ],
)
def test_answer_propagates_non_success_outcome_without_assembly(
    outcome: str, expected: str
):
    result = run_grounding(
        'context = grounding.assemble_grounded_context("Who?", '
        '{kind: quote(text), text: "Use evidence"}, [])\n'
        f"grounding.assemble_grounded_answer(context, {outcome})"
    )
    assert format_debug(result) == expected


@pytest.mark.parametrize(
    "expression,match",
    [
        (
            'grounding.assemble_grounded_context("", {kind: quote(text), text: "x"}, [])',
            "non-empty question",
        ),
        (
            'grounding.assemble_grounded_context("q", {kind: quote(text), text: "x", extra: 1}, [])',
            "closed content",
        ),
            (
                'grounding.assemble_grounded_context("q", {kind: quote(text), text: "x"}, '
            f'[{evidence_source(score="\"bad\"")}])',
                "finite score",
            ),
    ],
)
def test_local_shape_validation_rejects_invalid_grounding(expression: str, match: str):
    with pytest.raises((TypeError, ValueError), match=match):
        run_grounding(expression)


def test_generate_invokes_supplied_model_once_and_uses_success_only():
    result = run_grounding(
        'calls = ref(0)\n'
        'fake_model(request) = {\n'
        '  _ = ref_update(calls, (n) -> n + 1)\n'
        '  some({message: {role: quote(assistant), content: '
        '{kind: quote(text), text: "grounded"}}, finish_reason: quote(stop), '
        'usage: none("model-usage-unavailable")})\n'
        '}\n'
        'context = grounding.assemble_grounded_context("Who?", '
        '{kind: quote(text), text: "Use evidence"}, [])\n'
        'answer = grounding.generate_grounded_answer(fake_model, context)\n'
        '[ref_get(calls), answer.answer |> "text", answer.evidence]'
    )
    assert result == [1, "grounded", []]
