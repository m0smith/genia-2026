"""Python reference-host checks for callback containers and opaque diagnostics."""

import pytest

from genia import make_global_env, run_source
from genia.sheet import make_sheet, sheet_column
from genia.values import GeniaProtected, GeniaRepresented, symbol
from hosts.python.mcp_worker_profile import ALLOWED_BINDINGS


def test_comparator_gets_fresh_rows_and_pairs_with_exact_cells():
    env = make_global_env([])
    protected = GeniaProtected("synthetic", object(), symbol("test"))
    represented = GeniaRepresented("fixture", [1])
    outcome = run_source('none("fixture")', env)
    mutable = [2]
    payloads = [protected, represented, outcome, mutable]
    ranks = [4, 1, 3, 2]
    source = make_sheet([["rank", ranks], ["payload", payloads]])
    original = source.columns
    by_rank = dict(zip(ranks, payloads, strict=True))
    retained = []

    def before(left, right):
        """Keep both rows alive while comparing their ranks."""
        retained.extend((left, right))
        return left[0][1] < right[0][1]

    env.set_host("before_fixture", before, visibility="entry-only")
    env.set_host("sheet_fixture", source, visibility="entry-only")
    result = run_source("sort_rows(before_fixture, sheet_fixture)", env)

    assert retained
    assert len({id(row) for row in retained}) == len(retained)
    pairs = [pair for row in retained for pair in row]
    assert len({id(pair) for pair in pairs}) == len(pairs)
    for row in retained:
        assert [pair[0] for pair in row] == ["rank", "payload"]
        assert row[1][1] is by_rank[row[0][1]]
    assert result is not source
    assert source.columns is original
    assert sheet_column("rank", source) == ranks
    assert all(a is b for a, b in zip(sheet_column("payload", source), payloads, strict=True))
    assert sheet_column("rank", result) == sorted(ranks)
    assert all(
        cell is by_rank[rank]
        for rank, cell in zip(sorted(ranks), sheet_column("payload", result), strict=True)
    )
    assert mutable == [2]
    assert represented.value == [1]


@pytest.mark.parametrize("nested", [False, True])
def test_protected_key_precedes_illegality_per_cell(nested):
    protected = GeniaProtected("synthetic", object(), symbol("test"))
    key = [[protected]] if nested else protected
    env = make_global_env([])
    env.set_host("left_fixture", make_sheet([["id", [key]]]), visibility="entry-only")
    with pytest.raises(TypeError, match=r"^protected-value: inner-join key at left row 0$") as error:
        run_source('left_fixture |> inner_join("id", "id", sheet([["id", [nil]]]))', env)
    assert error.value.__cause__ is None


def test_illegal_key_normalizes_diagnostic_and_suppresses_context():
    env = make_global_env([])
    run_source('right = sheet([["id", [{}]]])', env)
    with pytest.raises(TypeError, match=r"^inner_join expected a legal key at right row 0$") as error:
        run_source('sheet([["id", [1]]]) |> inner_join("id", "id", right)', env)
    assert error.value.__cause__ is None
    assert error.value.__suppress_context__


@pytest.mark.parametrize("key", [GeniaProtected("synthetic", object(), symbol("test")), {}])
def test_join_key_names_keep_existing_sheet_diagnostic(key):
    env = make_global_env([])
    env.set_host("key_fixture", key, visibility="entry-only")
    run_source('s = sheet([["id", [1]]])', env)
    with pytest.raises(TypeError) as inherited:
        run_source('column(key_fixture, s)', env)
    for source in ('inner_join(key_fixture, "id", s, s)', 'inner_join("id", key_fixture, s, s)'):
        with pytest.raises(TypeError) as actual:
            run_source(source, env)
        assert str(actual.value) == str(inherited.value)


@pytest.mark.parametrize("name,arity", [("sort_rows", 2), ("inner_join", 4)])
def test_relational_binding_is_runtime_owned_and_worker_allowed(name, arity):
    env = make_global_env([])
    assert env.is_runtime_owned(name)
    assert name in ALLOWED_BINDINGS
    assert callable(env.get(name))
    signature = f"{name}/{arity}"
    with pytest.raises(TypeError, match=signature):
        run_source(f"{name}()", env)
