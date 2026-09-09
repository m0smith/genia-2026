"""
E16-3 host capability advertisement and per-case requirements (issue #760).

Loads the capability-name vocabulary genia-2026 already owns
(``spec/manifest.json``'s ``required_capabilities``/``optional_capabilities``)
and implements the deterministic selection rule: a case with no ``requires``
belongs to the base required-capability set every conforming host implements
by definition and is always applicable; a case with ``requires`` is
applicable only when the host's ``capabilities`` response marks every listed
capability exactly ``supported``.

This module never declares a Python-host-only capability portable and never
requires identical capability sets across hosts -- it only decides, given
one host's claims, which selected cases are meaningful to run against it.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "spec" / "manifest.json"


class CapabilityDeclarationError(ValueError):
    """A host's capabilities response, or a spec case's ``requires`` list,
    named a capability genia-2026 does not define. Raised for a malformed
    or contradictory declaration; never silently ignored."""


def known_capabilities() -> frozenset[str]:
    """The full genia-2026-owned capability vocabulary: every name listed in
    ``spec/manifest.json``'s ``required_capabilities`` or
    ``optional_capabilities``."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return frozenset(manifest["required_capabilities"]) | frozenset(manifest["optional_capabilities"])


def validate_capability_claims(capabilities: dict[str, str]) -> None:
    """Reject a host capabilities declaration that claims a status for any
    name outside the known vocabulary. Shape correctness (status values,
    field types) is already enforced by ``protocol.validate_envelope``;
    this is the E16-3 vocabulary policy layered on top."""
    unknown = sorted(set(capabilities) - known_capabilities())
    if unknown:
        raise CapabilityDeclarationError(
            f"host declared unknown capabilities not defined by genia-2026: {unknown}"
        )


def validate_case_requirements(requires: tuple[str, ...]) -> None:
    """Reject a spec case whose ``requires`` list names a capability outside
    the known vocabulary."""
    unknown = sorted(set(requires) - known_capabilities())
    if unknown:
        raise CapabilityDeclarationError(
            f"spec case requires unknown capabilities not defined by genia-2026: {unknown}"
        )


def case_is_applicable(requires: tuple[str, ...], capabilities: dict[str, str]) -> tuple[bool, str | None]:
    """Return ``(applicable, reason_if_not)`` for one case against one
    host's declared capabilities.

    A case with an empty ``requires`` is always applicable. A case with
    ``requires`` is applicable only when every listed capability is
    declared exactly ``supported``; ``partial`` and undeclared capabilities
    do not satisfy ``requires`` in this phase (partial-capability
    satisfaction, if ever added, is a separate contract decision, not an
    E16-3 default).
    """
    if not requires:
        return True, None
    missing = [name for name in requires if capabilities.get(name) != "supported"]
    if missing:
        return False, f"host does not declare required capabilities as supported: {missing}"
    return True, None
