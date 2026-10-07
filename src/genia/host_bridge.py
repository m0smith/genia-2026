"""Python host interop bridge and stdlib/module loading helpers.

Issue #217: Groups 1 and 2 extracted from the main runtime module.
Contains module loading helpers and Python host interop bridge.
"""
from __future__ import annotations

import io
import json
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Any, Callable

if __package__ in (None, ""):
    import sys
    _src_root = Path(__file__).resolve().parents[1]
    if str(_src_root) not in sys.path:
        sys.path.insert(0, str(_src_root))
    from genia.values import (
        OPTION_NONE,
        _normalize_absence,
        _runtime_type_name,
        GeniaMap,
        GeniaOptionSome,
        GeniaPythonHandle,
        GeniaSymbol,
        ModuleValue,
        is_none,
    )
    from genia.configuration import reject_declassification_authority, reject_protected
else:
    from .values import (
        OPTION_NONE,
        _normalize_absence,
        _runtime_type_name,
        GeniaMap,
        GeniaOptionSome,
        GeniaPythonHandle,
        GeniaSymbol,
        ModuleValue,
        is_none,
    )
    from .configuration import reject_declassification_authority, reject_protected

# ---------------------------------------------------------------------------
# Group 1: module loading helpers
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()


def _stdlib_resource(relative_path: str):
    """Resolve an existing packaged stdlib file without falling back to disk.

    Only path strings beginning with ``std/`` are considered. Return the
    importlib resource handle when it names a file, or None when the prefix is
    absent, the genia package is unavailable, or no packaged file exists.
    """
    if not relative_path.startswith("std/"):
        return None
    try:
        resource = importlib_resources.files("genia").joinpath(relative_path)
    except ModuleNotFoundError:
        return None
    return resource if resource.is_file() else None


def _load_source_from_path(path: str) -> tuple[str, str]:
    """Read UTF-8 Genia source and return it with its resolved load identity.

    Packaged std/ resources take precedence. An absolute filesystem path is
    tried directly; a relative path is tried below BASE_DIR before the current
    working directory. The function reads the first matching file without
    caching it. If no candidate is a file it raises FileNotFoundError(path);
    decoding and other read failures propagate.
    """
    resource = _stdlib_resource(path)
    if resource is not None:
        source = resource.read_text(encoding="utf-8")
        with importlib_resources.as_file(resource) as resolved_resource_path:
            return source, str(resolved_resource_path)

    file_path = Path(path)
    candidates: list[Path] = []
    if file_path.is_absolute():
        candidates.append(file_path)
    else:
        candidates.append((BASE_DIR / path).resolve())
        candidates.append(file_path.resolve())
    for candidate in candidates:
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8"), str(candidate.resolve())
    raise FileNotFoundError(path)


def _resolve_packaged_module(module_name: str) -> tuple[str, str] | None:
    """Load one packaged prelude module by name, without filesystem fallback.

    Return its UTF-8 source and resolved resource path, or None when
    std/prelude/<module_name>.genia is not a packaged file. Read and decode
    failures propagate.
    """
    resource = _stdlib_resource(f"std/prelude/{module_name}.genia")
    if resource is None:
        return None
    source = resource.read_text(encoding="utf-8")
    with importlib_resources.as_file(resource) as resolved_resource_path:
        return source, str(resolved_resource_path)


# ---------------------------------------------------------------------------
# Group 2: Python host interop bridge
# ---------------------------------------------------------------------------


def _genia_map_to_host_dict(value: GeniaMap) -> dict[Any, Any]:
    """Copy a Genia map into a recursively converted Python dict.

    Keys use the narrower host-key conversion and values use the ordinary host
    conversion, so an unsupported or protected nested value raises before a
    result is returned. If distinct Genia keys convert to the same Python key,
    the later entry wins. The source map and its nested containers are not mutated.
    """
    result: dict[Any, Any] = {}
    for _, (raw_key, raw_value) in value._entries.items():
        host_key = _genia_map_key_to_host(raw_key)
        result[host_key] = _genia_to_python_host(raw_value)
    return result


