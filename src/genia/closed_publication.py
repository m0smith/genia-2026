"""Private closed-callable admission lineage; no evaluator/publication activation.

Only a declaration owner may open its transaction window. Synchronous bridges
inherit the current thread's lineage; independent host dispatchers cut it with a
barrier. Context copies carry no authority. This is not a Python security boundary.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import threading
from typing import Any, Iterator


_LINEAGE = threading.local()
_BARRIER = object()


@dataclass(eq=False)
class _PublicationTransaction:
    """Stable callable descriptor, attached once while building and never removed.

    Window/closed flags are owner-written host state. Scope/slot/publication
    ownership is deliberately absent until the later publication slice.
    """
    callable: Any
    window_open: bool = False
    closed: bool = False

    def __post_init__(self) -> None:
        """Attach to an unreachable building callable; reject replacement descriptors."""
        if self.callable._state != 'building' or hasattr(self.callable, '_txn'):
            raise RuntimeError('publication descriptor requires a fresh building callable')
        self.callable._txn = self


def _lineage_stack() -> list[Any]:
    """Return this thread's private stack, allocating only on its first use."""
    stack = getattr(_LINEAGE, 'stack', None)
    if stack is None:
        stack = _LINEAGE.stack = []
    return stack


@contextmanager
def _publication_window(txn: _PublicationTransaction) -> Iterator[None]:
    """Open owner invocation admission, revoking it on every exit including interrupts.

    Private callers must not share ownership or reopen a closed transaction.
    Nested distinct transactions retain their own identities and windows.
    """
    if txn.closed or txn.window_open:
        raise RuntimeError('publication window is already open or closed')
    stack = _lineage_stack()
    txn.window_open = True
    try:
        stack.append(txn)
        try:
            yield
        finally:
            stack.pop()
    finally:
        txn.window_open = False


@contextmanager
def _publication_barrier() -> Iterator[None]:
    """Hide inherited admission for an independent host dispatch, restoring on unwind."""
    stack = _lineage_stack()
    stack.append(_BARRIER)
    try:
        yield
    finally:
        stack.pop()


def _publication_admitted(txn: _PublicationTransaction | None) -> bool:
    """Check local identity above the latest barrier before reading the owner flag.

    An E1 fixture without a descriptor remains fail-closed. No foreign thread
    reads window_open: only a stack containing the exact descriptor reaches it.
    """
    if txn is None:
        return False
    for entry in reversed(getattr(_LINEAGE, 'stack', ())):
        if entry is _BARRIER:
            return False
        if entry is txn:
            return txn.window_open
    return False
