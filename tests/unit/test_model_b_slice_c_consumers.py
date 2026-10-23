"""Slice C RED host-local tests: arity-keyed consumers, effective help, autoload twin.

PYTHON REFERENCE HOST ONLY (issue #1269; test plan R6.E HL-4, HL-5). Each
consumer's own predicate is exercised against real function groups built from
source, so the table `(group shape -> accepted?)` records what every consumer
actually does rather than a blanket rule: route, outbound-HTTP and `@test`
consumers require one exact fixed signature (D3b); lifecycle binding has no
signature gate; `help`/`doc`/`meta` are introspection and must stay usable.

RED phase: legacy-only shapes pass today. Shapes that need pattern-headed or
fixed-plus-rest ordinary clauses cannot be constructed until Slice C GREEN, so
their rows fail with the current `model-b-not-implemented`/duplicate error.
Help text and its `Defined at` line are Python formatting and are not claimed
to be portable.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

import genia
from genia.callable import GeniaFunctionGroup
from genia.lifecycle_binding import (
    AnnotationCandidate,
    AnnotationInfo,
    LifecycleAnnotationBinding,
    discover_lifecycle_participants,
)
from genia.http_annotation_binding import resolve_http_annotation
from genia.server_route_binding import RouteDeclaration, discover_route_bindings
from genia.test_cli import discover_annotated_test_units
from genia.values import GeniaMap
from tests.unit.model_b_slice_c_support import REPO_ROOT, cli, fresh_env

# Group shapes for one-argument consumers (route). Each program defines `h`.
ONE_ARG_SHAPES = {
    "legacy-fixed-1": "h(r) = r",
    "legacy-rest-only": "h(r, ..x) = r",
    "legacy-two-arities": "h(r) = r\nh(r, s) = r",
    "pattern-single": "h({path: p}) = p",
    "fixed-plus-rest-same-minimum": "h(r) = r\nh(r, ..x) = r",
    "pattern-then-plain": "h(0) = 1\nh(r) = r",
}
ROUTE_ACCEPTS = {
    "legacy-fixed-1": True,
    "legacy-rest-only": False,
    "legacy-two-arities": False,
    "pattern-single": False,
    "fixed-plus-rest-same-minimum": False,
    "pattern-then-plain": False,
}

# Zero-argument shapes (outbound HTTP annotations, `@test`).
ZERO_ARG_SHAPES = {
    "legacy-fixed-0": "t() = 1",
    "legacy-rest-only": "t(..r) = 1",
    "legacy-0-and-1": "t() = 1\nt(a) = 2",
    "fixed-plus-rest-same-minimum": "t() = 1\nt(..r) = 2",
    "pattern-record-other-arity": "t() = 1\nt(0) = 2",
}
HTTP_ACCEPTS = {
    "legacy-fixed-0": True,
    "legacy-rest-only": False,
    "legacy-0-and-1": False,
    "fixed-plus-rest-same-minimum": False,
    "pattern-record-other-arity": False,
}
# `@test` has an arity-set predicate and, today, no rest-parameter check.
TEST_ACCEPTS = {
    "legacy-fixed-0": True,
    "legacy-rest-only": True,  # existing behavior: the arity-set predicate has no rest-parameter check
    "legacy-0-and-1": False,
    "fixed-plus-rest-same-minimum": False,
    "pattern-record-other-arity": False,
}


def _map(**fields: object) -> GeniaMap:
    value = GeniaMap()
    for key, item in fields.items():
        value = value.put(key, item)
    return value


def _group(source: str, name: str):
    env, _printed = fresh_env()
    genia.run_source(source, env, filename="consumers.genia")
    value = env.get(name)
    assert isinstance(value, GeniaFunctionGroup)
    return value


# --- route -----------------------------------------------------------------------------------


@pytest.mark.parametrize("shape", sorted(ONE_ARG_SHAPES))
def test_route_consumer_accepts_only_one_exact_fixed_one_argument_arm(shape):
    group = _group(ONE_ARG_SHAPES[shape], "h")
    declaration = RouteDeclaration(
        name="h",
        value=group,
        metadata=_map(route=_map(method="GET", path="/x")),
        target_kind="function",
        source_identity="entry.genia",
        source_index=0,
        source_location="entry.genia:1:1",
    )
    result = discover_route_bindings([declaration], entry_source_identity="entry.genia")
    accepted = len(result.routes) == 1 and not result.diagnostics
    assert accepted == ROUTE_ACCEPTS[shape]
    if not accepted:
        assert [d.reason for d in result.diagnostics] == [
            "@route handler must expose exactly one fixed one-argument function arm"
        ]


# --- outbound HTTP annotations ---------------------------------------------------------------


@pytest.mark.parametrize("shape", sorted(ZERO_ARG_SHAPES))
def test_http_annotation_consumer_requires_one_exact_fixed_zero_argument_arm(shape):
    group = _group(ZERO_ARG_SHAPES[shape], "t")
    group.metadata = group.metadata.put("http_annotation", _map(verb=genia.values.symbol("get"), path="/p"))
    if HTTP_ACCEPTS[shape]:
        assert resolve_http_annotation(group).get("path") == "/p"
    else:
        with pytest.raises(TypeError, match="^send_annotated expected a fixed zero-argument function$"):
            resolve_http_annotation(group)


# --- @test discovery -------------------------------------------------------------------------


@pytest.mark.parametrize("shape", sorted(ZERO_ARG_SHAPES))
def test_native_test_discovery_accepts_arity_set_zero_only(shape):
    env, _printed = fresh_env()
    genia.run_source(f'@test "case"\n{ZERO_ARG_SHAPES[shape]}', env, filename="suite.genia")
    units = discover_annotated_test_units(env)
    assert len(units) == 1
    error = (units[0].metadata or {}).get("discovery_error")
    assert (error is None) == TEST_ACCEPTS[shape]
    if error is not None:
        assert error == "@test functions must take zero arguments"


# --- lifecycle binding: no signature gate -----------------------------------------------------


@pytest.mark.parametrize("shape", sorted(ONE_ARG_SHAPES))
def test_lifecycle_participant_binding_accepts_every_group_shape(shape):
    group = _group(ONE_ARG_SHAPES[shape], "h")
    binding = LifecycleAnnotationBinding(
        phase="test_before",
        annotation_name="setup",
        filters={},
        ordering="source_order",
        required=False,
        participant_kind="callable",
        failure_policy="diagnostic",
    )
    candidate = AnnotationCandidate(
        name="h",
        value=group,
        annotations=[
            AnnotationInfo(name="setup", metadata={}, source_location={"file": "s.genia", "line": 1, "source": "@setup"})
        ],
        source_location={"file": "s.genia", "line": 1},
        source_identity="s.genia",
        source_index=1,
    )
    result = discover_lifecycle_participants(binding, [candidate])
    assert [p.declaration_name for p in result.participants] == ["h"]
    assert result.diagnostics == []


# --- help / doc / meta stay usable -------------------------------------------------------------


@pytest.mark.parametrize("shape", sorted(ONE_ARG_SHAPES))
def test_introspection_stays_usable_for_every_group_shape(shape):
    env, printed = fresh_env()
    genia.run_source(f'@doc "documented"\n{ONE_ARG_SHAPES[shape]}', env, filename="<command>")
    assert genia.run_source('doc("h")', env, filename="<command>") == "documented"
    genia.run_source('help("h")', env, filename="<command>")
    text = "".join(printed)
    assert "documented" in text
    assert "0x" not in text and "GeniaFunction" not in text
    meta = genia.run_source('meta("h")', env, filename="<command>")
    assert meta is not None


def test_help_lists_pattern_records_in_declaration_order_without_host_objects():
    env, printed = fresh_env()
    genia.run_source('h(0) = "zero"\nh(1) = "one"\nh(n) = "other"\nhelp("h")', env, filename="<command>")
    text = "".join(printed)
    lines = [ln for ln in text.splitlines() if ln.strip()]
    assert lines[0].startswith("h/1")
    assert "0x" not in text and "GeniaFunction" not in text and "<function" not in text
    # Declaration order is deterministic: rerunning in a fresh environment is identical.
    env2, printed2 = fresh_env()
    genia.run_source('h(0) = "zero"\nh(1) = "one"\nh(n) = "other"\nhelp("h")', env2, filename="<command>")
    assert "".join(printed2) == text


def test_effective_help_shows_inline_text_and_alias_category_today():
    """Three metadata channels: effective help is `inline` + alias category and never `canonical`."""
    source = (
        '@doc "canonical"\n'
        'f(x) = "inline" x\n'
        '@category "alias-category"\n'
        "a = f\n"
    )
    for name in ("f", "a"):
        env, printed = fresh_env()
        result = genia.run_source(source + f'help("{name}")', env, filename="<command>")
        assert repr(result) == "none('nil')"
        assert "".join(printed) == "f/1\nDefined at <command>:1\n\ninline\n\nCategory: alias-category\n"
        assert "canonical" not in "".join(printed)


# --- grep-level guard: no consumer calls get(n) on a possibly multi-record group -----------------

CONSUMER_MODULES = (
    "src/genia/server_route_binding.py",
    "src/genia/http_annotation_binding.py",
    "src/genia/test_cli.py",
    "src/genia/lifecycle_binding.py",
)


def test_no_consumer_selects_a_representative_record_without_a_cardinality_check():
    """Every `.get(n)` on a function group must be preceded by an arity-set cardinality check."""
    offenders = []
    for relative in CONSUMER_MODULES:
        path = REPO_ROOT / relative
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for func in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            body = ast.get_source_segment(text, func) or ""
            if re.search(r"\.get\(\d+\)", body) and "sorted_arities()" not in body:
                offenders.append(f"{relative}:{func.name}")
    assert offenders == []


# --- HL-5: autoload resolution twin with pattern clauses -------------------------------------


def test_autoload_resolution_matches_non_autoload_for_pattern_clauses(tmp_path: Path):
    source = 'pick(0) = "zero"\npick(n) = "other"\n[pick(0), pick(3)]'
    env, _ = fresh_env()
    assert genia.run_source(source, env) == ["zero", "other"]

    prelude_file = tmp_path / "std" / "prelude" / "pick.genia"
    prelude_file.parent.mkdir(parents=True)
    prelude_file.write_text('pick(0) = "zero"\npick(n) = "other"\n', encoding="utf-8")
    auto_env, _ = fresh_env()
    auto_env.register_host_autoload("pick", 1, str(prelude_file.resolve()), visibility="runtime-public")
    assert genia.run_source("[pick(0), pick(3)]", auto_env) == ["zero", "other"]


def test_entry_declaration_over_prelude_name_routing_is_characterized_today():
    """P12: an entry declaration on a prelude-owned name keeps its existing routing (D2)."""
    completed = cli("-c", "map(f, xs, extra) = [f, xs, extra]\nmap(1, 2, 3)")
    assert completed.returncode == 0
    assert completed.stdout == "[1, 2, 3]\n"
    assert not re.search(r"Traceback", completed.stderr)
