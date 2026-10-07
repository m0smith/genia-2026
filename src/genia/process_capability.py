"""Experimental opaque process-execution capability for `execution.process`.

Implements the internal capability/provider representation the approved
design (`docs/design/execution-process-design.md` §4) proposes for the
approved contract (`docs/design/execution-process-contract.md`). This
module has no Genia-visible surface of its own: `GeniaProcessCapability`
is not constructible, comparable, serializable, or meaningfully
renderable from Genia source, and the private factory below is consumed
only by privileged host-side code (currently: tests, via
`tests/fixtures/execution_process_helpers.py`). The contract's deferred
source-level bootstrap/provisioning operation is not implemented here.

The capability holds exactly three private pieces of state, mirroring the
existing `GeniaModelProvider` (`src/genia/model.py`) shape:

- a private symbol -> opaque native target mapping ("bindings"), shallow-copied
  by the host factory and treated as immutable by the execution boundary;
- an authorization predicate consulted only for a bound symbol, kept
  distinct from the bindings map so "unbound" and "bound but denied" stay
  observably different failure modes;
- a launcher callable that performs the actual host launch attempt.

None of this is exposed as portable semantics: a native target string
never crosses into a Genia value, diagnostic, or error context anywhere in
this module.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class GeniaProcessCapability:
    """Opaque Python-host process-execution capability."""

    __slots__ = ("_bindings", "_authorized", "_launcher")

    def __init__(
        self,
        bindings: dict[str, Any],
        authorized: Callable[[str], bool],
        launcher: Callable[[Any, list[str], int], Any],
    ):
        """Capture host-owned bindings and callbacks without validation or IO.

        Direct construction retains the mapping by reference; privileged callers
        should use `create_process_capability` for validation and a shallow copy.
        Targets and callbacks remain host-private, with no Genia mutation API.
        """

        self._bindings = bindings
        self._authorized = authorized
        self._launcher = launcher

    def is_bound(self, symbol_name: str) -> bool:
        """Test binding presence without consulting authorization or launching."""

        return symbol_name in self._bindings

    def is_authorized(self, symbol_name: str) -> bool:
        """Consult the host predicate and coerce its result to bool.

        The execution boundary calls this only after confirming a binding.
        This method neither checks presence nor catches predicate exceptions.
        """

        return bool(self._authorized(symbol_name))

    def target_for(self, symbol_name: str) -> Any:
        """Return the private target; require a bound symbol or raise KeyError.

        Authorization is the caller's responsibility, not part of this lookup.
        """

        return self._bindings[symbol_name]

    def launch(self, target: Any, args: list[str], timeout_ms: int) -> Any:
        """Invoke the host launcher once with the resolved target and exact args.

        The caller validates the request and authorizes resolution beforehand.
        Results and exceptions pass through; the execution boundary normalizes
        launcher failures rather than exposing native details to Genia.
        """

        return self._launcher(target, args, timeout_ms)

    def __repr__(self) -> str:
        """Render an opaque marker without targets or authorization details."""

        return "<process-capability>"


def create_process_capability(
    bindings: dict[str, Any],
    authorized: Callable[[str], bool],
    launcher: Callable[[Any, list[str], int], Any],
) -> GeniaProcessCapability:
    """Build a capability from a shallow bindings snapshot and host callbacks.

    Python-host only; no Genia source constructor or provisioning operation.
    Raise TypeError for a non-dict mapping or non-callable callback, without
    invoking either callback or launching. Target values are retained by
    identity; their validity and PATH-independent selection belong to the host
    provisioner. The snapshot is not exposed for mutation by Genia callers.
    """

    if not isinstance(bindings, dict):
        raise TypeError(
            f"process capability expected a bindings dict, received {type(bindings).__name__}"
        )
    if not callable(authorized):
        raise TypeError("process capability expected a callable authorization predicate")
    if not callable(launcher):
        raise TypeError("process capability expected a callable launcher")
    return GeniaProcessCapability(dict(bindings), authorized, launcher)
