"""Runtime value representations for the Python reference host."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Iterator

from .errors import GeniaQuietBrokenPipe, format_exception_text


def _runtime_type_name(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, GeniaOptionNone):
        return "none"
    if isinstance(value, GeniaOptionSome):
        return f"some({_runtime_type_name(value.value)})"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, GeniaMap):
        return "map"
    if isinstance(value, GeniaFlow):
        return "flow"
    if isinstance(value, GeniaRng):
        return "rng"
    if isinstance(value, GeniaRef):
        return "ref"
    if isinstance(value, GeniaProcess):
        return "process"
    if isinstance(value, GeniaOutputSink):
        return "sink"
    if isinstance(value, GeniaBytes):
        return "bytes"
    if isinstance(value, GeniaZipEntry):
        return "zip_entry"
    if isinstance(value, GeniaPythonHandle):
        return "python_handle"
    if isinstance(value, GeniaPair):
        return "pair"
    if value.__class__.__name__ == "GeniaMetaEnv":
        return "meta_env"
    if value.__class__.__name__ == "GeniaPromise":
        return "promise"
    if value.__class__.__name__ == "GeniaFunctionGroup":
        return "function"
    if callable(value):
        return "function"
    return type(value).__name__


@dataclass(frozen=True)
class GeniaSymbol:
    name: str

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class GeniaPair:
    head: Any
    tail: Any

    def __repr__(self) -> str:
        return f"Pair({self.head!r}, {self.tail!r})"


_SYMBOL_INTERN_TABLE: dict[str, GeniaSymbol] = {}


def symbol(name: str) -> GeniaSymbol:
    existing = _SYMBOL_INTERN_TABLE.get(name)
    if existing is not None:
        return existing
    created = GeniaSymbol(name)
    _SYMBOL_INTERN_TABLE[name] = created
    return created


def _freeze_map_key(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, GeniaSymbol):
        return ("symbol", value.name)
    if isinstance(value, GeniaPair):
        return ("pair", _freeze_map_key(value.head), _freeze_map_key(value.tail))
    if isinstance(value, list):
        return ("list", tuple(_freeze_map_key(item) for item in value))
    if isinstance(value, tuple):
        return ("tuple", tuple(_freeze_map_key(item) for item in value))
    raise TypeError(f"map key type is not supported: {type(value).__name__}")


_MAP_GET_MISSING = object()


class GeniaMap:
    def __init__(self, entries: dict[Any, tuple[Any, Any]] | None = None):
        self._entries = {} if entries is None else entries

    def get(self, key: Any, default: Any = _MAP_GET_MISSING) -> Any:
        frozen_key = _freeze_map_key(key)
        entry = self._entries.get(frozen_key)
        if entry is None:
            if default is not _MAP_GET_MISSING:
                return default
            return make_none("missing-key", GeniaMap().put("key", key))
        return entry[1]

    def put(self, key: Any, value: Any) -> "GeniaMap":
        frozen_key = _freeze_map_key(key)
        next_entries = dict(self._entries)
        next_entries[frozen_key] = (key, value)
        return GeniaMap(next_entries)

    def has(self, key: Any) -> bool:
        frozen_key = _freeze_map_key(key)
        return frozen_key in self._entries

    def remove(self, key: Any) -> "GeniaMap":
        frozen_key = _freeze_map_key(key)
        if frozen_key not in self._entries:
            return self
        next_entries = dict(self._entries)
        del next_entries[frozen_key]
        return GeniaMap(next_entries)

    def count(self) -> int:
        return len(self._entries)

    def items(self) -> list[list[Any]]:
        return [[raw_key, raw_value] for raw_key, raw_value in self._entries.values()]

    def __repr__(self) -> str:
        return f"<map {len(self._entries)}>"


def _merge_metadata_maps(base: GeniaMap | None, override: GeniaMap | None) -> GeniaMap:
    result = base if base is not None else GeniaMap()
    if override is None:
        return result
    for key, value in override.items():
        result = result.put(key, value)
    return result


@dataclass(frozen=True)
class GeniaOptionNone:
    reason: Any = None
    context: Any = None

    @property
    def meta(self) -> "GeniaMap":
        metadata = GeniaMap().put("reason", self.reason)
        if self.context is not None:
            metadata = metadata.put("context", self.context)
        return metadata

    def __repr__(self) -> str:
        if self.reason is None:
            return 'none("nil")'
        if self.context is None:
            return f"none({self.reason!r})"
        return f"none({self.reason!r}, {self.context!r})"


def make_none(reason: Any = "nil", meta: Any = None) -> GeniaOptionNone:
    if reason is None:
        reason = "nil"
    if not isinstance(reason, str):
        raise TypeError(f"none reason expected string, received {_runtime_type_name(reason)}")
    if meta is not None and not isinstance(meta, GeniaMap):
        raise TypeError(f"none meta expected a map, received {_runtime_type_name(meta)}")
    return GeniaOptionNone(reason, meta)


def is_none(value: Any) -> bool:
    return isinstance(value, GeniaOptionNone)


def _is_nil_none(value: Any) -> bool:
    return is_none(value) and value.reason == "nil" and value.context is None


def _normalize_absence(value: Any) -> Any:
    if value is None:
        return OPTION_NONE
    return value


def _normalize_nil(value: Any) -> Any:
    return _normalize_absence(value)


OPTION_NONE = make_none("nil")
_RNG_MODULUS = 2**32
_RNG_MULTIPLIER = 1664525
_RNG_INCREMENT = 1013904223


@dataclass(frozen=True)
class GeniaOptionSome:
    value: Any

    def __repr__(self) -> str:
        return f"some({self.value!r})"


@dataclass(frozen=True)
class GeniaRng:
    state: int

    def __repr__(self) -> str:
        return "<rng>"


@dataclass(frozen=True)
class ModuleValue:
    name: str
    exports: dict[str, Any]
    path: str

    def get_export(self, export_name: str) -> Any:
        if export_name not in self.exports:
            raise NameError(f"Module {self.name} has no export named {export_name}")
        return self.exports[export_name]

    def __repr__(self) -> str:
        return f"<module {self.name}>"


@dataclass(frozen=True)
class GeniaPythonHandle:
    kind: str
    value: Any

    def __repr__(self) -> str:
        return f"<python {self.kind}>"


_UNSET = object()
_CELL_TX = threading.local()


def _cell_tx_stack() -> list[list[tuple[str, Any, Any]]]:
    stack = getattr(_CELL_TX, "stack", None)
    if stack is None:
        stack = []
        _CELL_TX.stack = stack
    return stack


def _push_cell_tx() -> list[tuple[str, Any, Any]]:
    actions: list[tuple[str, Any, Any]] = []
    _cell_tx_stack().append(actions)
    return actions


def _pop_cell_tx() -> list[tuple[str, Any, Any]]:
    stack = _cell_tx_stack()
    if not stack:
        return []
    actions = stack.pop()
    if not stack:
        try:
            delattr(_CELL_TX, "stack")
        except AttributeError:
            pass
    return actions


def _stage_cell_action(kind: str, first: Any, second: Any) -> bool:
    stack = getattr(_CELL_TX, "stack", None)
    if not stack:
        return False
    stack[-1].append((kind, first, second))
    return True


class GeniaRef:
    def __init__(self, initial: Any = _UNSET):
        self._condition = threading.Condition()
        self._value = initial
        self._is_set = initial is not _UNSET

    def get(self) -> Any:
        with self._condition:
            while not self._is_set:
                self._condition.wait()
            return self._value

    def set(self, value: Any) -> Any:
        with self._condition:
            self._value = value
            self._is_set = True
            self._condition.notify_all()
            return value

    def is_set(self) -> bool:
        with self._condition:
            return self._is_set

    def update(self, fn: Any) -> Any:
        with self._condition:
            while not self._is_set:
                self._condition.wait()
            self._value = fn(self._value)
            self._condition.notify_all()
            return self._value

    def __repr__(self) -> str:
        with self._condition:
            if self._is_set:
                return f"<ref {self._value!r}>"
            return "<ref <unset>>"


class GeniaCell:
    _STOP = object()

    def __init__(self, state_ref: GeniaRef):
        self._state_ref = state_ref
        self._condition = threading.Condition()
        self._failed = False
        self._stopped = False
        self._error: str | None = None
        self._generation = 0
        self._mailbox: queue.Queue[tuple[int, Any]] = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _error_text(self, exc: BaseException) -> str:
        return format_exception_text(exc)

    def _commit_actions(self, actions: list[tuple[str, Any, Any]]) -> None:
        for kind, first, second in actions:
            if kind == "cell_send":
                first.send(second)
                continue
            if kind == "process_send":
                first.send(second)
                continue
            if kind == "cell_stop":
                first._stopped = True
                first._mailbox.put((first._generation, GeniaCell._STOP))
                continue
            raise RuntimeError(f"Unknown cell action kind: {kind}")

    def _run(self) -> None:
        while True:
            generation, update_fn = self._mailbox.get()
            if update_fn is GeniaCell._STOP:
                return
            with self._condition:
                if generation != self._generation or self._failed:
                    continue

            try:
                _push_cell_tx()
                try:
                    current_state = self._state_ref.get()
                    next_state = update_fn(current_state)
                finally:
                    actions = _pop_cell_tx()

                with self._condition:
                    if generation != self._generation or self._failed:
                        continue
                    self._commit_actions(actions)
                    self._state_ref.set(next_state)
            except Exception as exc:
                with self._condition:
                    if generation != self._generation:
                        continue
                    self._failed = True
                    self._error = self._error_text(exc)
                    self._condition.notify_all()

    def send(self, update_fn: Any) -> None:
        with self._condition:
            if self._failed:
                raise RuntimeError(f"Cell has failed: {self._error}")
            if self._stopped:
                raise RuntimeError("Cell has been stopped")
            generation = self._generation
        self._mailbox.put((generation, update_fn))

    def get(self) -> Any:
        with self._condition:
            if self._failed:
                raise RuntimeError(f"Cell has failed: {self._error}")
        return self._state_ref.get()

    def failed(self) -> bool:
        with self._condition:
            return self._failed

    def error_option(self) -> Any:
        with self._condition:
            if self._failed and self._error is not None:
                return GeniaOptionSome(self._error)
            return OPTION_NONE

    def restart(self, value: Any) -> "GeniaCell":
        with self._condition:
            self._generation += 1
            self._failed = False
            self._stopped = False
            self._error = None
            self._state_ref.set(value)
            self._condition.notify_all()
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def stop(self) -> None:
        with self._condition:
            if self._stopped or self._failed:
                return
            self._stopped = True
            generation = self._generation
        self._mailbox.put((generation, GeniaCell._STOP))

    def stopped(self) -> bool:
        with self._condition:
            return self._stopped

    def status(self) -> str:
        with self._condition:
            if self._failed:
                return "failed"
            if self._stopped:
                return "stopped"
            return "ready"

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def __repr__(self) -> str:
        return f"<cell {self.status()}>"


class GeniaProcess:
    def __init__(self, handler: Callable[[Any], Any]):
        self._handler = handler
        self._mailbox: queue.Queue[Any] = queue.Queue()
        self._failed = False
        self._error: str | None = None
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _error_text(self, exc: BaseException) -> str:
        return format_exception_text(exc)

    def _run(self) -> None:
        while True:
            message = self._mailbox.get()
            try:
                self._handler(message)
            except Exception as exc:
                with self._lock:
                    self._failed = True
                    self._error = self._error_text(exc)
                return

    def send(self, message: Any) -> None:
        with self._lock:
            if self._failed:
                raise RuntimeError(f"Process has failed: {self._error}")
        self._mailbox.put(message)

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def failed(self) -> bool:
        with self._lock:
            return self._failed

    def error(self) -> str | None:
        with self._lock:
            return self._error

    def __repr__(self) -> str:
        with self._lock:
            if self._failed:
                return "<process failed>"
        status = "alive" if self.is_alive() else "dead"
        return f"<process {status}>"


class GeniaBytes:
    def __init__(self, value: bytes):
        self.value = value

    def __repr__(self) -> str:
        return f"<bytes {len(self.value)}>"


class GeniaZipEntry:
    def __init__(self, name: str, data: GeniaBytes):
        self.name = name
        self.data = data

    def __repr__(self) -> str:
        return f"<zip-entry {self.name!r} {len(self.data.value)}>"


class GeniaFlow:
    def __init__(
        self,
        iterator_factory: Callable[[], Iterable[Any]],
        *,
        label: str = "flow",
        close_on_early_termination: bool = True,
    ):
        self._iterator_factory = iterator_factory
        self._label = label
        self._consumed = False
        self._close_on_early_termination = close_on_early_termination

    def consume(self) -> Iterable[Any]:
        if self._consumed:
            raise RuntimeError("Flow has already been consumed")
        self._consumed = True
        produced = self._iterator_factory()
        try:
            return iter(produced)
        except TypeError:
            raise TypeError(f"Flow source {self._label} did not produce an iterable") from None

    def __repr__(self) -> str:
        state = "consumed" if self._consumed else "ready"
        return f"<flow {self._label} {state}>"

    @property
    def close_on_early_termination(self) -> bool:
        return self._close_on_early_termination


class GeniaOutputSink:
    def __init__(
        self,
        name: str,
        *,
        stream: Any | None = None,
        writer: Callable[[str], Any] | None = None,
        swallow_broken_pipe: bool = False,
    ):
        self.name = name
        self._stream = stream
        self._writer = writer
        self._swallow_broken_pipe = swallow_broken_pipe

    def write_text(self, text: str) -> None:
        try:
            if self._writer is not None:
                self._writer(text)
            elif self._stream is not None:
                self._stream.write(text)
            else:
                raise RuntimeError(f"{self.name} sink is not configured")
        except BrokenPipeError:
            if self._swallow_broken_pipe:
                return
            raise GeniaQuietBrokenPipe() from None

    def flush(self) -> None:
        try:
            if self._stream is not None and hasattr(self._stream, "flush"):
                self._stream.flush()
        except BrokenPipeError:
            if self._swallow_broken_pipe:
                return
            raise GeniaQuietBrokenPipe() from None

    def __repr__(self) -> str:
        return f"<{self.name}>"


class GeniaStdinSource:
    def __init__(self, iterator_factory: Callable[[], Iterable[str]]):
        self._iterator_factory = iterator_factory
        self._iterator: Iterator[str] | None = None
        self._cache: list[str] = []
        self._exhausted = False

    def _ensure_iterator(self) -> Iterator[str] | None:
        if self._exhausted:
            return None
        if self._iterator is None:
            self._iterator = iter(self._iterator_factory())
        return self._iterator

    def iter_lines(self) -> Iterable[str]:
        while True:
            iterator = self._ensure_iterator()
            if iterator is None:
                return
            try:
                item = next(iterator)
            except StopIteration:
                self._iterator = None
                self._exhausted = True
                return
            if not isinstance(item, str):
                raise TypeError("stdin expected string input items")
            normalized = item.rstrip("\r\n")
            self._cache.append(normalized)
            yield normalized

    def materialize(self) -> list[str]:
        if not self._exhausted:
            for _ in self.iter_lines():
                pass
        return list(self._cache)

    def __call__(self) -> list[str]:
        return self.materialize()

    def __repr__(self) -> str:
        state = "exhausted" if self._exhausted else "ready"
        return f"<stdin-source {state}>"
