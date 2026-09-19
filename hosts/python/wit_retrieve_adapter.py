"""P9 slice B — Python-host adapter to the real compiled `genia:retrieve`
WIT component (issue #951).

Scope authority: `docs/design/p9-genia-wit-interoperability-mapping.md`
(design, merged) and `docs/design/p9-wit-toolchain-build.md` (slice A,
WIT authoring + component build). This module adds no Genia semantics and
no Core IR/parser/AST change -- it is a Python-host-only adapter, never
reachable from Genia source and never registered in `genia.builtins`,
exactly like `hosts/python/r12_retrieve_cosine_fixture.py` before it.

Mechanism choice (issue #951 step 2): this slice checked whether the
`wasmtime` PyPI package (native Wasmtime embedding for Python) could serve
as the adapter's invocation mechanism. It installs cleanly
(`uv pip install wasmtime`, resolved `wasmtime==48.0.0`), but its public
API (`wasmtime.Config/Engine/Module/Instance/Linker/Store/...`) is
core-WebAssembly-only -- there is no `wasmtime.component` module and no
Component-Model-aware `Instance`/`Linker` in this installed version, so it
cannot instantiate or call a real Component-Model binary (a
`wasm32-wasip2` component, `file`-reported version `0x1000d`) at all; only
a bare core module. Using it would require either downgrading the built
artifact to a core module (defeating the point: the whole proof is that a
*real component*, not a core module, round-trips Genia values) or
reimplementing Component-Model lifting/lowering by hand in Python, which
is far more machinery than this slice's bounded proof needs. This module
therefore uses the documented fallback: shelling out to
`wasmtime run --invoke <component>.wasm <function>(<args>)`
(`wasmtime-cli 49.0.0-rc.1`, the same pinned binary slice A validated),
which *does* support real component instantiation and calls, and parsing
its deterministic `wasm-wave` textual output back into Python/Genia
values. `wasmtime` (the PyPI package) is not added as a project
dependency; it is not used anywhere in this adapter or its tests.

Failure layering (design doc §1.10), restated for this adapter:

- **L1 (Operation Outcome)** -- an ordinary `some`/`none`/`err` returned
  by the component's own `retrieve`/`echo-outcome` logic. Decoded into
  the existing `GeniaOptionSome`/`GeniaOptionNone`/`GeniaOptionErr`
  shapes, never raised as an exception.
- **L2 (adapter pre-call misuse)** -- a value this boundary forbids
  crossing at all (a protected carrier, a non-finite float, an
  unsupported map-key kind, an out-of-range exponent, ...) is rejected by
  `WitAdapterMisuseError` **before any subprocess is spawned** -- never a
  WIT/component-layer failure.
- **L3 (WIT/component-layer failure)** -- a real `wasmtime` process
  failure (nonzero exit: a Canonical ABI trap, a malformed invocation, a
  missing export, ...) is caught and normalized into
  `WitComponentFaultError`, carrying only a closed `kind` string. Raw
  `wasmtime`/Wasmtime/Rust process output (stderr text, backtraces,
  instruction pointers) never crosses into the normalized diagnostic or
  any Genia-visible value, mirroring PAI-8 "normalize at the owner."
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from genia.numeric_runtime import GeniaDecimal, GeniaRational, rational_from_integers
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionNone, GeniaOptionSome, GeniaProtected

_COMPONENT_RELATIVE_PATH = Path(
    "wit/genia-retrieve-component/target/wasm32-wasip2/release/genia_retrieve_component.wasm"
)
_S32_MIN = -(2**31)
_S32_MAX = 2**31 - 1
_U32_MAX = 2**32 - 1


class WitAdapterMisuseError(ValueError):
    """L2 -- rejected on the Python side before any component call is made."""


class WitComponentFaultError(RuntimeError):
    """L3 -- a normalized WIT/component-layer failure.

    Carries only a closed ``kind`` classification; never the raw
    ``wasmtime`` process output (stdout/stderr/backtrace), which is
    deliberately discarded by ``_invoke`` before this is raised.
    """

    def __init__(self, kind: str) -> None:
        self.kind = kind
        super().__init__(f"wit-component-fault:{kind}")


# ---------------------------------------------------------------------------
# Component discovery
# ---------------------------------------------------------------------------


def discover_repo_root(start: Path | None = None) -> Path:
    """Walk upward from this file (or ``start``) to find the repo root.

    The root is identified by the presence of ``pyproject.toml``, exactly
    the same convention every other `hosts/python/exec_*` entry point
    assumes implicitly via `pythonpath` in `pytest.ini`.
    """

    current = (start or Path(__file__)).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise FileNotFoundError("could not locate genia-2026 repository root (no pyproject.toml found)")


def find_component(repo_root: Path | None = None) -> Path:
    """Return the built component's path, raising if it has not been built.

    Never builds the component itself -- build is `docs/design/
    p9-wit-toolchain-build.md`'s documented, separate reproducible step.
    """

    root = repo_root or discover_repo_root()
    path = root / _COMPONENT_RELATIVE_PATH
    if not path.is_file():
        raise FileNotFoundError(
            "genia:retrieve WIT component is not built; see "
            "docs/design/p9-wit-toolchain-build.md section 3.3/5 to build it "
            f"(expected at {path})"
        )
    return path


# ---------------------------------------------------------------------------
# Encoding: Genia/Python values -> wasm-wave literal text
# ---------------------------------------------------------------------------


def _encode_genia_integer(value: int) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        raise WitAdapterMisuseError(f"expected an Integer, received {type(value).__name__}")
    negative = value < 0
    magnitude = abs(value)
    limbs: list[int] = []
    remaining = magnitude
    while remaining:
        limbs.append(remaining & 0xFFFFFFFF)
        remaining >>= 32
    limbs_text = ", ".join(str(limb) for limb in limbs)
    return f"{{negative: {'true' if negative else 'false'}, magnitude-digits: [{limbs_text}]}}"


def _encode_genia_decimal(value: GeniaDecimal) -> str:
    if value.exponent < _S32_MIN or value.exponent > _S32_MAX:
        raise WitAdapterMisuseError(
            f"Decimal exponent {value.exponent} does not fit this WIT interface's s32 exponent "
            "field (design doc section 1.11 exponent-range narrowing)"
        )
    coefficient = _encode_genia_integer(value.coefficient)
    return f"{{coefficient: {coefficient}, exponent: {value.exponent}}}"


def _encode_genia_rational(value: GeniaRational) -> str:
    numerator = _encode_genia_integer(value.numerator)
    denominator = _encode_genia_integer(value.denominator)
    return f"{{numerator: {numerator}, denominator: {denominator}}}"


def _encode_float64(value: float) -> str:
    if isinstance(value, bool) or not isinstance(value, float):
        raise WitAdapterMisuseError(f"expected a Float64, received {type(value).__name__}")
    import math

    if not math.isfinite(value):
        raise WitAdapterMisuseError(
            "non-finite Float64 (NaN/infinity) is not admissible on this boundary "
            "(design doc section 1.11: this interface legally admits only finite scores)"
        )
    return repr(value)


def encode_score(value: Any) -> str:
    """Encode an Integer/GeniaDecimal/GeniaRational/float into `genia-score`."""

    if isinstance(value, GeniaProtected):
        raise WitAdapterMisuseError("a protected carrier may never cross this WIT boundary (design doc section 1.7)")
    if isinstance(value, bool):
        raise WitAdapterMisuseError("bool is not an admissible genia-score kind")
    if isinstance(value, int):
        return f"score-integer({_encode_genia_integer(value)})"
    if isinstance(value, GeniaDecimal):
        return f"score-decimal({_encode_genia_decimal(value)})"
    if isinstance(value, GeniaRational):
        return f"score-rational({_encode_genia_rational(value)})"
    if isinstance(value, float):
        return f"score-float64({_encode_float64(value)})"
    raise WitAdapterMisuseError(f"unsupported genia-score kind: {type(value).__name__}")


def _encode_string(value: str) -> str:
    if not isinstance(value, str):
        raise WitAdapterMisuseError(f"expected a String, received {type(value).__name__}")
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _encode_map_value(value: Any) -> str:
    if isinstance(value, GeniaProtected):
        raise WitAdapterMisuseError("a protected carrier may never cross this WIT boundary (design doc section 1.7)")
    if isinstance(value, bool):
        raise WitAdapterMisuseError("bool is not an admissible genia-ordered-map key/value kind on this interface")
    if isinstance(value, int):
        return f"map-integer({_encode_genia_integer(value)})"
    if isinstance(value, str):
        return f"map-string({_encode_string(value)})"
    raise WitAdapterMisuseError(
        f"unsupported genia-ordered-map key/value kind on this narrow interface: {type(value).__name__} "
        "(design doc section 1.6/slice A section 2.2: only Integer and String are admissible here)"
    )


def encode_ordered_map(value: GeniaMap) -> str:
    """Encode a `GeniaMap` into `genia-ordered-map`, preserving R17/R18 order.

    Iterates `GeniaMap.items()`, which already reflects R17's
    deterministic construction order (`GeniaMap.put` dedups by R18
    canonical key identity in-place, per `src/genia/values.py`), so no
    separate canonicalization/dedup pass is needed here -- the existing
    Genia-side Map already enforces it before this function ever sees it.
    """

    if not isinstance(value, GeniaMap):
        raise WitAdapterMisuseError(f"expected a Map, received {type(value).__name__}")
    entries = []
    for key, entry_value in value.items():
        key_text = _encode_map_value(key)
        value_text = _encode_map_value(entry_value)
        entries.append(f"{{key: {key_text}, value: {value_text}}}")
    return "[" + ", ".join(entries) + "]"


def _encode_context(context: Any) -> str:
    if context is None:
        return "none"
    if not isinstance(context, GeniaMap):
        raise WitAdapterMisuseError(f"expected a Map context, received {type(context).__name__}")
    entries = []
    for key, entry_value in context.items():
        if not isinstance(key, str):
            raise WitAdapterMisuseError("outcome context keys must be strings on this narrow interface")
        if isinstance(entry_value, bool):
            raise WitAdapterMisuseError("bool is not an admissible context-value kind on this interface")
        if isinstance(entry_value, int):
            value_text = f"context-integer({_encode_genia_integer(entry_value)})"
        elif isinstance(entry_value, str):
            value_text = f"context-symbol({_encode_string(entry_value)})"
        else:
            raise WitAdapterMisuseError(
                f"unsupported context-value kind on this narrow interface: {type(entry_value).__name__}"
            )
        entries.append(f"{{key: {_encode_string(key)}, value: {value_text}}}")
    return "some({entries: [" + ", ".join(entries) + "]})"


def encode_outcome(value: Any) -> str:
    """Encode a `GeniaOptionSome`/`GeniaOptionNone`/`GeniaOptionErr` into
    `genia-outcome`, restricted to this narrow interface's evidence-list
    success payload and Integer/String context leaf shapes (design doc
    section 1.4).
    """

    if isinstance(value, GeniaOptionSome):
        evidence_items = value.value
        if not isinstance(evidence_items, list):
            raise WitAdapterMisuseError("genia-outcome some payload must be a list of evidence items")
        rendered = []
        for item in evidence_items:
            if not isinstance(item, GeniaMap):
                raise WitAdapterMisuseError("each evidence item must be a Map with 'chunk'/'score' fields")
            chunk = item.get("chunk", None)
            if not isinstance(chunk, str):
                raise WitAdapterMisuseError("evidence 'chunk' must be a String")
            score_text = encode_score(item.get("score", None))
            rendered.append(f"{{chunk: {_encode_string(chunk)}, score: {score_text}}}")
        context_text = _encode_context(value.context)
        return f"outcome-some({{value: [{', '.join(rendered)}], context: {context_text}}})"
    if isinstance(value, GeniaOptionNone):
        context_text = _encode_context(value.context)
        return f"outcome-none({{reason: {_encode_string(value.reason)}, context: {context_text}}})"
    if isinstance(value, GeniaOptionErr):
        context_text = _encode_context(value.context)
        return f"outcome-err({{reason: {_encode_string(value.reason)}, context: {context_text}}})"
    raise WitAdapterMisuseError(f"expected an Outcome (some/none/err), received {type(value).__name__}")


# ---------------------------------------------------------------------------
# Decoding: a small hand-rolled `wasm-wave` textual parser
#
# wasmtime's `run --invoke` prints its result in `wasm-wave` syntax, which
# is a small, fixed grammar for this proof's purposes: records `{k: v,
# ...}`, lists `[v, ...]`, tagged variants `name(payload)` or bare `name`,
# strings, numbers, and booleans. This parser targets exactly that
# grammar -- it is not a general wasm-wave implementation.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _WaveVariant:
    name: str
    payload: Any


class _WaveParseError(ValueError):
    pass


class _WaveParser:
    def __init__(self, text: str) -> None:
        self._text = text
        self._pos = 0
        self._len = len(text)

    def parse(self) -> Any:
        value = self._parse_value()
        self._skip_ws()
        if self._pos != self._len:
            raise _WaveParseError(f"trailing content at offset {self._pos}")
        return value

    def _skip_ws(self) -> None:
        while self._pos < self._len and self._text[self._pos] in " \t\r\n":
            self._pos += 1

    def _peek(self) -> str:
        if self._pos >= self._len:
            raise _WaveParseError("unexpected end of input")
        return self._text[self._pos]

    def _expect(self, char: str) -> None:
        self._skip_ws()
        if self._pos >= self._len or self._text[self._pos] != char:
            raise _WaveParseError(f"expected {char!r} at offset {self._pos}")
        self._pos += 1

    def _parse_value(self) -> Any:
        self._skip_ws()
        char = self._peek()
        if char == "{":
            return self._parse_record()
        if char == "[":
            return self._parse_list()
        if char == '"':
            return self._parse_string()
        if char == "-" or char.isdigit():
            return self._parse_number()
        return self._parse_ident_or_call()

    def _parse_record(self) -> dict[str, Any]:
        self._expect("{")
        result: dict[str, Any] = {}
        self._skip_ws()
        if self._pos < self._len and self._text[self._pos] == "}":
            self._pos += 1
            return result
        while True:
            self._skip_ws()
            key = self._parse_bare_ident()
            self._expect(":")
            value = self._parse_value()
            result[key] = value
            self._skip_ws()
            if self._pos < self._len and self._text[self._pos] == ",":
                self._pos += 1
                continue
            break
        self._expect("}")
        return result

    def _parse_list(self) -> list[Any]:
        self._expect("[")
        result: list[Any] = []
        self._skip_ws()
        if self._pos < self._len and self._text[self._pos] == "]":
            self._pos += 1
            return result
        while True:
            result.append(self._parse_value())
            self._skip_ws()
            if self._pos < self._len and self._text[self._pos] == ",":
                self._pos += 1
                continue
            break
        self._expect("]")
        return result

    def _parse_string(self) -> str:
        self._expect('"')
        chars = []
        while True:
            if self._pos >= self._len:
                raise _WaveParseError("unterminated string literal")
            char = self._text[self._pos]
            if char == '"':
                self._pos += 1
                break
            if char == "\\":
                self._pos += 1
                if self._pos >= self._len:
                    raise _WaveParseError("unterminated escape sequence")
                escaped = self._text[self._pos]
                chars.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(escaped, escaped))
                self._pos += 1
                continue
            chars.append(char)
            self._pos += 1
        return "".join(chars)

    def _parse_number(self) -> int | float:
        start = self._pos
        if self._text[self._pos] == "-":
            self._pos += 1
        while self._pos < self._len and (self._text[self._pos].isdigit() or self._text[self._pos] in ".eE+-"):
            self._pos += 1
        text = self._text[start : self._pos]
        if any(marker in text for marker in ".eE"):
            return float(text)
        return int(text)

    def _parse_bare_ident(self) -> str:
        self._skip_ws()
        start = self._pos
        while self._pos < self._len and (self._text[self._pos].isalnum() or self._text[self._pos] in "-_"):
            self._pos += 1
        if start == self._pos:
            raise _WaveParseError(f"expected an identifier at offset {self._pos}")
        return self._text[start : self._pos]

    def _parse_ident_or_call(self) -> Any:
        ident = self._parse_bare_ident()
        if ident == "true":
            return True
        if ident == "false":
            return False
        if ident == "none":
            return _WaveVariant("none", None)
        self._skip_ws()
        if self._pos < self._len and self._text[self._pos] == "(":
            self._pos += 1
            payload = self._parse_value()
            self._expect(")")
            return _WaveVariant(ident, payload)
        return _WaveVariant(ident, None)


def _parse_wave(text: str) -> Any:
    try:
        return _WaveParser(text.strip()).parse()
    except _WaveParseError:
        raise WitComponentFaultError("malformed-output") from None


# ---------------------------------------------------------------------------
# Decoding: parsed wave structure -> Genia/Python values
# ---------------------------------------------------------------------------


def _decode_genia_integer(node: dict) -> int:
    negative = bool(node["negative"])
    magnitude = 0
    for limb in reversed(node["magnitude-digits"]):
        magnitude = (magnitude << 32) | int(limb)
    return -magnitude if negative else magnitude


def _decode_genia_decimal(node: dict) -> GeniaDecimal:
    coefficient = _decode_genia_integer(node["coefficient"])
    exponent = int(node["exponent"])
    return GeniaDecimal(coefficient, exponent)


def _decode_genia_rational(node: dict) -> Any:
    numerator = _decode_genia_integer(node["numerator"])
    denominator = _decode_genia_integer(node["denominator"])
    return rational_from_integers(numerator, denominator)


def decode_score(node: _WaveVariant) -> Any:
    if not isinstance(node, _WaveVariant):
        raise WitComponentFaultError("malformed-output")
    if node.name == "score-integer":
        return _decode_genia_integer(node.payload)
    if node.name == "score-decimal":
        return _decode_genia_decimal(node.payload)
    if node.name == "score-rational":
        return _decode_genia_rational(node.payload)
    if node.name == "score-float64":
        return float(node.payload)
    raise WitComponentFaultError("malformed-output")


def _decode_map_value(node: _WaveVariant) -> Any:
    if not isinstance(node, _WaveVariant):
        raise WitComponentFaultError("malformed-output")
    if node.name == "map-integer":
        return _decode_genia_integer(node.payload)
    if node.name == "map-string":
        return str(node.payload)
    raise WitComponentFaultError("malformed-output")


def decode_ordered_map(node: list) -> GeniaMap:
    if not isinstance(node, list):
        raise WitComponentFaultError("malformed-output")
    result = GeniaMap()
    for entry in node:
        key = _decode_map_value(entry["key"])
        value = _decode_map_value(entry["value"])
        result = result.put(key, value)
    return result


def _decode_context(node: Any) -> Any:
    if isinstance(node, _WaveVariant) and node.name == "none":
        return None
    if isinstance(node, _WaveVariant) and node.name == "some":
        payload = node.payload
    elif isinstance(node, dict):
        payload = node
    else:
        raise WitComponentFaultError("malformed-output")
    result = GeniaMap()
    for entry in payload["entries"]:
        key = entry["key"]
        value_node = entry["value"]
        if not isinstance(value_node, _WaveVariant):
            raise WitComponentFaultError("malformed-output")
        if value_node.name == "context-integer":
            value = _decode_genia_integer(value_node.payload)
        elif value_node.name == "context-symbol":
            value = str(value_node.payload)
        else:
            raise WitComponentFaultError("malformed-output")
        result = result.put(key, value)
    return result


def decode_outcome(node: _WaveVariant) -> Any:
    if not isinstance(node, _WaveVariant):
        raise WitComponentFaultError("malformed-output")
    if node.name == "outcome-some":
        payload = node.payload
        context = _decode_context(payload.get("context", _WaveVariant("none", None)))
        evidence = []
        for item in payload["value"]:
            entry = GeniaMap().put("chunk", str(item["chunk"])).put("score", decode_score(item["score"]))
            evidence.append(entry)
        return GeniaOptionSome(evidence, context)
    if node.name == "outcome-none":
        payload = node.payload
        context = _decode_context(payload.get("context", _WaveVariant("none", None)))
        return GeniaOptionNone(str(payload["reason"]), context)
    if node.name == "outcome-err":
        payload = node.payload
        context = _decode_context(payload.get("context", _WaveVariant("none", None)))
        return GeniaOptionErr(str(payload["reason"]), context)
    raise WitComponentFaultError("malformed-output")


# ---------------------------------------------------------------------------
# Invocation
# ---------------------------------------------------------------------------


def _classify_failure(stderr_text: str) -> str:
    """Classify a nonzero-exit wasmtime failure into a closed L3 kind.

    Only the classification (never the raw text itself) is retained.
    """

    lowered = stderr_text.lower()
    if "no exported func" in lowered:
        return "invocation-invalid"
    if "interpreting parameters" in lowered or "invalid value type" in lowered:
        return "invalid-arguments"
    if "trap" in lowered or "panic" in lowered:
        return "trap"
    return "other"


def _invoke(component_path: Path, function_name: str, arg_literals: list[str], *, timeout_s: float = 30.0) -> Any:
    """Run one real `wasmtime run --invoke` call and parse its result.

    Raises `WitComponentFaultError` (never a raw subprocess exception, and
    never with raw stderr text in the message) on any nonzero exit,
    timeout, or missing `wasmtime` binary.
    """

    invocation = f"{function_name}({', '.join(arg_literals)})"
    try:
        completed = subprocess.run(
            ["wasmtime", "run", "--invoke", invocation, str(component_path)],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except FileNotFoundError:
        raise WitComponentFaultError("wasmtime-not-found") from None
    except subprocess.TimeoutExpired:
        raise WitComponentFaultError("timeout") from None

    if completed.returncode != 0:
        raise WitComponentFaultError(_classify_failure(completed.stderr or ""))

    return _parse_wave(completed.stdout)


# ---------------------------------------------------------------------------
# Public round-trip operations
# ---------------------------------------------------------------------------


def echo_score(component_path: Path, value: Any) -> Any:
    """Real round trip of one `genia-score` value through the compiled component."""

    literal = encode_score(value)
    node = _invoke(component_path, "echo-score", [literal])
    return decode_score(node)


def echo_outcome(component_path: Path, value: Any) -> Any:
    """Real round trip of one `genia-outcome` value through the compiled component."""

    literal = encode_outcome(value)
    node = _invoke(component_path, "echo-outcome", [literal])
    return decode_outcome(node)


def echo_map(component_path: Path, value: GeniaMap) -> GeniaMap:
    """Real round trip of one `genia-ordered-map` value through the compiled component."""

    literal = encode_ordered_map(value)
    node = _invoke(component_path, "echo-map", [literal])
    return decode_ordered_map(node)


@dataclass(frozen=True)
class IndexRef:
    """Mirrors WIT `index-ref` (design doc section 1.2/slice A section 2.1)."""

    handle_id: int
    space: str
    dims: int


def _encode_index_ref(index: IndexRef) -> str:
    if not isinstance(index, IndexRef):
        raise WitAdapterMisuseError(f"expected an IndexRef, received {type(index).__name__}")
    if isinstance(index.handle_id, bool) or not isinstance(index.handle_id, int) or index.handle_id < 0:
        raise WitAdapterMisuseError("IndexRef.handle_id must be a non-negative Integer")
    if index.handle_id > _U32_MAX * (2**32):  # generous, u64 range check via python int
        raise WitAdapterMisuseError("IndexRef.handle_id exceeds this interface's u64 range")
    if not isinstance(index.space, str):
        raise WitAdapterMisuseError("IndexRef.space must be a String")
    if isinstance(index.dims, bool) or not isinstance(index.dims, int) or not (0 <= index.dims <= _U32_MAX):
        raise WitAdapterMisuseError("IndexRef.dims must be a u32-range Integer")
    return f"{{handle-id: {index.handle_id}, space: {_encode_string(index.space)}, dims: {index.dims}}}"


def retrieve(component_path: Path, query_embedding: list[float], k: int, index: IndexRef, config: GeniaMap) -> Any:
    """Real call to the proof target's `retrieve` export.

    Mirrors R12's `retrieve/4` handler shape (design doc section 2), minus
    the already-declassified credential and never-crossing provider/
    authority values (design doc section 1.7/1.9), which this adapter's
    caller is responsible for handling entirely host-side, exactly as the
    existing `GeniaRetriever.__call__` already does for realizations A/B.
    """

    if not isinstance(query_embedding, list) or not all(
        isinstance(component, float) and not isinstance(component, bool) for component in query_embedding
    ):
        raise WitAdapterMisuseError("query_embedding must be a list of Float64 values")
    for component in query_embedding:
        import math

        if not math.isfinite(component):
            raise WitAdapterMisuseError("query_embedding components must be finite")
    if isinstance(k, bool) or not isinstance(k, int) or not (0 <= k <= _U32_MAX):
        raise WitAdapterMisuseError("k must be a u32-range Integer")

    embedding_literal = "[" + ", ".join(repr(float(component)) for component in query_embedding) + "]"
    index_literal = _encode_index_ref(index)
    config_literal = encode_ordered_map(config)
    node = _invoke(component_path, "retrieve", [embedding_literal, str(k), index_literal, config_literal])
    return decode_outcome(node)
