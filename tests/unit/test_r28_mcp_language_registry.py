"""#1099 PR A: registry projection, generator, probes, and drift gates for `genia_language_profile`.

Python-host tests of build-time governance: they add no Genia semantics. The wire stays
byte-identical to the pre-registry implementation (golden snapshot), the generated block in
`apps/mcp/mcp.genia` is checked against `docs/contract/semantic_facts.json`, and every
executable claim is verified by direct evaluation on the Python reference host.
"""

from __future__ import annotations

import copy
import json

import pytest

from genia.interpreter import make_global_env, run_source
from tools import gen_mcp_language_profile as gen
from tests.fixtures.r28_mcp_helpers import REPO_ROOT, REVISION, SERVER_PATH, PROFILE_TOOL, request, responses, run_messages, structured
from tests.unit.test_r28_mcp_language_profile import GOLDEN, _profile

pytestmark = pytest.mark.unit

REGISTRY = gen.load_registry()
SERVER = SERVER_PATH.read_text(encoding="utf-8")


def _direct(source):
    return run_source(source, make_global_env(), filename="<command>")


# --- registry validity and projection -------------------------------------------------------


def test_registry_is_valid():
    assert gen.validate(REGISTRY) == []


def test_committed_generated_block_matches_a_fresh_projection():
    assert gen.check(REGISTRY, SERVER) == []


def test_generated_block_is_delimited_and_unique():
    assert SERVER.count(gen.BEGIN) == 1 and SERVER.count(gen.END) == 1
    assert SERVER.index(gen.BEGIN) < SERVER.index(gen.END)


def test_a_hand_edit_inside_the_generated_markers_is_detected():
    start = SERVER.index(gen.BEGIN)
    edited = SERVER[:start] + SERVER[start:].replace("pattern_matching", "pattern_matchinq", 1)
    assert gen.check(REGISTRY, edited) != []


def test_a_missing_marker_is_detected():
    assert gen.check(REGISTRY, SERVER.replace(gen.END, "", 1)) != []


def test_wire_equals_the_registry_projection_and_the_golden_snapshot():
    language = _profile()
    language.pop("contract_revision")
    expected = gen.wire_projection(REGISTRY)
    for key, value in expected.items():
        assert language[key] == value, key
    assert language == GOLDEN
    assert set(language) == set(expected) | {"name", "examples"}


def test_plain_file_mode_equals_the_launcher_projection():
    (response,) = responses(run_messages([request("tools/call", 3, {"name": PROFILE_TOOL})], args=(REVISION,)))
    language = structured(response)[1]["result"]["language"]
    language.pop("contract_revision")
    assert language == GOLDEN


def test_state_sections_on_the_wire_come_from_the_anchor_crosswalk():
    table = REGISTRY["state_anchors"]
    for fact in REGISTRY["discovery"]["facts"]:
        wire = next(r for r in GOLDEN["discovery"]["facts"] if r["id"] == fact["id"])
        assert wire["state_sections"] == [table[a]["legacy_section"] for a in fact["anchors"]], fact["id"]


def test_no_hand_copy_of_governed_claims_outside_the_generated_block():
    outside = SERVER[: SERVER.index(gen.BEGIN)] + SERVER[SERVER.index(gen.END) :]
    for fact in REGISTRY["discovery"]["facts"]:
        assert fact["id"] not in outside, fact["id"]
        assert fact["summary"] not in outside, fact["id"]
    for token in ("first_match", "curated_non_exhaustive", "while_loop", "tail_call_optimization"):
        assert token not in outside, token


def test_examples_stay_native_and_are_evaluated_not_governed():
    assert "examples" not in REGISTRY["language"]
    assert "LANGUAGE_EXAMPLES" in SERVER[: SERVER.index(gen.BEGIN)] or "LANGUAGE_EXAMPLES" in SERVER[SERVER.index(gen.END) :]


