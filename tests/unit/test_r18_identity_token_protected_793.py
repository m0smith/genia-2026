"""E18-3 (#793) focused evidence for identity, opaque-token, and protected equality.

The protected sections are adversarial: they assume the boundary leaks until
evidence shows otherwise. The decisive pattern throughout is to build one pair of
carriers with **equal** payloads and one pair with **different** payloads, then
require every observable to answer identically for both. An observable that can
tell the two pairs apart is a payload oracle, regardless of what it returns.

Sentinel strings follow the established pattern in
`tests/unit/test_protected_configuration.py`.

Issue contract: .genia/process/tmp/handoffs/e18-3-identity-token-protected/01-contract.md
"""

from __future__ import annotations

import json

import pytest

from genia.builtins import make_global_env
from genia.equality import genia_equal
from genia.interpreter import run_source
from genia.utf8 import format_debug, format_display
from genia.values import (
    GeniaCell,
    GeniaMap,
    GeniaNamedPattern,
    GeniaOptionErr,
    GeniaOptionSome,
    GeniaPair,
    GeniaProtected,
    GeniaPythonHandle,
    GeniaRef,
    GeniaSymbol,
    ModuleValue,
    symbol,
)


PAYLOAD_SENTINEL = "PAYLOAD_SENTINEL_793"
OTHER_SENTINEL = "OTHER_SENTINEL_793"


def make_carrier(payload: str, provider_identity: object | None = None) -> GeniaProtected:
    """Mint one protected carrier. Each call is an independent acquisition."""
    return GeniaProtected(
        payload,
        provider_identity if provider_identity is not None else object(),
        symbol("purpose"),
    )


# --------------------------------------------------------------------------
# protected: carrier identity only
# --------------------------------------------------------------------------


def test_carrier_equals_itself_and_its_alias() -> None:
    carrier = make_carrier(PAYLOAD_SENTINEL)
    alias = carrier
    assert genia_equal(carrier, carrier) is True
    assert genia_equal(carrier, alias) is True


def test_independently_acquired_carriers_with_equal_payloads_are_unequal() -> None:
    """The core security requirement of this slice."""
    shared_provider = object()
    left = make_carrier(PAYLOAD_SENTINEL, shared_provider)
    right = make_carrier(PAYLOAD_SENTINEL, shared_provider)
    assert genia_equal(left, right) is False
    assert genia_equal(right, left) is False


def test_carrier_is_not_equal_to_its_payload_or_other_kinds() -> None:
    carrier = make_carrier(PAYLOAD_SENTINEL)
    assert genia_equal(carrier, PAYLOAD_SENTINEL) is False
    assert genia_equal(PAYLOAD_SENTINEL, carrier) is False
    assert genia_equal(carrier, 1) is False
    assert genia_equal(carrier, [PAYLOAD_SENTINEL]) is False


def test_host_equality_on_the_carrier_type_is_not_a_payload_oracle() -> None:
    """Defence in depth: the guarantee must belong to the type, not to callers.

    Any internal host comparison — assertions, deduplication, membership,
    an accidental `==` — would otherwise reopen the oracle.
    """
    shared_provider = object()
    left = make_carrier(PAYLOAD_SENTINEL, shared_provider)
    right = make_carrier(PAYLOAD_SENTINEL, shared_provider)
    different = make_carrier(OTHER_SENTINEL, shared_provider)

    assert (left == right) is False
    assert (left == different) is False
    assert (left == left) is True
    # equal-payload and different-payload pairs must be indistinguishable
    assert (left == right) == (left == different)


def test_carriers_remain_unhashable_so_host_containers_cannot_become_oracles() -> None:
    carrier = make_carrier(PAYLOAD_SENTINEL)
    with pytest.raises(TypeError):
        hash(carrier)
    with pytest.raises(TypeError):
        {carrier}


# --------------------------------------------------------------------------
# protected: non-interference across every observable
# --------------------------------------------------------------------------


