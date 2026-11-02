"""D2a RED: mixed-record view dispatch through the shared engine (#1250).

Acceptance ID D2a-06 (design sections 3.4-3.6, 6.3). PYTHON REFERENCE HOST ONLY.
Views are built with the private `link_view`; nothing evaluates `extend`/`use` over an
ordinary base from source. Dispatch classes and texts are the unchanged R20 family.
Matcher Outcome and ordinary-base TCO cases invoke a published mixed view.
"""

import pytest

import genia
from genia import callable as callables
from genia.callable import (
    OpenFunctionClauseAmbiguityError, OpenFunctionError, OpenFunctionNoMatchingCaseError,
    OpenFunctionNoMatchingFunctionError, OpenFunctionVarargsAmbiguityError,
)
from tests.unit.model_b_d2a_support import base_world, contributor, frozen, linking


def view_of(tmp_path, base_source, *contributions):
    """Build (root, view, env-with-contributions) for base `f` plus named contributor sources."""
    root, entry, module, group = base_world(tmp_path, base_source)
    units = [contributor(root, entry, tmp_path, name, group, clauses) for name, clauses in contributions]
    return root, linking().link_view(frozen(module, group), units), (root, entry, group)


def test_d2a_06_identifier_header_base_with_open_clause_contributions(tmp_path):
    _, view, _ = view_of(tmp_path, "f(x, y) = \"base\"\n", ("ext", ["f(0) = \"zero\"", "f(n) = \"one-arg\""]))
    assert view(1, 2) == "base" and view(0) == "zero" and view(7) == "one-arg"
    with pytest.raises(OpenFunctionNoMatchingFunctionError) as caught:
        view(1, 2, 3)
    assert str(caught.value).startswith("No matching function: f/3. Available:")


def test_d2a_06_pattern_header_base_and_no_matching_case(tmp_path):
    _, view, _ = view_of(tmp_path, "f(0) = \"base-zero\"\n", ("ext", ["f(1) = \"ext-one\""]))
    assert view(0) == "base-zero" and view(1) == "ext-one"
    with pytest.raises(OpenFunctionNoMatchingCaseError) as caught:
        view(2)
    assert str(caught.value).startswith("No matching case for function f/1 with arguments")


def test_d2a_06_identifier_header_base_makes_a_matching_specialization_ambiguous(tmp_path):
    _, view, _ = view_of(tmp_path, "f(x) = \"base\"\n", ("ext", ["f(0) = \"zero\""]))
    assert view(5) == "base"  # the specialization does not match, so the base is selected
    with pytest.raises(OpenFunctionClauseAmbiguityError) as caught:
        view(0)
    assert str(caught.value) == (
        "open-function-clause-ambiguity: f/1 matched clauses in more than one unit ['base', 'ext']"
    )


def test_d2a_06_fixed_arity_wins_over_varargs_and_varargs_minima_are_ambiguous(tmp_path):
    _, view, _ = view_of(tmp_path, "f(a) = \"fixed1\"\n", ("ext", ["f(a, b, ..r) = \"var2\""]))
    assert view(1) == "fixed1" and view(1, 2) == "var2" and view(1, 2, 3, 4) == "var2"
    _, ambiguous, _ = view_of(
        tmp_path / "v", "f(a, ..r) = \"var1\"\n", ("ext", ["f(a, b, ..r) = \"var2\""]),
    )
    assert ambiguous(1) == "var1"
    with pytest.raises(OpenFunctionVarargsAmbiguityError) as caught:
        ambiguous(1, 2)
    assert str(caught.value).startswith("open-function-varargs-ambiguity: f/2 matches more than one varargs shape")


def test_d2a_06_header_frame_capture_keeps_each_clause_in_its_own_module_scope(tmp_path):
    root, entry, module, group = base_world(tmp_path, "offset = 10\nf(x, y) = x + y + offset\n")
    (tmp_path / "ext.genia").write_text(
        "import iface\noffset = 1000\nextend iface.f(0) = offset\n", encoding="utf-8",
    )
    ext = root.load_module("ext", entry)
    unit = callables.GeniaOpenContributionUnit(
        group.owner, "ext", list(ext.contributions[("iface", "f")].clauses), target=group,
    )
    view = linking().link_view(frozen(module, group), [unit])
    assert view(1, 2) == 13  # base clause: base closure
    assert view(0) == 1000  # contributor clause: contributor closure, never rebound
    assert view(1, 2) == view(1, 2)


def test_d2a_06_body_level_case_miss_is_a_body_error_not_a_dispatch_diagnostic(tmp_path):
    _, view, _ = view_of(tmp_path, "f(x) = (0) -> \"z\"\n", ("ext", ["f(1, 2) = 0"]))
    assert view(0) == "z"
    with pytest.raises(RuntimeError) as caught:
        view(5)
    assert not isinstance(caught.value, OpenFunctionError)
    assert str(caught.value).startswith("No matching case for function f")


