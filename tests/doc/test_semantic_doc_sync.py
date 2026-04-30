from __future__ import annotations

import json
from pathlib import Path

import pytest

from genia import make_global_env, run_source
from genia.interpreter import _main
from genia.utf8 import format_debug


REPO = Path(__file__).resolve().parent.parent.parent
ROOT = Path(__file__).resolve().parents[2]
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
                    "automatic lifting is pipeline-only",
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
            "docs/cheatsheet/piepline-flow-vs-value.md",
            [
                FACTS["pipe_wrapper"],
                "auto-lift ordinary stages over `some(x)`",
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


# @pytest.mark.parametrize(
#     "relpath",
#     [
#         "README.md",
#         "docs/cheatsheet/core.md",
#         "docs/cheatsheet/quick-reference.md",
#         "docs/cheatsheet/unix-power-mode.md",
#         "docs/cheatsheet/piepline-flow-vs-value.md",
#         "docs/architecture/pipeline-ir-host-integration.md",
#     ],
# )

def test_pipeline_semantics_design_note_exists():
    path = ROOT / "docs/design/pipeline-semantics.md"
    assert path.exists()
    text = path.read_text()
    assert "Core IR" in text
    assert "portability boundary" in text
    assert "GENIA_STATE.md" in text


def test_architecture_folder_keeps_core_ir_portability_only_for_pipeline_cleanup():
    architecture = ROOT / "docs/architecture"

    assert (architecture / "core-ir-portability.md").exists()
    assert not (architecture / "spec-system.md").exists()
    assert not (architecture / "pipeline-ir-host-integration.md").exists()
    assert not (architecture / "pipeline-option-redesign.md").exists()
    assert not (architecture / "spec-phase-1-design.md").exists()


def test_completed_issue_phase_artifacts_removed_from_architecture_docs():
    architecture = ROOT / "docs/architecture"
    issue_docs = list(architecture.glob("issue-*.md"))
    assert issue_docs == []

def test_readme_consistency_note_section_includes_option_preservation() -> None:
    """The README 'Current consistency note' section must mention that Option
    stage results are preserved as-is whenever it describes non-Option wrapping.
    This catches the exact contradiction where the section describes wrapping
    but omits preservation, implying double-wrapping."""
    text = read_text("README.md")
    marker = "Current consistency note:"
    idx = text.find(marker)
    assert idx != -1, "README.md must contain a 'Current consistency note:' section"
    section = text[idx:]
    # section ends at the next ## heading
    next_heading = section.find("\n## ")
    if next_heading > 0:
        section = section[:next_heading]
    norm = normalize(section)
    assert "non-option" in norm and "wrapped back" in norm, (
        "README.md consistency-note section should describe non-Option wrapping"
    )
    assert "option" in norm and "preserved as-is" in norm, (
        "README.md consistency-note section mentions non-Option wrapping "
        "but does not mention that Option stage results are preserved as-is"
    )


def test_pipeline_flow_vs_value_cheatsheet_uses_current_option_wording() -> None:
    text = read_text("docs/cheatsheet/piepline-flow-vs-value.md")
    normalized = normalize(text)

    assert normalize("auto-lift ordinary stages over `some(x)`") in normalized
    assert normalize("Pipeline `some`/`none` lifting works the same in both worlds") in normalized
    assert normalize("Direct `f(some(x))` short-circuits") in normalized


@pytest.mark.parametrize(
    "relpath",
    [
        "README.md",
        "docs/cheatsheet/quick-reference.md",
        "docs/cheatsheet/core.md",
        "docs/cheatsheet/piepline-flow-vs-value.md",
    ],
)
def test_docs_that_mention_non_option_wrapping_also_mention_option_preservation(
    relpath: str,
) -> None:
    """If a doc mentions that lifted non-Option results are wrapped back into
    some(...), it must also mention that Option stage results are preserved
    as-is.  This catches the exact contradiction where a section describes
    wrapping but omits preservation, implying double-wrapping."""
    text = normalize(read_text(relpath))
    wrapping_phrase = normalize("non-Option")
    preservation_phrases = [
        normalize("Option results are preserved as-is"),
        normalize("Option result is preserved as-is"),
        normalize("preserve that Option result as-is"),
        normalize("Option stage results"),
        normalize("Final result preserves Option structure"),
    ]
    if wrapping_phrase in text:
        assert any(p in text for p in preservation_phrases), (
            f"{relpath} mentions non-Option wrapping but does not mention "
            f"that Option stage results are preserved as-is"
        )


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
        ("docs/host-interop/HOST_INTEROP.md", "Python is the only implemented host and is the reference host today."),
    ],
)
def test_host_status_docs_stay_clear(relpath: str, expected_excerpt: str) -> None:
    assert normalize(expected_excerpt) in normalize(read_text(relpath))