def equal_and_different_pairs() -> tuple[tuple[GeniaProtected, GeniaProtected], tuple[GeniaProtected, GeniaProtected]]:
    provider = object()
    equal_pair = (
        make_carrier(PAYLOAD_SENTINEL, provider),
        make_carrier(PAYLOAD_SENTINEL, provider),
    )
    different_pair = (
        make_carrier(PAYLOAD_SENTINEL, provider),
        make_carrier(OTHER_SENTINEL, provider),
    )
    return equal_pair, different_pair


WRAPPERS = [
    ("bare", lambda c: c),
    ("list", lambda c: [c]),
    ("nested-list", lambda c: [[c]]),
    ("pair-head", lambda c: GeniaPair(c, 1)),
    ("pair-tail", lambda c: GeniaPair(1, c)),
    ("some", lambda c: GeniaOptionSome(c)),
    ("some-context", lambda c: GeniaOptionSome(1, c)),
    ("err-context", lambda c: GeniaOptionErr("e", c)),
    ("map-value", lambda c: GeniaMap().put("k", c)),
    ("deep", lambda c: GeniaOptionSome([GeniaMap().put("k", [c])])),
]


@pytest.mark.parametrize("label,wrap", WRAPPERS, ids=[w[0] for w in WRAPPERS])
def test_equality_cannot_distinguish_equal_from_different_payloads(
    label: str, wrap: object
) -> None:
    (eq_left, eq_right), (diff_left, diff_right) = equal_and_different_pairs()

    equal_payload_result = genia_equal(wrap(eq_left), wrap(eq_right))
    different_payload_result = genia_equal(wrap(diff_left), wrap(diff_right))

    assert equal_payload_result == different_payload_result, (
        f"{label}: equality distinguishes equal payloads from different ones, "
        "which is a protected-payload oracle"
    )
    assert equal_payload_result is False


@pytest.mark.parametrize("label,wrap", WRAPPERS, ids=[w[0] for w in WRAPPERS])
def test_inequality_cannot_distinguish_equal_from_different_payloads(
    label: str, wrap: object
) -> None:
    (eq_left, eq_right), (diff_left, diff_right) = equal_and_different_pairs()
    assert (not genia_equal(wrap(eq_left), wrap(eq_right))) == (
        not genia_equal(wrap(diff_left), wrap(diff_right))
    )


@pytest.mark.parametrize("label,wrap", WRAPPERS, ids=[w[0] for w in WRAPPERS])
def test_carrier_identity_is_still_observable_through_wrappers(
    label: str, wrap: object
) -> None:
    """Revealing carrier identity is permitted; revealing payload equality is not."""
    carrier = make_carrier(PAYLOAD_SENTINEL)
    assert genia_equal(wrap(carrier), wrap(carrier)) is True


def test_rendering_never_discloses_a_payload() -> None:
    carrier = make_carrier(PAYLOAD_SENTINEL)
    for wrapped in (wrap(carrier) for _, wrap in WRAPPERS):
        for rendered in (format_display(wrapped), format_debug(wrapped)):
            assert PAYLOAD_SENTINEL not in rendered


def test_map_key_rejection_never_discloses_a_payload() -> None:
    carrier = make_carrier(PAYLOAD_SENTINEL)
    with pytest.raises(TypeError) as excinfo:
        GeniaMap().put(carrier, 1)
    assert PAYLOAD_SENTINEL not in str(excinfo.value)


def test_equality_never_declassifies() -> None:
    """Comparing carriers must not consult any declassification authority."""
    audits: list[object] = []

    class SpyAuthority:  # pragma: no cover - must never be used
        def _allows(self, *args: object) -> bool:
            audits.append(args)
            return True

        def _audit(self, *args: object) -> None:
            audits.append(args)

    (eq_left, eq_right), _ = equal_and_different_pairs()
    genia_equal(eq_left, eq_right)
    genia_equal([eq_left], [eq_right])
    assert audits == []


