"""Python reference-host protection and identity checks under R31 decision F6."""

import pytest

from genia import make_global_env, run_source
from genia.sheet import make_sheet, sheet_column
from genia.values import (
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaPair,
    GeniaProtected,
    GeniaRepresented,
    symbol,
)

SENTINEL = "r31-synthetic-protected-payload"
FACET = "r31-synthetic-facet"


@pytest.fixture
def carrier():
    return GeniaProtected(SENTINEL, object(), symbol("fixture"))


def _represented(value):
    return GeniaRepresented(FACET, value)


@pytest.mark.parametrize(
    "wrap",
    [
        pytest.param(lambda token: token, id="direct"),
        pytest.param(_represented, id="represented"),
        pytest.param(lambda token: [_represented(token)], id="list"),
        pytest.param(lambda token: (_represented(token),), id="tuple"),
        pytest.param(lambda token: GeniaPair(0, _represented(token)), id="pair"),
        pytest.param(lambda token: GeniaMap().put("value", _represented(token)), id="map"),
        pytest.param(lambda token: GeniaOptionSome(_represented(token)), id="some"),
        pytest.param(lambda token: GeniaOptionNone("fixture", _represented(token)), id="none"),
        pytest.param(lambda token: GeniaOptionErr(_represented(token)), id="err"),
        pytest.param(lambda token: make_sheet([["inner", [_represented(token)]]]), id="sheet"),
        pytest.param(lambda token: [GeniaMap(), _represented(token)], id="illegal-first"),
        pytest.param(lambda token: [_represented(token), GeniaMap()], id="protected-first"),
    ],
)
@pytest.mark.parametrize("side", ["left", "right"])
def test_protection_precedes_legality_and_uses_opaque_diagnostic(carrier, wrap, side):
    env = make_global_env([])
    left = [0, wrap(carrier)] if side == "left" else [0, 1]
    right = [0, wrap(carrier)] if side == "right" else [0, 1]
    env.set_host("left_fixture", make_sheet([["secret_left_name", left]]), visibility="entry-only")
    env.set_host("right_fixture", make_sheet([["secret_right_name", right]]), visibility="entry-only")

    with pytest.raises(TypeError) as failure:
        run_source(
            'left_fixture |> inner_join("secret_left_name", "secret_right_name", right_fixture)',
            env,
        )

    diagnostic = str(failure.value)
    assert diagnostic == f"protected-value: inner-join key at {side} row 1"
    assert SENTINEL not in diagnostic
    assert FACET not in diagnostic
    assert failure.value.__cause__ is None


def test_protected_non_key_cells_remain_exact(carrier):
    env = make_global_env([])
    wrapped = _represented(carrier)
    left = make_sheet([["id", [1]], ["left_value", [carrier]]])
    right = make_sheet([["id", [1, 1]], ["right_value", [wrapped, carrier]]])
    env.set_host("left_fixture", left, visibility="entry-only")
    env.set_host("right_fixture", right, visibility="entry-only")

    result = run_source('inner_join("id", "id", right_fixture, left_fixture)', env)

    assert result is not left and result is not right
    assert sheet_column("id", result) == [1, 1]
    assert all(value is carrier for value in sheet_column("left_value", result))
    first, second = sheet_column("right_value", result)
    assert first is wrapped
    assert second is carrier
    assert sheet_column("left_value", left)[0] is carrier
    assert sheet_column("right_value", right)[0] is wrapped
