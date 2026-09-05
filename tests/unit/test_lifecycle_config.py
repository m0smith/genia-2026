"""Focused tests for the R14 E14-4 ``lifecycle_config`` builtin (issue #694):
composition with real R10/R13 provider/view machinery, proving a
lifecycle-bound provider behaves identically to one threaded by hand, per
docs/design/r14-composable-lifecycle-contract.md's "Lifecycle-owned
configuration binding" section.

These tests exercise ``lifecycle_config`` through real Genia source via
``run_source``, since they need the full ``config_provider``/`config_view`/
``secret_view``/protected-value machinery, not just the trivial injected
invoker ``tests/unit/test_lifecycle_runtime.py`` uses for peer-shape and
non-shadowing-composition proofs.
"""

from __future__ import annotations

import pytest

import genia.configuration as configuration
from genia.builtins import make_global_env
from genia.interpreter import run_source
from genia.utf8 import format_debug, format_display
from genia.values import GeniaConfigProvider, GeniaOptionSome, GeniaProtected, GeniaSymbol


def _run(source: str, env=None):
    return run_source(source, env if env is not None else make_global_env([]))


def test_lifecycle_config_view_matches_hand_threaded_provider():
    src = """
    provider = config_provider([{kind: quote(values), values: {SERVER_PORT: "8080"}}]) |> unwrap_or(none)
    peer = lifecycle_config(provider)
    lifecycle_scope([peer], (root) -> {
      bound = unwrap_or(none, lifecycle_context(root, quote(config)))
      config_view(bound, "SERVER_")("PORT")
    }).result
    """
    value = _run(src)

    assert value == GeniaOptionSome(GeniaOptionSome("8080"))


def test_lifecycle_config_secret_view_matches_hand_threaded_provider_and_redacts():
    provider = GeniaConfigProvider(({"OPENAI_TOKEN": "payload"},))
    env = make_global_env([])
    env.set("provider", provider)
    src = """
    peer = lifecycle_config(provider)
    lifecycle_scope([peer], (root) -> {
      bound = unwrap_or(none, lifecycle_context(root, quote(config)))
      secret_view(bound, "OPENAI_", quote(model_call))("TOKEN")
    }).result
    """
    value = _run(src, env)

    assert isinstance(value, GeniaOptionSome)
    inner = value.value
    assert isinstance(inner, GeniaOptionSome)
    protected = inner.value
    assert isinstance(protected, GeniaProtected)

    direct = configuration.get_secret_configuration(
        provider, "OPENAI_TOKEN", GeniaSymbol("model_call")
    )
    assert protected == direct.value

    assert format_display(protected) == "<protected>"
    assert format_debug(protected) == "<protected>"


def test_lifecycle_config_minimal_end_to_end_through_child_scope():
    src = """
    provider = config_provider([{kind: quote(values), values: {APP_PORT: "9090"}}]) |> unwrap_or(none)
    config_peer = lifecycle_config(provider)
    lifecycle_scope([config_peer], (root) -> {
      child_result = lifecycle_child(root, [], (req) -> {
        bound = unwrap_or(none, lifecycle_context(req, quote(config)))
        config_view(bound, "APP_")("PORT")
      })
      child_result.result
    }).result
    """
    value = _run(src)

    assert value == GeniaOptionSome(GeniaOptionSome(GeniaOptionSome("9090")))


def test_lifecycle_config_rejects_an_unwrapped_option_result():
    src = """
    wrapped = config_provider([{kind: quote(values), values: {A: "1"}}])
    lifecycle_config(wrapped)
    """

    with pytest.raises(TypeError):
        _run(src)
