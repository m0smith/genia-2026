from __future__ import annotations

from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]


def read_text(relpath: str) -> str:
    return (REPO / relpath).read_text(encoding="utf-8")


def normalize(text: str) -> str:
    return " ".join(text.split()).lower()


def assert_contains_all(relpath: str, excerpts: list[str]) -> None:
    text = normalize(read_text(relpath))
    for excerpt in excerpts:
        assert normalize(excerpt) in text, f"{relpath} missing Seq contract excerpt: {excerpt}"


def test_state_defines_seq_as_semantic_contract_not_runtime_surface() -> None:
    assert_contains_all(
        "GENIA_STATE.md",
        [
            "`Seq` is a semantic compatibility category for ordered value production.",
            "Seq is not a runtime value, type constructor, syntax form, helper, or Core IR node.",
            "In this phase, the implemented Seq-compatible public values are lists and Flow.",
            "Lists are eager and reusable.",
            "Flow is lazy, pull-based, source-bound, and single-use.",
            "Iterators and generators are host implementation details, not portable Genia values.",
        ],
    )


def test_rules_lock_seq_pipeline_and_bridge_invariants() -> None:
    assert_contains_all(
        "GENIA_RULES.md",
        [
            "Seq compatibility does not change pipeline call shape.",
            "Seq compatibility does not change Option-aware pipeline behavior.",
            "No implicit list-to-Flow conversion is introduced.",
            "No implicit Flow-to-list conversion is introduced.",
            "Matching a Flow as a list requires explicit materialization first.",
        ],
    )


@pytest.mark.parametrize(
    "relpath",
    [
        "README.md",
        "GENIA_REPL_README.md",
        "docs/host-interop/HOST_INTEROP.md",
        "docs/cheatsheet/piepline-flow-vs-value.md",
    ],
)
def test_public_docs_describe_seq_list_flow_iterator_split(relpath: str) -> None:
    assert_contains_all(
        relpath,
        [
            "Seq is the semantic abstraction for ordered value production.",
            "List is the eager reusable Seq-compatible value.",
            "Flow is the lazy single-use Seq-compatible value.",
            "Iterator is a host implementation detail.",
        ],
    )


def test_flow_spec_readme_records_seq_coverage_boundary() -> None:
    assert_contains_all(
        "spec/flow/README.md",
        [
            "Flow shared specs cover the Flow side of the Seq contract only.",
            "They do not define a public Seq runtime value, Seq syntax, or host iterator semantics.",
            "List-side Seq behavior is covered through eval/list specs where applicable.",
        ],
    )