def test_protected_oracle_is_closed_from_ordinary_source() -> None:
    """End-to-end: the oracle measured before R18 must be gone from real source."""
    source = (
        'provider = config_provider([{kind: quote(values), values: '
        f'{{A: "{PAYLOAD_SENTINEL}", B: "{PAYLOAD_SENTINEL}", C: "{OTHER_SENTINEL}"}}}}]) '
        "|> unwrap_or(none)\n"
        'a = secret_get(provider, "A", quote(use))\n'
        'b = secret_get(provider, "B", quote(use))\n'
        'c = secret_get(provider, "C", quote(use))\n'
        "[a == a, a == b, a == c, [a] == [b], [a] == [c]]\n"
    )
    result = run_source(source, make_global_env([]))
    assert result == [True, False, False, False, False]


# --------------------------------------------------------------------------
# identity-bearing values
# --------------------------------------------------------------------------


def test_refs_and_cells_compare_by_identity_not_contents() -> None:
    ref = GeniaRef([1, 2])
    assert genia_equal(ref, ref) is True
    assert genia_equal(ref, GeniaRef([1, 2])) is False
    assert genia_equal(ref, [1, 2]) is False

    cell = GeniaCell(1)
    assert genia_equal(cell, cell) is True
    assert genia_equal(cell, GeniaCell(1)) is False


def test_modules_compare_by_identity_and_exports_are_never_compared() -> None:
    """`ModuleValue` is a host dataclass whose generated equality compares its
    whole export table. Identity must override that."""
    exports = {"f": lambda: None}
    left = ModuleValue("m", exports, "/tmp/m.genia")
    right = ModuleValue("m", exports, "/tmp/m.genia")
    assert genia_equal(left, left) is True
    assert genia_equal(left, right) is False


def test_python_handles_compare_by_identity() -> None:
    left = GeniaPythonHandle("kind", [1, 2])
    right = GeniaPythonHandle("kind", [1, 2])
    assert genia_equal(left, left) is True
    assert genia_equal(left, right) is False


def test_named_patterns_compare_by_identity_and_are_never_invoked() -> None:
    calls: list[object] = []

    def matcher(*args: object) -> object:  # pragma: no cover - must not be called
        calls.append(args)
        return GeniaOptionSome(1)

    left = GeniaNamedPattern("p", matcher)
    right = GeniaNamedPattern("p", matcher)
    assert genia_equal(left, left) is True
    assert genia_equal(left, right) is False
    assert calls == [], "comparing matcher values must never invoke them"


def test_callables_compare_by_identity() -> None:
    def f() -> None:
        return None

    def g() -> None:
        return None

    assert genia_equal(f, f) is True
    assert genia_equal(f, g) is False


def test_identity_values_are_terminal_inside_structural_values() -> None:
    ref = GeniaRef([1])
    other = GeniaRef([1])
    assert genia_equal([ref], [ref]) is True
    assert genia_equal([ref], [other]) is False
    assert genia_equal(GeniaMap().put("k", ref), GeniaMap().put("k", ref)) is True
    assert genia_equal(GeniaMap().put("k", ref), GeniaMap().put("k", other)) is False


# --------------------------------------------------------------------------
# opaque semantic tokens
# --------------------------------------------------------------------------
#
# R18 exposes no way to mint or observe a token from Genia source. This fixture
# is test-only and must never become source-visible language behavior; it exists
# to prove the equality engine's adapter shape works, so a future built-in or
# user-defined token domain can participate without registering comparator code.


class TokenFixture:
    """A token supplies three immutable identities as DATA, never a comparator."""

    __slots__ = ("__identity",)

    def __init__(self, domain: object, provenance: object, semantic: object):
        self.__identity = (domain, provenance, semantic)

    @property
    def __genia_token_equality__(self) -> tuple[object, object, object]:
        return self.__identity

    def __repr__(self) -> str:
        return "<token>"


