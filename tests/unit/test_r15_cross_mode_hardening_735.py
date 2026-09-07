"""E15-8 (#735) combined cross-mode, protected-value, Flow, and determinism hardening.

Individual R15 mechanisms (E15-1 through E15-7) already have focused specs and
unit tests. This file proves the *combined boundaries* the issue calls out:
cross-mode conformance, R10 protected-value non-leakage across every R15
metadata/diagnostic/schema path, bounded Flow/no-over-pull under a combined
chain of mechanisms, discriminator-invocation determinism, and R13/R14
no-ambient-state composition -- none of which change any runtime behavior
themselves (see test_template_recursive_733.py for the one genuine contract
fix this hardening pass found and repaired: recursive_template's own Python
call-stack usage).
"""

from pathlib import Path

import genia.interpreter as interpreter_module
from genia.builtins import make_global_env
from genia.utf8 import format_display
from genia.values import GeniaMap, GeniaOptionErr, symbol
from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import load_spec

REPO = Path(__file__).resolve().parents[2]
CROSS_MODE_SPECS = (
    REPO / "spec/cli/r15-cross-mode-command.yaml",
    REPO / "spec/cli/r15-cross-mode-file.yaml",
    REPO / "spec/cli/r15-cross-mode-pipe.yaml",
    REPO / "spec/parse/parse-r15-existing-call-forms.yaml",
    REPO / "spec/ir/r15-existing-call-ir.yaml",
)
SENTINEL = "TOP_SECRET_SENTINEL_735"


def test_e15_8_cross_mode_shared_conformance_inventory_exists():
    assert all(path.is_file() for path in CROSS_MODE_SPECS)


def test_e15_8_cross_mode_specs_execute_as_contract():
    for path in CROSS_MODE_SPECS:
        spec = load_spec(path)
        failures = compare_spec(spec, execute_spec(spec))
        assert failures == [], (path, failures)


def test_protected_value_never_leaks_through_default_description_diagnostic_or_schema():
    # A real R10 protected value (not a stand-in string) threaded through
    # default_field's missing-only default, template_description, accumulate's
    # diagnostics, and template_schema -- combined in one call, matching the
    # issue's explicit "descriptions/defaults/diagnostics/schema" boundary
    # list, using genuine R10 acquisition machinery rather than a hand-rolled
    # substitute.
    env = make_global_env(
        [],
        environment_snapshot_provider=lambda: {"TOKEN": SENTINEL},
        dotenv_snapshot_provider=lambda _path: b"",
    )
    provider = env.get("config_standard")(GeniaMap(), []).value
    protected = env.get("secret_view")(provider, "", symbol("purpose_735"))("TOKEN").value
    env.set("protected_default", protected)
    env.set("protected_present", protected)

    # (a) description + missing-only default insertion: description records
    # only that a default exists, never the literal protected value; the
    # inserted value renders as the opaque <protected> marker only.
    description_and_default = interpreter_module.run_source(
        """
Token = default_field(protected_default, refinement((x) -> true))
Wrapper = open_shape({token: Token})
[template_description(Token), accumulate(Wrapper, {})]
""",
        env,
    )
    rendered = format_display(description_and_default)
    assert SENTINEL not in rendered
    assert rendered == (
        "[some({kind: field_default, has_default: true, template: {kind: refinement}}), "
        "some({token: <protected>})]"
    )

    # (b) a present protected value that fails a refinement: the diagnostic's
    # reason must never carry the underlying value or context.
    diagnostic = interpreter_module.run_source(
        """
Token2 = refinement((x) -> x == "expected-plain-value")
Wrapper2 = open_shape({token: Token2})
accumulate(Wrapper2, {token: protected_present})
""",
        env,
    )
    assert isinstance(diagnostic, GeniaOptionErr)
    rendered_diagnostic = format_display(diagnostic)
    assert SENTINEL not in rendered_diagnostic
    assert rendered_diagnostic == (
        "err(accumulated-validation-failed, {diagnostics: "
        "[{path: [token], kind: mismatch, reason: refinement-mismatch}]})"
    )

    # (c) template_schema over a Template containing a default_field never
    # invokes the field, so it cannot leak the protected default either; it
    # fails deterministically like any other default_field, per E15-4.
    schema_result = interpreter_module.run_source("template_schema(Wrapper)", env)
    rendered_schema = format_display(schema_result)
    assert SENTINEL not in rendered_schema
    assert rendered_schema == "err(unsupported-template, {path: [token], kind: default_field})"


