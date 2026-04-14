from __future__ import annotations

import json
from pathlib import Path

import pytest

from genia import make_global_env, run_source
from genia.interpreter import _main
from genia.utf8 import format_debug


REPO = Path(__file__).resolve().parent.parent
FACTS_PATH = REPO / "docs" / "contract" / "semantic_facts.json"
INSTRUCTION_SURFACES = [
    "AGENTS.md",
    "docs/ai/LLM_CONTRACT.md",
    ".github/copilot-instructions.md",
    ".github/instructions/docs.instructions.md",
    ".github/instructions/stdlib.instructions.md",
    ".github/instructions/tests.instructions.md",
]


def read_text(relpath: str) -> str:
    return (REPO / relpath).read_text(encoding="utf-8")


def normalize(text: str) -> str:
    return " ".join(text.split()).lower()


FACTS = json.loads(FACTS_PATH.read_text(encoding="utf-8"))


def test_semantic_facts_file_stays_small_and_complete() -> None:
    expected_keys = {
        "pipeline_none_short_circuit",
        "pipeline_some_lifts",
        "pipeline_wrap_back",
        "pipeline_option_results_preserved",
        "direct_call_option_behavior",
        "pipe_wrapper",
        "main_dispatch",
        "pipe_bypasses_main",
        "flow_single_use",
        "flow_early_termination",
        "host_status",
        "naming_rule",
        "annotation_builtins",
    }
    assert set(FACTS) == expected_keys
    assert len(FACTS) <= 16, "semantic facts surface should stay intentionally small"


def test_authoritative_docs_capture_pipeline_option_contract() -> None:
    state = read_text("GENIA_STATE.md")
    rules = read_text("GENIA_RULES.md")

    assert "if a stage input is `none(...)`, the remaining stages do not execute" in state
    assert "if a stage input is `some(x)` and the stage is not explicitly Option-aware, the stage receives `x`" in state
    assert "non-Option stage results are wrapped back into `some(...)`" in state
    assert "Option stage results (`some(...)` / `none(...)`) are preserved as-is" in state

    assert "if a stage input is `none(...)`, the remaining stages do not execute" in rules
    assert "if a stage input is `some(x)` and the stage is not explicitly Option-aware, the stage receives `x`" in rules
    assert "when that lifted stage returns a non-Option value `y`, the pipeline wraps it back as `some(y)`" in rules
    assert "when that lifted stage returns `some(...)` or `none(...)`, that Option result is used as-is" in rules
    assert FACTS["direct_call_option_behavior"] in rules


@pytest.mark.parametrize(
    ("relpath", "required"),
    [
        (
                "README.md",
                [
                    FACTS["pipeline_some_lifts"].rstrip("."),
                    "preserve that Option result as-is",
                    "direct calls still receive explicit `some(...)` values unchanged",
                    FACTS["pipe_wrapper"],
                    FACTS["host_status"].replace(" today.", ""),
                    "new `?`-suffixed APIs are boolean-returning",
                    "`get?` remains the current compatibility exception",
                    "Supported built-ins in this phase:",
                ],
            ),
        (
            "GENIA_REPL_README.md",
            [
                FACTS["pipe_wrapper"],
                "new `?`-suffixed APIs are boolean-returning",
                "`get?` remains the current compatibility exception",
            ],
        ),
        (
            "docs/cheatsheet/core.md",
            [
                FACTS["pipeline_some_lifts"].rstrip("."),
                "Option results are preserved as-is",
                FACTS["pipe_wrapper"],
                "`@doc \"...\"`, `@meta {...}`, `@since \"...\"`, `@deprecated \"...\"`, `@category \"...\"`",
            ],
        ),
        (
            "docs/cheatsheet/quick-reference.md",
            [
                FACTS["pipeline_some_lifts"].rstrip("."),
                "direct calls still receive explicit `some(...)` values unchanged",
                FACTS["pipe_wrapper"],
            ],
        ),
        (
            "docs/cheatsheet/unix-power-mode.md",
            [
                FACTS["pipe_wrapper"],
                "row |> nth(5) |> parse_int",
            ],
        ),
        (
            "docs/book/11-flow.md",
            [
                FACTS["pipe_wrapper"],
                "the pipeline lifts it over `some(field)` automatically",
            ],
        ),
    ],
)
def test_public_docs_keep_protected_semantic_facts_in_sync(
    relpath: str, required: list[str]
) -> None:
    text = read_text(relpath)
    for excerpt in required:
        assert normalize(excerpt) in normalize(text), f"{relpath} is missing required excerpt: {excerpt}"


@pytest.mark.parametrize(
    "relpath",
    [
        "README.md",
        "docs/cheatsheet/core.md",
        "docs/cheatsheet/quick-reference.md",
        "docs/cheatsheet/unix-power-mode.md",
        "docs/cheatsheet/piepline-flow-vs-value.md",
    ],
)
def test_public_docs_drop_old_pipeline_wording(relpath: str) -> None:
    text = read_text(relpath)
    assert "pipeline evaluation does not auto-unwrap `some(...)`" not in text
    assert "Pipelines preserve `some(...)`; no implicit unwrapping." not in text


def test_pipeline_flow_vs_value_cheatsheet_uses_current_option_wording() -> None:
    text = read_text("docs/cheatsheet/piepline-flow-vs-value.md")
    normalized = normalize(text)

    assert normalize("ordinary stages lift over `some(x)` automatically") in normalized
    assert normalize("Option results are preserved as-is") in normalized
    assert normalize("direct calls still receive explicit `some(...)` values unchanged") in normalized