def test_d2a_06_effectful_guard_runs_once_per_candidate_discovery(tmp_path):
    root, entry, module, group = base_world(tmp_path, "f(0, y) = \"base\"\n")
    hits = []
    root.set_host("bump", lambda value: hits.append(value) or True, visibility="runtime-public")
    unit = contributor(root, entry, tmp_path, "ext", group, ["f(a, b) ? bump(a) = \"ext\""])
    view = linking().link_view(frozen(module, group), [unit])
    assert view(1, 2) == "ext" and hits == [1]  # exactly one guard evaluation for the one candidate


def test_d2a_06_option_awareness_uses_the_union_over_the_stratum(tmp_path):
    handles_none = callables._callable_explicitly_handles_none
    handles_some = callables._callable_explicitly_handles_some
    _, plain, _ = view_of(tmp_path, "f(0) = 0\n", ("ext", ["f(1) = 1"]))
    assert not handles_none(plain, 1) and not handles_some(plain, 1)
    _, aware, _ = view_of(tmp_path / "n", "f(0) = 0\n", ("ext", ["f(none(m)) = 1"]))
    assert handles_none(aware, 1) and not handles_some(aware, 1)
    _, some_aware, _ = view_of(tmp_path / "s", "f(0) = 0\n", ("ext", ["f(some(v)) = 1"]))
    assert handles_some(some_aware, 1) and handles_none(some_aware, 1)
    _, ident, _ = view_of(tmp_path / "i", "f(x) = x\n", ("ext", ["f(a, b) = 1"]))
    assert not handles_none(ident, 1)  # identifier-header record uses _record_handles_none
    _, case_aware, _ = view_of(tmp_path / "c", "f(x) = (none(m)) -> 1 | (v) -> v\n", ("ext", ["f(a, b) = 1"]))
    assert handles_none(case_aware, 1)


def test_d2a_06_none_argument_reaches_an_aware_contribution_only(tmp_path):
    root, view, _ = view_of(tmp_path, "f(0) = 0\n", ("ext", ["f(none(m)) = \"handled\""]))
    root.publish_view("v", view)
    assert genia.run_source('v(none("e"))', root, filename="<command>") == "handled"
    root2, plain, _ = view_of(tmp_path / "p", "f(0) = 0\n", ("ext", ["f(1) = 1"]))
    root2.publish_view("v", plain)
    result = genia.run_source('v(none("e"))', root2, filename="<command>")
    assert result == genia.run_source('none("e")', root2, filename="<command>")


def test_d2a_06_self_tail_recursion_through_a_published_view_is_constant_stack(tmp_path):
    root, entry, module, group = base_world(tmp_path, "f(a) = a\n")
    genia.run_source(
        "import iface\nextend iface.f(0, acc) = acc\nextend iface.f(n, acc) = walk(n - 1, acc + 1)\n",
        root, filename=entry,
    )
    harvested = root.open_contributions[("iface", "f")]
    unit = callables.GeniaOpenContributionUnit(group.owner, "entry", list(harvested.clauses), target=group)
    view = linking().link_view(frozen(module, group), [unit])
    root.publish_view("walk", view)
    assert genia.run_source("walk(60000, 0)", root, filename="<command>") == 60000
    assert root.get("walk") is view


# These sources are also loaded by the diagnostic fixture probe, without linking.
MATCHER_SOURCE = '''pattern Broken(value) = match_probe(value)
f(Broken(v)) ? guard_probe(v) = body_probe(v)
f(v) = fallback_probe(v)
'''
SELF_SOURCE = 'f(n, acc) = (0, a) -> a | (k, a) -> f(n - 1, acc + 1)\n'
MUTUAL_SOURCE = 'f(n, acc) = (0, a) -> a | (k, a) -> peer(n - 1, acc + 1)\n'


def test_d2a_06_matcher_err_is_the_exact_call_value_without_guard_body_or_fallthrough(tmp_path):
    events = []
    root = genia.make_global_env([])
    outcome = genia.run_source('err("matcher-failed", {stage: "header"})', root)
    root.set_host('match_probe', lambda value: events.append(('matcher', value)) or outcome,
                  visibility='runtime-public')
    for name in ('guard_probe', 'body_probe', 'fallback_probe'):
        root.set_host(name, lambda value, label=name: events.append((label, value)) or True,
                      visibility='runtime-public')
    root, entry, module, group = base_world(tmp_path, MATCHER_SOURCE, root=root)
    unit = contributor(root, entry, tmp_path, 'ext', group, ['f(a, b) = 0'])
    view = linking().link_view(frozen(module, group), [unit])
    root.publish_view('v', view)
    assert genia.run_source('v(7)', root, filename=entry) is outcome
    assert events == [('matcher', 7)]


def test_d2a_06_ordinary_identifier_header_self_tco_through_published_view(tmp_path):
    root, entry, module, group = base_world(tmp_path, SELF_SOURCE)
    unit = contributor(root, entry, tmp_path, 'ext', group, ['f(a, b, c) = 0'])
    view = linking().link_view(frozen(module, group), [unit])
    closure = group.records[0].closure
    closure.publish_view('f', view)  # actual recursive lookup must return the linked view
    root.publish_view('walk', view)
    assert closure.get('f') is view
    assert view.base.clauses[0].pattern is None
    assert genia.run_source('walk(60000, 0)', root, filename=entry) == 60000