class HostileTokenFixture(TokenFixture):
    """A token that also offers a comparator. The engine must ignore it."""

    def __eq__(self, other: object) -> bool:  # pragma: no cover - must not be used
        return True

    __hash__ = None  # type: ignore[assignment]


def test_tokens_are_equal_when_all_three_identities_are_equal() -> None:
    left = TokenFixture("domain", "issuer", "fact")
    right = TokenFixture("domain", "issuer", "fact")
    assert genia_equal(left, right) is True
    assert genia_equal(right, left) is True
    assert genia_equal(left, left) is True


@pytest.mark.parametrize(
    "other",
    [
        TokenFixture("OTHER", "issuer", "fact"),
        TokenFixture("domain", "OTHER", "fact"),
        TokenFixture("domain", "issuer", "OTHER"),
    ],
    ids=["domain", "provenance", "semantic"],
)
def test_tokens_differing_in_any_identity_are_unequal(other: TokenFixture) -> None:
    base = TokenFixture("domain", "issuer", "fact")
    assert genia_equal(base, other) is False
    assert genia_equal(other, base) is False


def test_tokens_are_never_equal_to_other_kinds() -> None:
    token = TokenFixture("domain", "issuer", "fact")
    assert genia_equal(token, "fact") is False
    assert genia_equal(token, 1) is False
    assert genia_equal(token, ["domain", "issuer", "fact"]) is False
    assert genia_equal("fact", token) is False


def test_token_identity_components_compare_with_the_canonical_relation() -> None:
    """Components are compared portably, not by host equality."""
    assert genia_equal(
        TokenFixture("d", "i", 1), TokenFixture("d", "i", 1.0)
    ) is True, "the exact int/float bridge applies inside a token identity"
    assert genia_equal(
        TokenFixture("d", "i", True), TokenFixture("d", "i", 1)
    ) is False, "boolean/number separation applies inside a token identity"


def test_a_token_supplied_comparator_is_never_used() -> None:
    """Equality is not overloadable: a token supplies data, never behavior."""
    left = HostileTokenFixture("domain", "issuer", "fact")
    right = HostileTokenFixture("domain", "issuer", "DIFFERENT")
    assert genia_equal(left, right) is False, (
        "the engine used the token's own comparator, which would make == overloadable"
    )


def test_tokens_are_terminal_inside_structural_values() -> None:
    left = TokenFixture("d", "i", "fact")
    right = TokenFixture("d", "i", "fact")
    assert genia_equal([left], [right]) is True
    assert genia_equal(GeniaOptionSome(left), GeniaOptionSome(right)) is True
    assert genia_equal([left], [TokenFixture("d", "i", "other")]) is False


def test_tokens_are_not_legal_map_keys() -> None:
    from genia.equality import canonical_map_key

    with pytest.raises(TypeError):
        canonical_map_key(TokenFixture("d", "i", "fact"))


def test_token_comparison_contacts_no_issuer() -> None:
    contacts: list[object] = []

    class SpyIssuer:
        def __call__(self, *args: object) -> object:  # pragma: no cover
            contacts.append(args)
            return None

    issuer = SpyIssuer()
    left = TokenFixture("d", issuer, "fact")
    right = TokenFixture("d", issuer, "fact")
    assert genia_equal(left, right) is True
    assert contacts == []


# --------------------------------------------------------------------------
# no transitional scaffold remains
# --------------------------------------------------------------------------


def test_the_relation_has_no_transitional_branch_left() -> None:
    """After E18-3 every family is classified; no host-equality delegation remains."""
    import genia.equality as equality_module

    for leftover in ("_deferred_equal", "_is_deferred"):
        assert not hasattr(equality_module, leftover), (
            f"{leftover} is a transitional E18-1 scaffold that E18-3 must remove"
        )
