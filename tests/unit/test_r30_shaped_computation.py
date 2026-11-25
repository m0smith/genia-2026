"""Python host-injection checks for opaque cells, authority and callable state."""

import pytest

from genia import make_global_env, run_source
from genia.callable import GeniaClosedFunction
from genia.configuration import create_declassification_authority
from genia.utf8 import format_debug
from genia.values import symbol

SENTINEL = "R30_SYNTHETIC_PROTECTED_SENTINEL"


@pytest.fixture
def protected_env():
    """Construct a synthetic protected cell and inject authority through the host."""
    env = make_global_env([])
    provider = run_source(
        f'p = config_provider([{{kind: quote(values), values: {{K: "{SENTINEL}"}}}}]) |> unwrap_or(nil)\n'
        'token = secret_get(p, "K", quote(demo)) |> unwrap_or(nil)\n'
        's = sheet([["old", [token]]])\np',
        env,
    )
    authority = create_declassification_authority(provider, [symbol("demo")], lambda event: None)
    env.set_host("authority_fixture", authority, visibility="entry-only")
    return env


@pytest.mark.parametrize("name", ["authority_fixture", "[[authority_fixture]]"])
def test_authority_name_is_illegal_before_values(protected_env, name):
    with pytest.raises(TypeError, match="^sheet expected a legal column name: declassification authority cannot be a map key$"):
        run_source(f"with_column({name}, 0, s)", protected_env)


@pytest.mark.parametrize("value", [
    "authority_fixture",
    "[[authority_fixture]]",
    "{nested: authority_fixture}",
    "some(authority_fixture)",
])
def test_detected_authority_precedes_row_count(protected_env, value):
    with pytest.raises(TypeError, match="^declassification authority cannot be stored in a Sheet$"):
        run_source(f'with_column("new", [{value}, 2], s)', protected_env)


def test_exact_protected_transport_and_sinks(protected_env, capsys):
    env = protected_env
    run_source(
        'xs = column("old", s)\n'
        'out = map2((x, y) -> x, xs, [0])\n'
        't = with_column("new", out, s)',
        env,
    )
    seed, result = env.get("s"), env.get("t")
    token = env.get("token")
    assert seed.columns[0] is result.columns[0]
    assert env.get("xs") is not env.get("out")
    assert env.get("xs") is not run_source('column("old", s)', env)
    assert env.get("xs")[0] is env.get("out")[0] is result.columns[1][1][0] is token
    with pytest.raises(TypeError, match="protected-value") as sink:
        run_source("render_csv(t)", env)
    with pytest.raises(TypeError, match="^column could not find column$") as missing:
        run_source(f'column("{SENTINEL}", t)', env)
    captured = capsys.readouterr()
    assert "<protected>" in format_debug(env.get("out"))
    assert SENTINEL not in str(sink.value) + str(missing.value) + format_debug(env.get("out"))
    assert captured.out == captured.err == ""


def test_unpublished_closed_callable_is_checked_only_on_invocation():
    env = make_global_env([])
    env.set_host("pending_fixture", GeniaClosedFunction("pending_fixture"), visibility="entry-only")
    assert run_source("map2(pending_fixture, [], [])", env) == []
    with pytest.raises(RuntimeError, match="closed-function-not-yet-published"):
        run_source("map2(pending_fixture, [1], [2])", env)