def _genia_map_key_to_host(value: Any) -> Any:
    """Convert a supported Genia map key into a hashable Python key.

    None, booleans, primitive numbers, and strings pass through; symbols become
    their name strings, and list/tuple keys become recursively converted
    tuples. Other runtime values raise TypeError rather than becoming opaque
    handles.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, GeniaSymbol):
        return value.name
    if isinstance(value, list):
        return tuple(_genia_map_key_to_host(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_genia_map_key_to_host(item) for item in value)
    raise TypeError(f"python interop cannot convert map key type {_runtime_type_name(value)}")


def _genia_to_python_host(value: Any) -> Any:
    """Convert an ordinary Genia value for an allowlisted Python host call.

    Protected values and declassification authorities are rejected recursively
    before conversion. Supported Python-backed scalars pass through; structured
    absence becomes None, and some contributes only its payload (its context is
    not sent to Python). Lists and maps are copied recursively, while an opaque
    Python handle yields its borrowed host object. Unsupported runtime values
    raise TypeError. This is a Python reference-host boundary, not a portable
    conversion protocol.
    """
    reject_declassification_authority(value, "host-call")
    reject_protected(value, "host-call")
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if is_none(value):
        return None
    if isinstance(value, GeniaOptionSome):
        return _genia_to_python_host(value.value)
    if isinstance(value, list):
        return [_genia_to_python_host(item) for item in value]
    if isinstance(value, GeniaMap):
        return _genia_map_to_host_dict(value)
    if isinstance(value, GeniaPythonHandle):
        return value.value
    raise TypeError(f"python interop cannot convert {_runtime_type_name(value)} to a host value")


def _python_host_to_genia(value: Any) -> Any:
    """Convert an allowlisted Python result into a Genia runtime value.

    None becomes the canonical none("nil") value. Scalars pass through, lists
    and tuples become new Genia lists, and dictionaries become new Genia maps
    through the host-key conversion. Existing GeniaPythonHandle values retain
    identity; every other Python object is borrowed through a new opaque handle
    named from its lowercase type. The bridge does not take ownership of that
    underlying object.
    """
    if value is None:
        return OPTION_NONE
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [_python_host_to_genia(item) for item in value]
    if isinstance(value, tuple):
        return [_python_host_to_genia(item) for item in value]
    if isinstance(value, dict):
        result = GeniaMap()
        for raw_key, raw_value in value.items():
            key = _python_host_map_key_to_genia(raw_key)
            result = result.put(key, _python_host_to_genia(raw_value))
        return result
    if isinstance(value, GeniaPythonHandle):
        return value
    return GeniaPythonHandle(type(value).__name__.lower(), value)


def _python_host_map_key_to_genia(value: Any) -> Any:
    """Convert a Python dictionary key into a supported Genia map key.

    None and scalar keys pass through; tuple keys become recursively converted
    Genia lists. Mutable lists and arbitrary host objects are rejected with
    TypeError.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, tuple):
        return [_python_host_map_key_to_genia(item) for item in value]
    raise TypeError(f"python interop cannot convert host map key type {type(value).__name__}")


def _wrap_python_host_callable(
    module_name: str,
    export_name: str,
    fn: Callable[..., Any],
) -> Callable[..., Any]:
    """Adapt a positional Python callable to the Genia host-value boundary.

    Each argument is converted before fn is invoked, so protected,
    authority-bearing, or unsupported inputs produce no host-call side effect.
    The return value is converted recursively and a Python None result becomes
    canonical Genia absence. During input conversion and invocation, the
    enumerated host/validation exceptions propagate unchanged and another
    Exception is wrapped in RuntimeError with the supplied module/export name.
    Result-conversion errors propagate directly; BaseException is never caught.
    """
    def wrapped(*args: Any) -> Any:
        """Convert arguments, invoke the host function once, and convert its result."""
        try:
            host_args = [_genia_to_python_host(arg) for arg in args]
            result = fn(*host_args)
        except (TypeError, ValueError, FileNotFoundError, OSError, PermissionError, RuntimeError):
            raise
        except Exception as exc:  # pragma: no cover - defensive bridge fallback
            raise RuntimeError(f"{module_name}/{export_name} raised {type(exc).__name__}: {exc}") from exc
        return _normalize_absence(_python_host_to_genia(result))

    return wrapped


