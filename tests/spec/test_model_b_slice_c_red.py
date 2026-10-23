"""Slice C TEST-only RED harness (issue #1269, parent #1250).

LANGUAGE CONTRACT: the shared cases selected here are the frozen
``spec/{eval,error,cli}/model-b-c-*.yaml`` inventory (test plan section R6.D,
approved Option B). PYTHON REFERENCE HOST: this module executes them directly
through the existing shared-spec loader, ``execute_spec`` and ``compare_spec``;
it adds no runner, comparator, evaluator or expected-output store.

RED phase: the 55 existing-behavior guards pass on the Python reference host and
the 82 Model B future-behavior cases (all ``default_open_functions``) fail with
the real mismatch until Slice C GREEN. This harness deliberately bypasses the
external-host applicability gate so the unimplemented behavior is visible; it
never consults capability claims, and it uses no skip, xfail or slow marker.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs

REPO = Path(__file__).resolve().parents[2]
PREFIX = "model-b-c-"

# Frozen guard inventory: pass today and must keep passing through GREEN.
SLICE_C_GUARD_IDS = (
    "model-b-c-open-noncontiguous-arities",
    "model-b-c-open-alias-sees-later-arity",
    "model-b-c-open-immutable-alias-stays-live",
    "model-b-c-open-call-before-later-clause",
    "model-b-c-open-lambda-factory-distinct",
    "model-b-c-disp-p5-migration-drop-lower",
    "model-b-c-disp-p7-same-arity-ambiguity",
    "model-b-c-disp-fixed-over-varargs",
    "model-b-c-disp-no-matching-function",
    "model-b-c-disp-case-miss-identity",
    "model-b-c-hdr-block-prefix-once",
    "model-b-c-hdr-block-prefix-miss",
    "model-b-c-hdr-block-prefix-multi-call",
    "model-b-c-hdr-grouped-body-captures-header",
    "model-b-c-optim-collection-recursion",
    "model-b-c-opt-plain-identity-none",
    "model-b-c-opt-pipe-lift",
    "model-b-c-own-alias-call-live",
    "model-b-c-own-immutable-alias-live",
    "model-b-c-own-explicit-open-alias-unchanged",
    "model-b-c-own-import-inert",
    "model-b-c-own-extend-ordinary-rejected",
    "model-b-c-own-use-ordinary-base-unchanged",
    "model-b-c-own-entry-prelude-name",
    "model-b-c-d8-legacy-identical-header-dup",
    "model-b-c-d8-grouped-decl-one-key",
    "model-b-c-d8-prefix-and-capture",
    "model-b-c-d8-r20-flattening-unchanged",
    "model-b-c-imm-rebind-as-function",
    "model-b-c-imm-declare-after-function",
    "model-b-c-meta-binding-doc-merge",
    "model-b-c-meta-newer-key-overwrites",
    "model-b-c-meta-alias-no-copy",
    "model-b-c-meta-inline-doc-shared-via-alias",
    "model-b-c-meta-conflicting-inline-doc-before-install",
    "model-b-c-meta-three-channel-trio",
    "model-b-c-ann-later-annotation-suppressed",
    "model-b-c-ann-prior-effects-persist",
    "model-b-c-stage-closed-rejected",
    "model-b-c-main-legacy-main1-preferred",
    "model-b-c-main-legacy-main0-fallback",
    "model-b-c-main-legacy-rest-main-selected",
    "model-b-c-main-no-qualifying",
    "model-b-c-main-command-mode",
    "model-b-c-open-persistent-arities",
    "model-b-c-open-repl-alias-sees-later-arity",
    "model-b-c-ann-installed-clause-visible-via-alias",
    "model-b-c-ann-old-metadata-retained",
    "model-b-c-main-repl-never-selects",
    "model-b-c-key-legacy-dup-id",
    "model-b-c-key-rest-binders-legacy-duplicate",
    "model-b-c-meta-channel-binding-doc",
    "model-b-c-meta-channel-inline-doc",
    "model-b-c-meta-channel-alias-only",
    "model-b-c-meta-inline-doc-body-runs",
)

# Frozen Model B future-behavior inventory: every id requires
# ``default_open_functions`` (Option B, R7-D1) and fails until GREEN.
SLICE_C_GATED_IDS = (
    "model-b-c-open-pattern-after-plain",
    "model-b-c-open-noncontiguous-pattern",
    "model-b-c-pat-literal-base-case",
    "model-b-c-pat-guard-selects",
    "model-b-c-pat-guard-sees-header-binding",
    "model-b-c-pat-match-local-shadows-outer",
    "model-b-c-pat-list-rest",
    "model-b-c-pat-map",
    "model-b-c-pat-some",
    "model-b-c-pat-err",
    "model-b-c-pat-wildcard",
    "model-b-c-pat-first-match-wins",
    "model-b-c-pat-fixed-miss-no-varargs-fallthrough",
    "model-b-c-pat-fixed-miss-two-args-varargs",
    "model-b-c-pat-named-matcher",
    "model-b-c-pat-string-body-is-body",
    "model-b-c-key-true-vs-one",
    "model-b-c-key-one-vs-one-point-zero",
    "model-b-c-key-same-binary64-dup",
    "model-b-c-key-spelling-dup",
    "model-b-c-key-alpha-equivalent-dup",
    "model-b-c-key-guard-alpha-dup",
    "model-b-c-key-guard-differs-ok",
    "model-b-c-key-free-name-syntactic",
    "model-b-c-key-lambda-shadow-dup",
    "model-b-c-key-lambda-shadow-outer-slot-distinct",
    "model-b-c-key-quote-names-are-data",
    "model-b-c-key-named-matcher-distinct",
    "model-b-c-key-named-matcher-same-dup",
    "model-b-c-key-no-effects",
    "model-b-c-key-r20-delta-true-one",
    "model-b-c-key-r20-delta-one-float",
    "model-b-c-disp-p5-varargs-minima-ambiguity",
    "model-b-c-disp-p5-migration-fixed-clause",
    "model-b-c-disp-fixed-and-varargs-same-arity",
    "model-b-c-disp-no-matching-function-new-group",
    "model-b-c-disp-duplicate-pattern-header",
    "model-b-c-disp-case-miss-pattern-group",
    "model-b-c-disp-no-clause-ambiguity-single-unit",
    "model-b-c-hdr-guard-evaluated-once",
    "model-b-c-hdr-guard-order",
    "model-b-c-hdr-guard-error",
    "model-b-c-hdr-matcher-outcome",
    "model-b-c-hdr-recursion-tco",
    "model-b-c-optim-late-declaration",
    "model-b-c-opt-none-pattern-in-group-dispatches",
    "model-b-c-opt-other-arity-clause-not-aware",
    "model-b-c-opt-delegation-to-aware-callee",
    "model-b-c-opt-err-pipeline-value-short-circuits",
    "model-b-c-own-local-alias-rejected",
    "model-b-c-own-local-alias-pattern-clause",
    "model-b-c-own-local-alias-varargs",
    "model-b-c-own-alias-annotation-not-evaluated",
    "model-b-c-own-imported-alias-rejected",
    "model-b-c-own-two-modules-independent",
    "model-b-c-d8-forward-collision",
    "model-b-c-d8-reverse-collision",
    "model-b-c-d8-terminal-grouped-miss",
    "model-b-c-d8-earlier-pattern-miss-continues",
    "model-b-c-imm-rebind-as-pattern-function",
    "model-b-c-meta-pattern-clause-annotations",
    "model-b-c-ann-pattern-clause-variants",
    "model-b-c-mode-file-pattern-program",
    "model-b-c-mode-command-pattern-program",
    "model-b-c-mode-import-pattern-program",
    "model-b-c-main-pattern-not-selected",
    "model-b-c-main-pattern-guard-not-evaluated",
    "model-b-c-main-wildcard-not-selected",
    "model-b-c-main-multi-pattern-group-not-selected",
    "model-b-c-main-pattern-command-mode",
    "model-b-c-main-explicit-call-dispatches",
    "model-b-c-main-explicit-call-miss",
    "model-b-c-main-test-mode-unchanged",
    "model-b-c-open-persistent-env",
    "model-b-c-ann-repl-recovery",
    "model-b-c-main-repl-pattern-never-selects",
    "model-b-c-own-local-alias-state-after-rejection",
    "model-b-c-own-local-alias-owner-still-extendable",
    "model-b-c-mode-repl-failed-declaration-leaves-group",
    "model-b-c-key-unquote-active-dup",
    "model-b-c-key-unquote-nested-quoted-distinct",
    "model-b-c-key-unquote-nested-active-dup",
)

SLICE_C_CASE_IDS = SLICE_C_GUARD_IDS + SLICE_C_GATED_IDS

# Literal id -> exact ``requires`` table (GA-14). Replacing one capability by
# another, or adding/removing ``default_open_functions``, fails.
SLICE_C_REQUIRES = {
    "model-b-c-open-noncontiguous-arities": (),
    "model-b-c-open-alias-sees-later-arity": (),
    "model-b-c-open-immutable-alias-stays-live": ("immutable_bindings",),
    "model-b-c-open-call-before-later-clause": (),
    "model-b-c-open-pattern-after-plain": ("default_open_functions",),
    "model-b-c-open-noncontiguous-pattern": ("default_open_functions",),
    "model-b-c-open-lambda-factory-distinct": (),
    "model-b-c-pat-literal-base-case": ("default_open_functions",),
    "model-b-c-pat-guard-selects": ("default_open_functions",),
    "model-b-c-pat-guard-sees-header-binding": ("default_open_functions",),
    "model-b-c-pat-match-local-shadows-outer": ("default_open_functions",),
    "model-b-c-pat-list-rest": ("default_open_functions",),
    "model-b-c-pat-map": ("default_open_functions",),
    "model-b-c-pat-some": ("default_open_functions",),
    "model-b-c-pat-err": ("default_open_functions",),
    "model-b-c-pat-wildcard": ("default_open_functions",),
    "model-b-c-pat-first-match-wins": ("default_open_functions",),
    "model-b-c-pat-fixed-miss-no-varargs-fallthrough": ("default_open_functions",),
    "model-b-c-pat-fixed-miss-two-args-varargs": ("default_open_functions",),
    "model-b-c-pat-named-matcher": ("default_open_functions",),
    "model-b-c-pat-string-body-is-body": ("default_open_functions", "doc_help"),
    "model-b-c-key-true-vs-one": ("default_open_functions",),
    "model-b-c-key-one-vs-one-point-zero": ("default_open_functions",),
    "model-b-c-key-same-binary64-dup": ("default_open_functions",),
    "model-b-c-key-spelling-dup": ("default_open_functions",),
    "model-b-c-key-alpha-equivalent-dup": ("default_open_functions",),
    "model-b-c-key-guard-alpha-dup": ("default_open_functions",),
    "model-b-c-key-guard-differs-ok": ("default_open_functions",),
    "model-b-c-key-free-name-syntactic": ("default_open_functions",),
    "model-b-c-key-lambda-shadow-dup": ("default_open_functions",),
    "model-b-c-key-lambda-shadow-outer-slot-distinct": ("default_open_functions",),
    "model-b-c-key-quote-names-are-data": ("default_open_functions",),
    "model-b-c-key-named-matcher-distinct": ("default_open_functions",),
    "model-b-c-key-named-matcher-same-dup": ("default_open_functions",),
    "model-b-c-key-no-effects": ("default_open_functions",),
    "model-b-c-key-r20-delta-true-one": ("default_open_functions", "open_functions"),
    "model-b-c-key-r20-delta-one-float": ("default_open_functions", "open_functions"),
    "model-b-c-disp-p5-varargs-minima-ambiguity": ("default_open_functions",),
    "model-b-c-disp-p5-migration-fixed-clause": ("default_open_functions",),
    "model-b-c-disp-p5-migration-drop-lower": (),
    "model-b-c-disp-p7-same-arity-ambiguity": (),
    "model-b-c-disp-fixed-over-varargs": (),
    "model-b-c-disp-fixed-and-varargs-same-arity": ("default_open_functions",),
    "model-b-c-disp-no-matching-function": (),
    "model-b-c-disp-no-matching-function-new-group": ("default_open_functions",),
    "model-b-c-disp-duplicate-pattern-header": ("default_open_functions",),
    "model-b-c-disp-case-miss-identity": (),
    "model-b-c-disp-case-miss-pattern-group": ("default_open_functions",),
    "model-b-c-disp-no-clause-ambiguity-single-unit": ("default_open_functions",),
    "model-b-c-hdr-block-prefix-once": (),
    "model-b-c-hdr-block-prefix-miss": (),
    "model-b-c-hdr-block-prefix-multi-call": (),
    "model-b-c-hdr-grouped-body-captures-header": (),
    "model-b-c-hdr-guard-evaluated-once": ("default_open_functions",),
    "model-b-c-hdr-guard-order": ("default_open_functions",),
    "model-b-c-hdr-guard-error": ("default_open_functions",),
    "model-b-c-hdr-matcher-outcome": ("default_open_functions",),
    "model-b-c-hdr-recursion-tco": ("default_open_functions",),
    "model-b-c-optim-collection-recursion": (),
    "model-b-c-optim-late-declaration": ("default_open_functions",),
    "model-b-c-opt-none-pattern-in-group-dispatches": ("default_open_functions",),
    "model-b-c-opt-other-arity-clause-not-aware": ("default_open_functions",),
    "model-b-c-opt-delegation-to-aware-callee": ("default_open_functions",),
    "model-b-c-opt-err-pipeline-value-short-circuits": ("default_open_functions",),
    "model-b-c-opt-plain-identity-none": (),
    "model-b-c-opt-pipe-lift": (),
    "model-b-c-own-alias-call-live": (),
    "model-b-c-own-immutable-alias-live": ("immutable_bindings",),
    "model-b-c-own-local-alias-rejected": ("default_open_functions",),
    "model-b-c-own-local-alias-pattern-clause": ("default_open_functions",),
    "model-b-c-own-local-alias-varargs": ("default_open_functions",),
    "model-b-c-own-alias-annotation-not-evaluated": ("default_open_functions", "doc_help"),
    "model-b-c-own-imported-alias-rejected": ("default_open_functions", "multi_file_eval"),
    "model-b-c-own-explicit-open-alias-unchanged": ("open_functions",),
    "model-b-c-own-import-inert": ("multi_file_eval",),
    "model-b-c-own-extend-ordinary-rejected": ("multi_file_eval", "open_functions"),
    "model-b-c-own-use-ordinary-base-unchanged": ("multi_file_eval", "open_functions"),
    "model-b-c-own-two-modules-independent": ("default_open_functions", "multi_file_eval"),
    "model-b-c-own-entry-prelude-name": (),
    "model-b-c-d8-forward-collision": ("default_open_functions",),
    "model-b-c-d8-reverse-collision": ("default_open_functions",),
    "model-b-c-d8-terminal-grouped-miss": ("default_open_functions",),
    "model-b-c-d8-earlier-pattern-miss-continues": ("default_open_functions",),
    "model-b-c-d8-legacy-identical-header-dup": (),
    "model-b-c-d8-grouped-decl-one-key": (),
    "model-b-c-d8-prefix-and-capture": (),
    "model-b-c-d8-r20-flattening-unchanged": ("open_functions",),
    "model-b-c-imm-rebind-as-function": ("immutable_bindings",),
    "model-b-c-imm-rebind-as-pattern-function": ("default_open_functions", "immutable_bindings"),
    "model-b-c-imm-declare-after-function": ("immutable_bindings",),
    "model-b-c-meta-binding-doc-merge": ("doc_help",),
    "model-b-c-meta-newer-key-overwrites": ("doc_help",),
    "model-b-c-meta-alias-no-copy": ("doc_help",),
    "model-b-c-meta-inline-doc-shared-via-alias": ("doc_help",),
    "model-b-c-meta-conflicting-inline-doc-before-install": ("doc_help",),
    "model-b-c-meta-three-channel-trio": ("doc_help",),
    "model-b-c-meta-pattern-clause-annotations": ("default_open_functions", "doc_help"),
    "model-b-c-ann-later-annotation-suppressed": ("doc_help",),
    "model-b-c-ann-prior-effects-persist": ("doc_help",),
    "model-b-c-ann-pattern-clause-variants": ("default_open_functions", "doc_help"),
    "model-b-c-stage-closed-rejected": (),
    "model-b-c-mode-file-pattern-program": ("default_open_functions",),
    "model-b-c-mode-command-pattern-program": ("default_open_functions",),
    "model-b-c-mode-import-pattern-program": ("default_open_functions", "multi_file_eval"),
    "model-b-c-main-legacy-main1-preferred": (),
    "model-b-c-main-legacy-main0-fallback": (),
    "model-b-c-main-legacy-rest-main-selected": (),
    "model-b-c-main-no-qualifying": (),
    "model-b-c-main-command-mode": (),
    "model-b-c-main-pattern-not-selected": ("default_open_functions",),
    "model-b-c-main-pattern-guard-not-evaluated": ("default_open_functions",),
    "model-b-c-main-wildcard-not-selected": ("default_open_functions",),
    "model-b-c-main-multi-pattern-group-not-selected": ("default_open_functions",),
    "model-b-c-main-pattern-command-mode": ("default_open_functions",),
    "model-b-c-main-explicit-call-dispatches": ("default_open_functions",),
    "model-b-c-main-explicit-call-miss": ("default_open_functions",),
    "model-b-c-main-test-mode-unchanged": ("default_open_functions",),
    "model-b-c-open-persistent-arities": ("repl",),
    "model-b-c-open-repl-alias-sees-later-arity": ("repl",),
    "model-b-c-open-persistent-env": ("default_open_functions", "repl"),
    "model-b-c-ann-installed-clause-visible-via-alias": ("doc_help", "repl"),
    "model-b-c-ann-old-metadata-retained": ("doc_help", "repl"),
    "model-b-c-ann-repl-recovery": ("default_open_functions", "doc_help", "repl"),
    "model-b-c-main-repl-never-selects": ("repl",),
    "model-b-c-main-repl-pattern-never-selects": ("default_open_functions", "repl"),
    "model-b-c-own-local-alias-state-after-rejection": ("default_open_functions", "repl"),
    "model-b-c-own-local-alias-owner-still-extendable": ("default_open_functions", "repl"),
    "model-b-c-mode-repl-failed-declaration-leaves-group": ("default_open_functions", "immutable_bindings", "repl"),
    "model-b-c-key-unquote-active-dup": ("default_open_functions",),
    "model-b-c-key-unquote-nested-quoted-distinct": ("default_open_functions",),
    "model-b-c-key-unquote-nested-active-dup": ("default_open_functions",),
    "model-b-c-key-legacy-dup-id": (),
    "model-b-c-key-rest-binders-legacy-duplicate": (),
    "model-b-c-meta-channel-binding-doc": ("doc_help",),
    "model-b-c-meta-channel-inline-doc": ("doc_help",),
    "model-b-c-meta-channel-alias-only": ("doc_help",),
    "model-b-c-meta-inline-doc-body-runs": (),
}

CAPABILITY = "default_open_functions"


def _load():
    specs, invalid = discover_specs()
    return specs, invalid


_SPECS, _INVALID = _load()
_SLICE_C = {s.name: s for s in _SPECS if s.name.startswith(PREFIX)}


def test_case_inventory_counts_are_frozen() -> None:
    assert len(SLICE_C_GUARD_IDS) == 55
    assert len(SLICE_C_GATED_IDS) == 82
    assert len(SLICE_C_CASE_IDS) == 137
    assert len(set(SLICE_C_CASE_IDS)) == 137
    assert set(SLICE_C_REQUIRES) == set(SLICE_C_CASE_IDS)


def test_loader_has_no_invalid_specs_and_exact_case_id_equality() -> None:
    assert _INVALID == [], [f"{i.path}: {i.message}" for i in _INVALID]
    loaded_names = [s.name for s in _SPECS if s.name.startswith(PREFIX)]
    assert len(loaded_names) == len(set(loaded_names)), "duplicate model-b-c-* names"
    assert set(loaded_names) == set(SLICE_C_CASE_IDS)
    assert len(loaded_names) == 137
    for spec in _SLICE_C.values():
        assert spec.path.stem == spec.name


def test_exact_requires_per_case() -> None:
    mismatches = {
        name: (tuple(_SLICE_C[name].requires), expected)
        for name, expected in SLICE_C_REQUIRES.items()
        if tuple(_SLICE_C[name].requires) != tuple(expected)
    }
    assert not mismatches, mismatches


def test_only_future_cases_require_the_new_capability() -> None:
    gated = {n for n, s in _SLICE_C.items() if CAPABILITY in s.requires}
    assert gated == set(SLICE_C_GATED_IDS)
    assert len(gated) == 82
    for name in SLICE_C_GUARD_IDS:
        assert CAPABILITY not in _SLICE_C[name].requires, name
    # Option B: the P5 varargs-minima ambiguity is gated like every future case.
    assert CAPABILITY in _SLICE_C["model-b-c-disp-p5-varargs-minima-ambiguity"].requires


def test_known_host_gap_lists_exactly_the_gated_ids() -> None:
    gaps = json.loads((REPO / "spec" / "known_host_gaps.json").read_text(encoding="utf-8"))["gaps"]
    entry = [g for g in gaps if g["capability"] == CAPABILITY]
    assert len(entry) == 1
    assert entry[0]["affected_host"] == "cpp"
    assert entry[0]["tracking_issue"] == "m0smith/genia-2026#1269"
    assert sorted(entry[0]["affected_tests"]) == sorted(SLICE_C_GATED_IDS)


def test_harness_contains_no_skip_xfail_slow_or_loopback_classification() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    forbidden = {"skip", "skipif", "xfail", "importorskip", "slow", "loopback", "full_conformance"}
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in forbidden:
            if isinstance(node.value, (ast.Name, ast.Attribute)):
                found.add(node.attr)
    assert not found, found
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "pytestmark"]
    ini = (REPO / "pytest.ini").read_text(encoding="utf-8")
    assert "xfail_strict" not in ini and "--runxfail" not in ini


@pytest.mark.parametrize("name", SLICE_C_CASE_IDS)
def test_slice_c_shared_case(name: str) -> None:
    """Execute one frozen case through the existing runner machinery.

    Guards must pass today; gated future cases fail until Slice C GREEN. The
    actual-versus-expected streams are retained in the assertion message.
    """
    spec = _SLICE_C[name]
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)
    assert not failures, (
        f"{name} ({'future' if name in SLICE_C_GATED_IDS else 'guard'}) mismatch: "
        + "; ".join(f"{f.field}: expected {f.expected!r} actual {f.actual!r}" for f in failures)
    )