@pytest.mark.parametrize("relpath", INSTRUCTION_SURFACES)
def test_instruction_surfaces_reference_canonical_docs_and_avoid_local_semantic_redefinition(
    relpath: str,
) -> None:
    text = read_text(relpath)

    assert "GENIA_STATE.md" in text
    assert "GENIA_RULES.md" in text

    if relpath != "AGENTS.md":
        assert "docs/ai/LLM_CONTRACT.md" in text

    assert "redefine language semantics" in text.lower() or "semantic" in text.lower()

    forbidden = [
        "pipeline evaluation does not auto-unwrap `some(...)`",
        "Pipelines preserve `some(...)`; no implicit unwrapping.",
    ]
    for excerpt in forbidden:
        assert excerpt not in text


def test_instruction_surfaces_reference_semantic_sync_guardrails() -> None:
    for relpath in [
        "AGENTS.md",
        "docs/ai/LLM_CONTRACT.md",
        ".github/copilot-instructions.md",
    ]:
        text = read_text(relpath)
        assert "docs/contract/semantic_facts.json" in text
        assert "tests/test_semantic_doc_sync.py" in text


@pytest.mark.parametrize(
    ("relpath", "expected_excerpt"),
    [
        ("README.md", FACTS["host_status"].replace(" today.", "")),
        ("hosts/README.md", FACTS["host_status"]),
        ("spec/README.md", FACTS["host_status"]),
        ("docs/browser/README.md", FACTS["host_status"]),
        ("apps/playground/README.md", FACTS["host_status"]),
        ("docs/book/15-reference-host-and-portability.md", "one implemented host: Python"),
    ],
)
def test_host_status_docs_stay_clear(relpath: str, expected_excerpt: str) -> None:
    assert normalize(expected_excerpt) in normalize(read_text(relpath))


def test_browser_and_playground_docs_stay_scaffolded() -> None:
    browser = read_text("docs/browser/README.md")
    playground = read_text("apps/playground/README.md")
    spec = read_text("spec/README.md")

    assert "architecture and contract documentation only" in browser
    assert "documentation scaffold only" in playground
    assert "scaffolded/planned" in spec


def test_authoritative_and_public_docs_keep_annotation_contract_visible() -> None:
    for relpath in [
        "GENIA_RULES.md",
        "README.md",
        "docs/book/03-functions.md",
        "docs/cheatsheet/core.md",
    ]:
        text = normalize(read_text(relpath))
        for token in ["`@doc`", "`@meta`", "`@since`", "`@deprecated`", "`@category`"]:
            assert normalize(token) in text


def test_authoritative_and_public_docs_keep_naming_rule_visible() -> None:
    for relpath in [
        "GENIA_STATE.md",
        "GENIA_REPL_README.md",
        "README.md",
        "docs/book/01-core-data.md",
    ]:
        text = normalize(read_text(relpath))
        assert normalize("new `?`-suffixed APIs are boolean-returning") in text
        assert (
            normalize("`get?` remains the current compatibility exception") in text
            or normalize("`get?` remains the existing compatibility exception") in text
        )


def test_authoritative_and_public_docs_keep_cli_dispatch_contract_visible() -> None:
    for relpath in [
        "GENIA_STATE.md",
        "GENIA_REPL_README.md",
        "README.md",
        "docs/cheatsheet/core.md",
        "docs/cheatsheet/quick-reference.md",
        "docs/book/03-functions.md",
    ]:
        text = normalize(read_text(relpath))
        assert "main(argv())" in text
        assert "main/1" in text
        assert "main()" in text
        assert "main/0" in text
        assert "pipe mode" in text
        assert (
            "bypasses `main`" in text
            or "never dispatches `main`" in text
            or "bypasses the `main` convention" in text
        )


def test_runtime_pipeline_lifts_some_and_wraps_back() -> None:
    result = run_source('some("42") |> parse_int', make_global_env([]))
    assert format_debug(result) == "some(42)"


def test_runtime_direct_calls_preserve_explicit_some() -> None:
    result = run_source("echo(x) = x\necho(some(42))", make_global_env([]))
    assert format_debug(result) == "some(42)"


def test_runtime_annotations_match_documented_supported_builtins() -> None:
    src = """
    @doc "Adds one"
    @meta {stable: true}
    @since "0.4"
    @deprecated "Use inc2 instead."
    @category "math"
    inc(x) -> x + 1

    [
      unwrap_or("missing", meta("inc") |> get("doc")),
      unwrap_or(false, meta("inc") |> get("stable")),
      unwrap_or("missing", meta("inc") |> get("since")),
      unwrap_or("missing", meta("inc") |> get("deprecated")),
      unwrap_or("missing", meta("inc") |> get("category"))
    ]
    """
    result = run_source(src, make_global_env([]))
    assert result == ["Adds one", True, "0.4", "Use inc2 instead.", "math"]


class CountingStdin:
    def __init__(self, lines: list[str]):
        self._lines = list(lines)
        self._index = 0
        self.reads = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._lines):
            raise StopIteration
        self.reads += 1
        value = self._lines[self._index]
        self._index += 1
        return value


def test_runtime_cli_contract_matches_documented_main_dispatch(capsys) -> None:
    exit_code = _main(["-c", "main() = 10\nmain(args) = length(args)", "a", "b"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "2"

    exit_code = _main(["-c", "main() = 7"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "7"


def test_runtime_pipe_mode_matches_documented_wrapper(monkeypatch, capsys) -> None:
    stdin = CountingStdin(["a\n", "b\n"])
    monkeypatch.setattr("sys.stdin", stdin)

    exit_code = _main(["-p", "head(1) |> each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "a\n"
    assert stdin.reads == 1