def test_d2a_06_ordinary_identifier_headers_mutually_recurse_through_two_views(tmp_path):
    root, entry, module, group = base_world(tmp_path, MUTUAL_SOURCE,
                                          {'other': MUTUAL_SOURCE})
    other = root.load_module('other', entry)
    other_group = other.get_export('f')
    unit = contributor(root, entry, tmp_path, 'ext', group, ['f(a, b, c) = 0'])
    unit2 = callables.GeniaOpenContributionUnit(other_group.owner, 'ext', list(unit.clauses),
                                               target=other_group)
    first = linking().link_view(frozen(module, group), [unit])
    second = linking().link_view(frozen(other, other_group), [unit2])
    group.records[0].closure.publish_view('peer', second)
    other_group.records[0].closure.publish_view('peer', first)
    root.publish_view('walk', first)
    assert first.base.clauses[0].pattern is None and second.base.clauses[0].pattern is None
    assert genia.run_source('walk(60001, 0)', root, filename=entry) == 60001


def test_d2a_06_some_invocation_and_awareness_exclude_other_arity_strata(tmp_path):
    root, view, _ = view_of(tmp_path, 'f(0) = 0\n',
                            ('ext', ['f(some(v)) = v + 10', 'f(none(m), y) = y']))
    root.publish_view('v', view)
    assert genia.run_source('v(some(7))', root) == 17
    absent = genia.run_source('none("absent")', root)
    root.set_host('absent', absent, visibility='runtime-public')
    # R20 contract 5.2: a selected some pattern also admits none to dispatch.
    # No selected unary clause matches it, so this is a dispatch miss, not propagation.
    with pytest.raises(OpenFunctionNoMatchingCaseError) as caught:
        genia.run_source('v(absent)', root)
    assert str(caught.value) == 'No matching case for function f/1 with arguments [none("absent")]'
    assert callables._callable_explicitly_handles_none(view, 1)
    assert callables._callable_explicitly_handles_none(view, 2)
    assert genia.run_source('v(absent, 9)', root) == 9

    # Isolate the other-arity negative: there must be no unary some/none pattern.
    excluded_root, excluded, _ = view_of(
        tmp_path / 'excluded', 'f(0) = 0\n',
        ('ext', ['f(1) = 1', 'f(none(m), y) = y']))
    excluded_root.publish_view('v', excluded)
    excluded_root.set_host('absent', absent, visibility='runtime-public')
    assert not callables._callable_explicitly_handles_none(excluded, 1)
    assert genia.run_source('v(absent)', excluded_root) is absent
    assert callables._callable_explicitly_handles_none(excluded, 2)
    assert genia.run_source('v(absent, 9)', excluded_root) == 9


def test_d2a_06_ambiguity_runs_each_guard_once_and_no_bodies(tmp_path):
    from collections import Counter

    events = []
    root = genia.make_global_env([])
    root.set_host('mark', lambda label, answer: events.append(label) or answer,
                  visibility='runtime-public')
    root, entry, module, group = base_world(
        tmp_path, 'f(x) ? mark("base-guard", true) = mark("base-body", 1)\n', root=root)
    unit = contributor(root, entry, tmp_path, 'ext', group, [
        'f(x) ? mark("false-guard", false) = mark("unselected-body", 2)',
        'f(x) ? mark("ext-guard", true) = mark("ext-body", 3)',
        'f(x) ? mark("late-guard", true) = mark("late-body", 4)',
    ])
    view = linking().link_view(frozen(module, group), [unit])
    root.publish_view('v', view)
    with pytest.raises(OpenFunctionClauseAmbiguityError):
        genia.run_source('v(1)', root, filename=entry)
    assert Counter(events) == Counter({'base-guard': 1, 'false-guard': 1, 'ext-guard': 1})


def test_d2a_06_fixed_miss_never_falls_back_to_same_unit_varargs(tmp_path):
    root, view, _ = view_of(tmp_path, 'f(0,y)="fixed"\nf(a,b,..r)="varargs"\n',
                            ('ext', ['f() = "zero"']))
    root.publish_view('v', view)
    assert genia.run_source('v(0,2)', root) == 'fixed'
    with pytest.raises(OpenFunctionNoMatchingCaseError):
        genia.run_source('v(1,2)', root)
    assert genia.run_source('v(1,2,3)', root) == 'varargs'


def test_d2a_06_identifier_header_stops_its_unit_before_later_pattern_guards(tmp_path):
    events = []
    root = genia.make_global_env([])
    root.set_host('late_guard', lambda value: events.append(value) or True,
                  visibility='runtime-public')
    root, entry, module, group = base_world(
        tmp_path, 'f(0)="first"\nf(x)=x+10\nf(v) ? late_guard(v) = 99\n', root=root)
    unit = contributor(root, entry, tmp_path, 'ext', group, ['f(a,b)=0'])
    view = linking().link_view(frozen(module, group), [unit])
    root.publish_view('v', view)
    assert genia.run_source('v(0)', root, filename=entry) == 'first'
    assert genia.run_source('v(3)', root, filename=entry) == 13
    assert events == []