def test_the_projection_has_no_python_host_dependency():
    for path in sorted((REPO_ROOT / "hosts" / "python").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert "semantic_facts" not in text and "mcp_language_profile" not in text, path.name


# --- mutation tests: a registry change without its projection fails -------------------------


def _mutate(fn):
    registry = copy.deepcopy(REGISTRY)
    fn(registry)
    return registry


def test_changing_a_fact_without_regenerating_fails_check():
    mutated = _mutate(lambda r: r["discovery"]["facts"][0].__setitem__("summary", "Branching uses guards."))
    assert gen.check(mutated, SERVER) != []


def test_removing_a_fact_fails_validation_or_check():
    mutated = _mutate(lambda r: r["discovery"]["facts"].pop())
    assert gen.validate(mutated) != [] or gen.check(mutated, SERVER) != []


def test_a_fact_without_evidence_fails_validation():
    mutated = _mutate(lambda r: r["discovery"]["facts"][0].__setitem__("evidence", []))
    assert gen.validate(mutated) != []


def test_an_unknown_anchor_or_status_fails_validation():
    assert gen.validate(_mutate(lambda r: r["discovery"]["facts"][0].__setitem__("anchors", ["state:nope"]))) != []
    assert gen.validate(_mutate(lambda r: r["discovery"]["facts"][0].__setitem__("status", "shipped"))) != []


def test_an_oversized_summary_fails_validation():
    assert gen.validate(_mutate(lambda r: r["discovery"]["facts"][0].__setitem__("summary", "x" * 257))) != []


def test_evidence_anchor_outside_cited_anchors_fails_validation():
    def change(r):
        r["discovery"]["facts"][0]["evidence"] = [{"kind": "state_text", "anchor": "state:tail-calls", "fragment": "x"}]

    assert gen.validate(_mutate(change)) != []


def test_regenerating_a_changed_registry_is_accepted_by_check():
    mutated = _mutate(lambda r: r["discovery"]["facts"][0].__setitem__("summary", "Branching uses patterns."))
    assert gen.check(mutated, gen.splice(SERVER, gen.render_block(mutated))) == []


# --- executable probes and manifest cross-checks --------------------------------------------


def _probe_absent_forms_are_absent():
    for source in ("if(true, 1, 2)", "while(true, 1)", "for(1, 2)"):
        with pytest.raises(Exception):
            _direct(source)


def _probe_tail_recursion_constant_stack():
    assert _direct("open count(0, acc) = acc\ncount(n, acc) = count(n - 1, acc + 1)\ncount(100000, 0)") == 100000


def _probe_pattern_dispatch_evaluates():
    assert _direct("open f(0) = 10\nf(n) = n\n[f(0), f(5)]") == [10, 5]


def _probe_pattern_kinds_evaluate():
    assert _direct("open f(0) = 1\nf(_) = 2\n[f(0), f(9)]") == [1, 2]  # literal, wildcard, first match
    assert _direct("((a, b) -> a + b)(1, 2)") == 3  # tuple
    assert _direct("h(p) =\n  [x, y] -> x + y\nh([3, 4])") == 7  # list
    assert _direct("k(p) =\n  {a: v} -> v\nk({a: 5})") == 5  # map
    assert _direct("open s(n) ? n > 0 = 1\ns(_) = 0\n[s(5), s(-1)]") == [1, 0]  # guard


def _probe_supported_forms_evaluate():
    assert _direct("1 + 2") == 3  # binary_expression, literal
    assert _direct("x = 4\nx") == 4  # variable
    assert _direct("sq(n) = n * n\nsq(3)") == 9  # function_definition, function_call
    assert _direct("f(x) = x ? x > 1 -> 5 |\n  _ -> 6\nf(2)") == 5  # case_expression
    assert _direct("[1, 2] |> length") == 2  # pipeline


def _probe_open_clause_rule():
    assert _direct("open gcd(a, 0) = a\ngcd(a, b) = gcd(b, a % b)\ngcd(48, 18)") == 6
    with pytest.raises(Exception):
        _direct("gcd(a, 0) = a\ngcd(a, b) = gcd(b, a % b)\ngcd(48, 18)")


def _probe_validated_pipeline_evaluates():
    """Evaluate the documented validated-pipeline shape directly (#1119).

    Evidence for `idioms.pipelines` and `validated_data_pipelines`: `lines |> keep_some(parse_int)`
    keeps only the parsed payloads, and `validate_each` returns one Outcome per record, `some` for a
    valid record and `err` for an invalid one.
    """
    assert _direct('["10", "oops", "20"] |> lines |> keep_some(parse_int) |> collect') == [10, 20]
    outcomes = _direct('validate_each([{name: "a"}, {}], (r) -> validate_required("name", r))')
    assert len(outcomes) == 2
    assert str(outcomes[0]).startswith("some(") and str(outcomes[1]).startswith("err(")


def _shown(source):
    """Return the evaluated value's string form with double quotes, so Outcome text matches the CLI display."""
    return str(_direct(source)).replace("'", '"')


def _probe_direct_call_vs_pipeline_outcome():
    """A9.2 rows 1-4 (#1084): a direct call receives the Outcome itself; a pipeline lifts over it."""
    inc = "inc(x) = x + 1\n"
    assert _shown(inc + "some(1) |> inc") == "some(2)"  # pipeline unwraps and re-wraps
    assert _shown(inc + "some(1) |> inc |> inc") == "some(3)"
    assert _shown(inc + 'inc(none("m"))') == 'none("m")'  # ordinary call short-circuits on none
    assert _shown(inc + 'none("m") |> inc') == 'none("m")'
    assert _shown(inc + 'err("bad") |> inc') == 'err("bad")'  # err propagates unchanged
    direct = _direct(inc + "inc(some(1))")  # the callee received some(1), not 1
    assert str(direct) != "some(2)" and str(direct).startswith("none(")


def _probe_err_is_not_absence():
    """A9 (#1084): `err(...)` is neither `none` nor `some`, and a later `unwrap_or` stage leaves it unchanged."""
    assert _direct('none?(err("e"))') is False
    assert _direct('is_some?(err("e"))') is False
    assert _shown('err("bad") |> unwrap_or(0)') == 'err("bad")'  # not converted to none or recovered


def _probe_recovery_wraps_pipeline():
    """A9 (#1084): `unwrap_or` recovers around the whole expression; as a later `|>` stage it never runs after `none`."""
    assert _direct('unwrap_or(0, parse_int("x"))') == 0
    assert _direct('unwrap_or(0, parse_int("7"))') == 7
    later_stage = _direct('parse_int("x") |> unwrap_or(0)')
    assert str(later_stage).startswith("none(")  # a later stage never runs after none


PROBES = {
    "absent_forms_are_absent": _probe_absent_forms_are_absent,
    "tail_recursion_constant_stack": _probe_tail_recursion_constant_stack,
    "pattern_dispatch_evaluates": _probe_pattern_dispatch_evaluates,
    "pattern_kinds_evaluate": _probe_pattern_kinds_evaluate,
    "supported_forms_evaluate": _probe_supported_forms_evaluate,
    "open_clause_rule": _probe_open_clause_rule,
    "validated_pipeline_evaluates": _probe_validated_pipeline_evaluates,
    # A9 (#1084): the registry does not reference these yet, so the referenced-equals-implemented
    # gate below is intentionally red until the implementation phase.
    "direct_call_vs_pipeline_outcome": _probe_direct_call_vs_pipeline_outcome,
    "err_is_not_absence": _probe_err_is_not_absence,
    "recovery_wraps_pipeline": _probe_recovery_wraps_pipeline,
}


def _manifest():
    return json.loads((REPO_ROOT / "spec" / "manifest.json").read_text(encoding="utf-8"))


MANIFEST_CHECKS = {
    "other_hosts_planned_not_implemented": lambda m: set(m["host_status"]["planned_hosts"]) == {"node", "java", "rust", "go"}
    and not set(m["host_status"]["planned_hosts"]) & set(m["host_status"]["implemented_hosts"]),
    "browser_scaffolded": lambda m: m["browser_runtime_adapter"]["status"] == "scaffolded"
    and m["browser_runtime_adapter"]["implemented_hosts"] == [],
    "cpp_host_implemented": lambda m: set(m["host_status"]["implemented_hosts"]) == {"python", "cpp"},
}


def test_every_referenced_probe_and_manifest_check_is_implemented_and_nothing_is_unreferenced():
    assert gen.referenced_probes(REGISTRY) == set(PROBES)
    assert gen.referenced_manifest_checks(REGISTRY) == set(MANIFEST_CHECKS)


@pytest.mark.parametrize("name", sorted(PROBES))
def test_executable_probe_holds(name):
    PROBES[name]()


@pytest.mark.parametrize("name", sorted(MANIFEST_CHECKS))
def test_manifest_cross_check_holds(name):
    assert MANIFEST_CHECKS[name](_manifest())


def test_validated_pipeline_registry_entries_are_anchored_and_probed():
    fact = next(f for f in REGISTRY["discovery"]["facts"] if f["id"] == "validated_data_pipelines")
    assert fact["anchors"] == ["state:validated-pipelines"]
    assert REGISTRY["state_anchors"]["state:validated-pipelines"] == {"legacy_section": "6"}
    assert any(i == {"kind": "probe", "name": "validated_pipeline_evaluates"} for i in fact["evidence"])
    idioms = REGISTRY["language"]["idioms"]
    assert "pipelines" in idioms["value"]
    assert any(i.get("anchor") == "state:validated-pipelines" for i in idioms["evidence"])
    assert len(REGISTRY["discovery"]["facts"]) == gen.DISCOVERY_FACT_COUNT == 14  # A9 (#1084): 13 -> 14


def test_the_direct_evaluation_helper_really_evaluates():
    assert _direct("1 + 2") == 3
