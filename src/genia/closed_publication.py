"""Private closed-callable lineage and transactions; no evaluator activation.

Only a declaration owner may open its transaction window. Synchronous bridges
inherit the current thread's lineage; independent host dispatchers cut it with a
barrier. Context copies carry no authority. This is not a Python security boundary.
"""
from contextlib import contextmanager
from dataclasses import dataclass, field
import threading
from typing import TYPE_CHECKING, Any, Callable, Iterator

if TYPE_CHECKING:
    from .callable import GeniaClosedFunction
    from .environment import Env
    from .values import GeniaMap


_LINEAGE = threading.local()
_BARRIER = object()


@dataclass(eq=False)
class _PublicationTransaction:
    """Stable callable descriptor, attached once while building and never removed.

    Window exit revokes window_open only; terminal transaction cleanup writes
    closed. The two owning scopes belong to the callable's reserved self frame
    and its direct parent. The descriptor remains attached after either outcome.
    """
    callable: Any
    window_open: bool = False
    closed: bool = False
    declaring_scope: Any = field(init=False, default=None)
    self_frame: Any = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Attach to an unreachable building callable; reject replacement descriptors."""
        if self.callable._state != 'building' or hasattr(self.callable, '_txn'):
            raise RuntimeError('publication descriptor requires a fresh building callable')
        self.self_frame = getattr(self.callable, "_self_frame", None)
        self.declaring_scope = self.self_frame.parent if self.self_frame is not None else None
        self.callable._txn = self


def _stage_immutable_names(scope: "Env", name: str) -> frozenset[str]:
    """Allocate the current immutable-name set plus name without publishing it.

    The private caller holds the T6 binding lock and has not reached C3. This
    named C2b allocation exposes before/after faults without intercepting C4.
    """
    return scope._immutable | {name}


def _run_publication(
    txn: _PublicationTransaction,
    evaluate_annotations: Callable[["Env"], "GeniaMap"],
) -> "GeniaClosedFunction":
    """Publish a prepared private group, or fail it without rolling back effects.

    Caller owns T0–T3 validation/construction and supplies a fresh building txn.
    This driver owns T4–T7. Its callback evaluates/folds annotations in the self
    frame inside the admission window, outside the binding lock, returning a
    private GeniaMap. Success returns the same committed callable. BaseException
    exits before commitment fail/discard and release only this owner's slots;
    exits after commitment finish both tables and cleanup under the same lock
    before re-raising unchanged. Recovery covers single faults within an acquired
    lock, not progress under persistent failures. Interrupting failure-lock
    acquisition can strand a provisional transaction. Source evaluation is unwired.
    """
    # Runtime imports are lazy: environment/callable already depend on lineage.
    from . import environment as env

    group, scope, frame = txn.callable, txn.declaring_scope, txn.self_frame
    name = group.name
    if (txn.closed or txn.window_open or group._state != 'building'
            or group._txn is not txn or frame is None or scope is None
            or frame.parent is not scope):
        raise RuntimeError('publication requires a fresh building transaction and owning scopes')

    def close() -> None:
        """Repeat ownership-conditional K1–K4 under the caller-held lock."""
        while not txn.closed:
            try:
                scope._remove_provisional_slot(name, txn)
                frame._remove_provisional_slot(name, txn)
                env._unregister_open_transaction(txn)
                txn.closed = True
            except BaseException:
                # Each step is its own progress record. Never clear other owners.
                continue

    def install_committed() -> None:
        """Finish C4/C5 from already staged data; caller retains the T6 lock."""
        scope.binding_metadata[name] = metadata
        scope._immutable = immutable_names
        scope.values[name] = group
        frame.binding_metadata[name] = metadata
        frame.values[name] = group

    try:
        with env._BINDING_LOCK:
            scope._check_declaration(name)  # P1 repeats the caller's name check.
            env._register_open_transaction(txn)
            group._state = 'initializing'
            scope._install_provisional_slot(name, txn, strict=False)
            frame._install_provisional_slot(name, txn, strict=True)
        with _publication_window(txn):
            metadata = evaluate_annotations(frame)
        with env._BINDING_LOCK:
            try:
                slot = (scope._provisional_slots or {}).get(name)
                if slot is None or slot.transaction is not txn or name in scope.values:
                    raise env.ImmutableBindingError(f'Cannot rebind immutable binding: {name}')
                group.metadata = metadata
                # C2b is local, reads current shared state under this same lock,
                # and may allocate. It precedes the single C3 linearization store.
                immutable_names = _stage_immutable_names(scope, name)
                if group._state == 'initializing':
                    group._state = 'committed'
                install_committed()
                close()
            except BaseException:
                if group._state == 'committed':
                    # C3 may have taken effect before its interrupted store
                    # returned. Nothing after it can fail/roll back the callable.
                    while True:
                        try:
                            install_committed()
                            close()
                            break
                        except BaseException:
                            continue
                raise
    except BaseException:
        with env._BINDING_LOCK:
            if group._state != 'committed':
                while True:
                    try:
                        if group._state == 'initializing':
                            group._state = 'failed'
                        if group._state == 'failed':
                            frame.values[name] = group
                        # Building groups were never reachable: discard them.
                        close()
                        break
                    except BaseException:
                        continue
        raise
    return group


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