def test_browser_and_playground_docs_stay_scaffolded() -> None:
    browser = read_text("docs/browser/README.md")
    playground = read_text("apps/playground/README.md")
    spec = read_text("spec/README.md")

    assert "architecture and contract documentation only" in browser, (
        "Browser documentation must state its scaffolded status."
    )
    assert "documentation scaffold only" in playground, (
        "Playground documentation must state its scaffolded status."
    )
    assert (
        "shared cross-host spec suite" in spec
        or "Python is the only implemented host today." in spec
        or "The Python host adapter implements the shared host contract" in spec
    ), "Specification documentation must state its scaffolded/planned or current status."


def test_authoritative_and_public_docs_keep_annotation_contract_visible() -> None:
    for relpath in [
        "GENIA_RULES.md",
        "README.md",
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


def test_genia_state_limitations_includes_parse_directory() -> None:
    state = read_text("GENIA_STATE.md")
    assert "spec/parse/" in state, (
        "GENIA_STATE.md Limitations section must list spec/parse/ alongside the other five directories"
    )


def test_genia_state_does_not_claim_parse_not_yet_executed() -> None:
    state = read_text("GENIA_STATE.md")
    assert "does not yet execute parse categories as shared spec files" not in state, (
        "GENIA_STATE.md must not claim the runner does not yet execute parse — parse is active"
    )


def test_host_interop_does_not_claim_no_parse_coverage() -> None:
    text = read_text("docs/host-interop/HOST_INTEROP.md")
    assert "does not yet provide implemented shared case coverage for parse" not in text, (
        "HOST_INTEROP.md must not claim no parse coverage — parse is active"
    )


@pytest.mark.parametrize("relpath", [
    "docs/cheatsheet/quick-reference.md",
    "docs/cheatsheet/unix-power-mode.md",
])
def test_cheatsheets_do_not_claim_only_eval_is_active(relpath: str) -> None:
    text = read_text(relpath)
    assert "only the eval category is active for executable shared spec files" not in text, (
        f"{relpath} must not claim only eval is active — six categories are now active"
    )
    assert "other categories are scaffold-only" not in text, (
        f"{relpath} must not claim other categories are scaffold-only — five others are active"
    )





# --- Issue #119: Core IR lowering invariant doc-sync tests ---
# These tests enforce that the architectural docs actually document the lowering
# invariants that the Python reference host already implements.  They FAIL until
# the docs phase updates docs/architecture/core-ir-portability.md and GENIA_RULES.md.


def test_arch_doc_lowering_invariants_cover_slash_as_ir_binary() -> None:
    arch = read_text("docs/architecture/core-ir-portability.md")
    assert "SLASH" in arch, (
        "docs/architecture/core-ir-portability.md must document that "
        "named slash access (lhs/name) lowers as IrBinary(op=SLASH)"
    )


def test_arch_doc_lowering_invariants_cover_bare_none_null_reason() -> None:
    arch = read_text("docs/architecture/core-ir-portability.md")
    has_reason_null = "reason=null" in arch or "reason: null" in arch
    has_bare_none_null = "bare" in arch.lower() and "none" in arch and "null" in arch
    assert has_reason_null or has_bare_none_null, (
        "docs/architecture/core-ir-portability.md must document that "
        "bare `none` lowers to IrOptionNone with reason=null and context=null"
    )


def test_arch_doc_lowering_invariants_cover_ir_assign_placement() -> None:
    arch = read_text("docs/architecture/core-ir-portability.md")
    not_wrapped = "not wrapped" in arch.lower()
    directly_in_block = "directly in" in arch.lower() and "block" in arch.lower()
    assert not_wrapped or directly_in_block, (
        "docs/architecture/core-ir-portability.md must document the IrAssign placement "
        "rule: IrAssign appears directly in IrBlock.exprs, NOT wrapped in IrExprStmt"
    )


# --- Issue #118: Host capability registry contract doc-sync tests ---
# These tests enforce that capabilities.md exists, is complete, and is
# internally consistent per the 12 invariants in the spec.
# They FAIL until the implementation phase creates capabilities.md
# and updates the three related files.

_CAPABILITIES_DOC = "docs/host-interop/capabilities.md"

# Invariant 1: all 29 required capability names must appear in the document.
_REQUIRED_CAPABILITY_NAMES = [
    "io.stdout",
    "io.stderr",
    "io.stdin",
    "time.sleep",
    "random.rng",
    "random.rand",
    "random.rand-int",
    "random.rand-seeded",
    "random.rand-int-seeded",
    "http.serve",
    "process.spawn",
    "process.send",
    "process.alive",
    "process.failed",
    "process.error",
    "ref.create",
    "ref.get",
    "ref.set",
    "ref.update",
    "cell.create",
    "cell.send",
    "cell.get",
    "cell.restart",
    "bytes.utf8-encode",
    "bytes.utf8-decode",
    "json.parse",
    "json.stringify",
    "zip.entries",
    "zip.write",
]

_ALLOWED_PORTABILITY_TERMS = frozenset(
    ["language contract", "Python-host-only", "not implemented"]
)

_PROHIBITED_PHRASES = [
    "will be implemented",
    "coming soon",
    "Node.js: Implemented",
    "Java: Implemented",
    "Rust: Implemented",
    "Go: Implemented",
    "C++: Implemented",
]

_PROHIBITED_INTERNAL_NAMES = [
    "src/genia/interpreter.py",
    "class Ir",
    "class Ast",
    "src/genia/evaluator",
]


def test_capability_registry_all_required_names_present() -> None:
    """Invariant 1: every required capability name appears in capabilities.md."""
    text = read_text(_CAPABILITIES_DOC)
    for name in _REQUIRED_CAPABILITY_NAMES:
        assert f"`{name}`" in text, (
            f"capabilities.md is missing required capability entry: `{name}`"
        )


def test_capability_registry_required_fields_present() -> None:
    """Invariant 2: required fields (name, genia_surface, input, output, errors,
    portability) appear at least once per capability (29 entries minimum)."""
    text = read_text(_CAPABILITIES_DOC)
    required_field_markers = [
        "**name:**",
        "**genia_surface:**",
        "**input:**",
        "**output:**",
        "**errors:**",
        "**portability:**",
    ]
    for marker in required_field_markers:
        count = text.count(marker)
        assert count >= len(_REQUIRED_CAPABILITY_NAMES), (
            f"capabilities.md has {count} occurrences of '{marker}' "
            f"but needs at least {len(_REQUIRED_CAPABILITY_NAMES)} (one per capability)"
        )


def test_capability_registry_portability_values_are_canonical() -> None:
    """Invariant 3: every portability field uses exactly one of the three
    allowed status terms; no other portability value may appear."""
    text = read_text(_CAPABILITIES_DOC)
    portability_lines = [
        line for line in text.splitlines() if "**portability:**" in line
    ]
    assert len(portability_lines) >= len(_REQUIRED_CAPABILITY_NAMES), (
        f"capabilities.md has {len(portability_lines)} portability lines "
        f"but needs at least {len(_REQUIRED_CAPABILITY_NAMES)}"
    )
    for line in portability_lines:
        assert any(term in line for term in _ALLOWED_PORTABILITY_TERMS), (
            f"portability line uses a non-canonical status term: {line!r}\n"
            f"Allowed terms: {sorted(_ALLOWED_PORTABILITY_TERMS)}"
        )


def test_capability_registry_no_python_internal_names() -> None:
    """Invariant 4: capabilities.md must not contain Python-internal class names
    or source paths from src/genia/."""
    text = read_text(_CAPABILITIES_DOC)
    for fragment in _PROHIBITED_INTERNAL_NAMES:
        assert fragment not in text, (
            f"capabilities.md must not reference Python internal name: {fragment!r}"
        )


def test_capability_registry_no_prohibited_phrases() -> None:
    """Invariants 5, 6, 9, 10: capabilities.md must not use prohibited
    phrasings that overclaim implementation status or future-host status."""
    text = read_text(_CAPABILITIES_DOC)
    for phrase in _PROHIBITED_PHRASES:
        assert phrase not in text, (
            f"capabilities.md contains prohibited phrase: {phrase!r}"
        )


def test_capability_registry_no_future_tense_in_contracts() -> None:
    """Invariant 10: capability contract field lines must not use future tense."""
    text = read_text(_CAPABILITIES_DOC)
    field_lines = [
        line for line in text.splitlines()
        if any(f"**{field}:**" in line for field in
               ["input", "output", "errors", "portability", "genia_surface", "name"])
    ]
    future_words = ["coming soon", "will be", "not yet"]
    for line in field_lines:
        for word in future_words:
            assert word not in line.lower(), (
                f"capability contract field line uses future-tense phrase {word!r}: {line!r}"
            )


def test_capability_registry_structured_absence_not_conflated_with_errors() -> None:
    """Invariant 11: json.parse and json.stringify must document failures as
    structured absence (none(...)) not as exception raises."""
    text = read_text(_CAPABILITIES_DOC)
    assert 'none("json-parse-error"' in text, (
        "capabilities.md must document json.parse failure as "
        'none("json-parse-error", context), not as a raised exception'
    )
    assert 'none("json-stringify-error"' in text, (
        "capabilities.md must document json.stringify failure as "
        'none("json-stringify-error", context), not as a raised exception'
    )
    assert 'raises `none(' not in text, (
        "capabilities.md must not describe structured absence as a raised exception"
    )


def test_capability_registry_no_core_ir_semantics() -> None:
    """Invariant 12: capabilities.md must not define Core IR nodes or language
    semantics that belong in GENIA_STATE.md."""
    text = read_text(_CAPABILITIES_DOC)
    ir_markers = ["IrPipeline", "IrOptionSome", "IrOptionNone", "IrBinary", "IrBlock"]
    for marker in ir_markers:
        assert marker not in text, (
            f"capabilities.md must not reference Core IR node: {marker!r} — "
            "Core IR semantics belong in docs/architecture/core-ir-portability.md"
        )


def test_capability_registry_maturity_notice_present() -> None:
    """Doc requirements: capabilities.md must carry the required maturity notice."""
    text = read_text(_CAPABILITIES_DOC)
    assert "Python is the reference host" in text, (
        "capabilities.md must include the maturity notice stating "
        "Python is the reference host"
    )
    assert "partial" in text.lower(), (
        "capabilities.md must include a maturity notice describing the "
        "registry contract as partial"
    )


def test_capability_registry_cross_referenced_from_host_interop_readme() -> None:
    """Spec §8.3: docs/host-interop/README.md must list capabilities.md in its
    start-here section."""
    text = read_text("docs/host-interop/README.md")
    assert "capabilities.md" in text, (
        "docs/host-interop/README.md must reference capabilities.md "
        "in its start-here list"
    )


def test_capability_registry_cross_referenced_from_capability_matrix() -> None:
    """Spec §8.2: HOST_CAPABILITY_MATRIX.md must reference capabilities.md
    as the per-capability contract source."""
    text = read_text("docs/host-interop/HOST_CAPABILITY_MATRIX.md")
    assert "capabilities.md" in text, (
        "HOST_CAPABILITY_MATRIX.md must reference capabilities.md "
        "as the formal per-capability contract document"
    )


def test_genia_state_records_capability_registry_exists() -> None:
    """Spec §8.1: GENIA_STATE.md §0 must record that the formal capability
    registry contract exists at docs/host-interop/capabilities.md."""
    text = read_text("GENIA_STATE.md")
    assert "capabilities.md" in text, (
        "GENIA_STATE.md §0 must record that the formal host capability "
        "registry contract is documented at docs/host-interop/capabilities.md"
    )


def test_rules_doc_8_4_mentions_slash_lowering_form() -> None:
    rules = read_text("GENIA_RULES.md")
    marker = "§8.4"
    idx = rules.find(marker)
    if idx == -1:
        marker = "8.4"
        idx = rules.find(marker)
    assert idx != -1, "GENIA_RULES.md must contain a §8.4 section"
    section_after = rules[idx:]
    next_section = section_after.find("\n## ", 1)
    section = section_after[:next_section] if next_section > 0 else section_after
    assert "SLASH" in section or "IrBinary" in section, (
        "GENIA_RULES.md §8.4 must document the SLASH accessor lowering form (IrBinary(op=SLASH))"
    )