def _mark_handles_none(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Mark fn as explicitly none-aware and return the same callable.

    The evaluator consults the mutable marker to bypass automatic pipeline
    absence short-circuiting for this callable.
    """
    setattr(fn, "__genia_handles_none__", True)
    return fn


def _mark_handles_some(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Mark fn as explicitly some-aware and return the same callable.

    The evaluator consults the mutable marker to pass the complete some value
    instead of automatically lifting the callable over its payload.
    """
    setattr(fn, "__genia_handles_some__", True)
    return fn


_SAFE_PYTHON_OPEN_MODES = frozenset({"r", "w", "a"})


def _python_open_impl(path: Any, mode: Any = "r") -> Any:
    """Open a UTF-8 text file and return an opaque, caller-owned host handle.

    path and mode must be strings, and the only modes are exactly r, w, and a.
    The caller must close the returned handle explicitly through python.close.
    FileNotFoundError propagates unchanged; other open failures are re-raised
    as OSError with the path.
    """
    if not isinstance(path, str):
        raise TypeError(f"python/open expected a string path, received {_runtime_type_name(path)}")
    if not isinstance(mode, str):
        raise TypeError(f"python/open expected a string mode, received {_runtime_type_name(mode)}")
    if mode not in _SAFE_PYTHON_OPEN_MODES:
        raise ValueError("python/open only allows text modes 'r', 'w', or 'a'")
    try:
        handle = open(path, mode, encoding="utf-8")
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise OSError(f"python/open could not open {path}: {exc}") from exc
    return GeniaPythonHandle("file", handle)


def _ensure_python_file(value: Any, name: str) -> io.TextIOBase:
    """Return the text stream inside value or reject a non-file argument.

    Both a raw io.TextIOBase and a GeniaPythonHandle containing one are
    accepted. name prefixes the TypeError diagnostic. This check does not open,
    close, or verify the current closed state of the stream.
    """
    if isinstance(value, GeniaPythonHandle):
        value = value.value
    if not isinstance(value, io.TextIOBase):
        raise TypeError(f"{name} expected a python file handle, received {_runtime_type_name(value)}")
    return value


def _python_read_impl(handle: Any) -> str:
    """Read all remaining text from a borrowed Python file handle.

    Reading advances the stream position but does not close the handle.
    Validation and underlying stream errors propagate.
    """
    file_handle = _ensure_python_file(handle, "python/read")
    return file_handle.read()


def _python_write_impl(handle: Any, text: Any) -> int:
    """Write text at a borrowed file handle's current position.

    text must be a string. Return the stream's character count; do not flush or
    close it. Validation and underlying stream errors propagate.
    """
    file_handle = _ensure_python_file(handle, "python/write")
    if not isinstance(text, str):
        raise TypeError(f"python/write expected a string as second argument, received {_runtime_type_name(text)}")
    return file_handle.write(text)


def _python_close_impl(handle: Any) -> Any:
    """Close a Python text-file handle and return host None.

    The surrounding bridge converts that None to canonical Genia absence.
    Handle validation and close errors propagate.
    """
    file_handle = _ensure_python_file(handle, "python/close")
    file_handle.close()
    return None


def _python_read_text_impl(path: Any) -> str:
    """Read one filesystem path completely as UTF-8 text.

    path must be a string. FileNotFoundError propagates unchanged; other OS
    failures are re-raised as OSError with the path, while Unicode decoding
    failures propagate. No persistent file handle is returned.
    """
    if not isinstance(path, str):
        raise TypeError(f"python/read_text expected a string path, received {_runtime_type_name(path)}")
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise OSError(f"python/read_text could not read {path}: {exc}") from exc


def _python_write_text_impl(path: Any, text: Any) -> int:
    """Replace one filesystem path with UTF-8 text and return characters written.

    Both arguments must be strings. The internally opened file is closed before
    return; OS failures are re-raised as OSError with the path.
    """
    if not isinstance(path, str):
        raise TypeError(f"python/write_text expected a string path, received {_runtime_type_name(path)}")
    if not isinstance(text, str):
        raise TypeError(f"python/write_text expected a string body, received {_runtime_type_name(text)}")
    try:
        return Path(path).write_text(text, encoding="utf-8")
    except OSError as exc:
        raise OSError(f"python/write_text could not write {path}: {exc}") from exc


def _python_len_impl(value: Any) -> int:
    """Return Python's length for an already converted host value.

    Objects without a length raise the native TypeError.
    """
    return len(value)


def _python_str_impl(value: Any) -> str:
    """Return Python's string conversion for an already converted host value."""
    return str(value)


def _python_json_loads_impl(text: Any) -> Any:
    """Decode Python JSON text or raise a location-bearing ValueError.

    The input must be a string. JSON syntax errors expose the decoder's message,
    line, and column through the fixed python.json/loads prefix; decoded
    containers are converted to Genia values by the outer bridge. This is the
    Python-host compatibility surface, not portable strict JSON.
    """
    if not isinstance(text, str):
        raise TypeError(f"python.json/loads expected a string, received {_runtime_type_name(text)}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"python.json/loads invalid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}"
        ) from exc