def test_combined_mechanisms_over_an_unbounded_flow_pull_only_demanded_elements():
    # Combines alternatives + accumulate (rather than a single mechanism, as
    # E15-3's own test already covers) inside an ordinary map stage over an
    # unbounded lazy Flow, terminated by take(n). If either mechanism forced
    # whole-source buffering or over-pulled, this would hang instead of
    # terminating with exactly 3 items.
    result = _run(
        "Shape = alternatives(\"kind\", {"
        "even: exact_shape({kind: refinement((x) -> x == \"even\"), n: refinement((x) -> mod(x, 2) == 0)}), "
        "odd: exact_shape({kind: refinement((x) -> x == \"odd\"), n: refinement((x) -> mod(x, 2) == 1)})"
        "})\n"
        "classify(r, n) =\n"
        "  (0, n) -> {kind: \"even\", n: n} |\n"
        "  (1, n) -> {kind: \"odd\", n: n}\n"
        "tag(n) = classify(mod(n, 2), n)\n"
        "naturals = evolve(1, (n) -> n + 1)\n"
        "naturals |> map(tag) |> map((record) -> accumulate(Shape, record)) |> take(3) |> collect"
    )
    assert isinstance(result, list)
    assert len(result) == 3
    assert [format_display(outcome) for outcome in result] == [
        "some({kind: odd, n: 1})",
        "some({kind: even, n: 2})",
        "some({kind: odd, n: 3})",
    ]


def test_alternatives_invokes_only_the_matching_branch_never_the_others():
    # Discriminator resolution is a closed map lookup, not sequential trial:
    # prove it by giving every branch a side-effecting predicate and checking
    # only the matching branch's predicate ever ran, across every branch and
    # repeated calls (determinism).
    log_and_run = (
        "log = ref([])\n"
        "mk_branch(tag) = exact_shape({kind: refinement((x) -> { ref_update(log, (l) -> [..l, tag]); x == tag })})\n"
        "Branches = alternatives(\"kind\", {a: mk_branch(\"a\"), b: mk_branch(\"b\"), "
        "c: mk_branch(\"c\"), d: mk_branch(\"d\"), e: mk_branch(\"e\")})\n"
    )
    for tag in ("a", "c", "e"):
        result = _run(log_and_run + f'[Branches({{kind: "{tag}"}}), ref_get(log)]')
        assert format_display(result) == f"[some({{kind: {tag}}}), [{tag}]]"

    # Repeated calls on the same instance remain deterministic: only the
    # requested branch runs each time, and prior calls never leave residue
    # that changes a later, different branch's outcome.
    repeated = _run(
        log_and_run
        + 'r1 = Branches({kind: "b"})\n'
        + 'r2 = Branches({kind: "d"})\n'
        + '[r1, r2, ref_get(log)]'
    )
    assert format_display(repeated) == "[some({kind: b}), some({kind: d}), [b, d]]"


def test_recursive_template_inside_lifecycle_repeat_has_no_ambient_state_crosstalk():
    # R13/R14 no-ambient-state guarantee: recursive_template validation
    # composed inside an R14 lifecycle_repeat must not acquire lifecycle
    # context ambiently, and per-element validation must not leak depth
    # state across sibling elements (each element revalidates the same
    # Tree Template independently, at varying depths, all within bound).
    result = _run(
        "Tree = recursive_template(\"tree\", (ref) -> alternatives(\"kind\", "
        "{leaf: exact_shape({kind: refinement((x) -> x == \"leaf\")}), "
        "node: exact_shape({kind: refinement((x) -> x == \"node\"), left: ref(\"tree\"), right: ref(\"tree\")})}), 3)\n"
        "peer() = { name: quote(p), enter: (scope) -> some(nil), exit: (scope, summary) -> some(nil) }\n"
        "process(scope) = {\n"
        "  element = lifecycle_context(scope, quote(element)) |> unwrap_or(none)\n"
        "  Tree(element)\n"
        "}\n"
        "records = [\n"
        "  {kind: \"leaf\"},\n"
        "  {kind: \"node\", left: {kind: \"leaf\"}, right: {kind: \"leaf\"}},\n"
        "  {kind: \"node\", left: {kind: \"node\", left: {kind: \"leaf\"}, right: {kind: \"leaf\"}}, right: {kind: \"leaf\"}}\n"
        "]\n"
        "results = lifecycle_repeat([peer()], records, process)\n"
        "results |> map((r) -> r.result)"
    )
    assert format_display(result) == (
        "[some(some({kind: leaf})), "
        "some(some({kind: node, left: {kind: leaf}, right: {kind: leaf}})), "
        "some(some({kind: node, left: {kind: node, left: {kind: leaf}, right: {kind: leaf}}, right: {kind: leaf}}))]"
    )


def _run(source: str):
    return interpreter_module.run_source(source, make_global_env([]), filename="<test>")