def _python_json_dumps_impl(value: Any) -> str:
    """Encode a converted Python value as sorted-key, unescaped-Unicode JSON.

    Python's encoder defines supported values and raises its native exceptions
    for unsupported values or incomparable keys. This compatibility helper
    does not add the portable strict-JSON representation contract.
    """
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _build_python_host_module(root: Any, module_name: str) -> ModuleValue:
    """Construct the allowlisted Python host modules and return the requested one.

    root must expose a mutable loaded_modules mapping. The function seeds its
    missing python and python.json entries without replacing existing entries;
    the returned module is the newly constructed value. Exports are wrapped
    through the conversion/exception boundary above. Only those two module names
    can be returned; construction and seeding precede the PermissionError for
    any other name. Building modules performs no file open or other exported
    host operation.
    """
    json_module = ModuleValue(
        "python.json",
        {
            "loads": _wrap_python_host_callable("python.json", "loads", _python_json_loads_impl),
            "dumps": _wrap_python_host_callable("python.json", "dumps", _python_json_dumps_impl),
        },
        "<python-host:python.json>",
    )
    root.loaded_modules.setdefault("python.json", json_module)

    root_module = ModuleValue(
        "python",
        {
            "json": json_module,
            "open": _wrap_python_host_callable("python", "open", _python_open_impl),
            "read": _wrap_python_host_callable("python", "read", _python_read_impl),
            "write": _wrap_python_host_callable("python", "write", _python_write_impl),
            "close": _wrap_python_host_callable("python", "close", _python_close_impl),
            "read_text": _wrap_python_host_callable("python", "read_text", _python_read_text_impl),
            "write_text": _wrap_python_host_callable("python", "write_text", _python_write_text_impl),
            "len": _wrap_python_host_callable("python", "len", _python_len_impl),
            "str": _wrap_python_host_callable("python", "str", _python_str_impl),
        },
        "<python-host:python>",
    )
    root.loaded_modules.setdefault("python", root_module)

    if module_name == "python":
        return root_module
    if module_name == "python.json":
        return json_module
    raise PermissionError(f"Host module not allowed: {module_name}")
