from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - exercised in runtime environments
    raise RuntimeError(
        "tools.spec_runner requires PyYAML in the active environment"
    ) from exc



REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_CATEGORIES = ["eval", "error", "flow", "pattern", "cli", "ir"]
SPEC_ROOTS = [REPO_ROOT / "spec" / cat for cat in SPEC_CATEGORIES]
ALLOWED_TOP_LEVEL_KEYS = {"name", "category", "input", "expected", "notes"}
ALLOWED_INPUT_KEYS_BY_CATEGORY = {
    "eval": {"source", "stdin"},
    "error": {"source", "stdin"},
    "flow": {"source", "stdin"},
    "pattern": {"source", "stdin"},
    "cli": {"source", "stdin"},
    "ir": {"source"},
}
ALLOWED_EXPECTED_KEYS_BY_CATEGORY = {
    "eval": {"stdout", "stderr", "exit_code"},
    "error": {"stdout", "stderr", "exit_code"},
    "flow": {"stdout", "stderr", "exit_code"},
    "pattern": {"stdout", "stderr", "exit_code"},
    "cli": {"stdout", "stderr", "exit_code"},
    "ir": {"ir"},
}


@dataclass(frozen=True)
class LoadedSpec:
    name: str
    category: str
    source: str
    stdin: str
    expected_stdout: str | None
    expected_stderr: str | None
    expected_exit_code: int | None
    expected_ir: Any | None
    path: Path


@dataclass(frozen=True)
class InvalidSpec:
    path: Path
    message: str


def _validate_mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def load_spec(path: Path) -> LoadedSpec:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    data = _validate_mapping(raw, field_name="spec")

    unknown_top_level = set(data) - ALLOWED_TOP_LEVEL_KEYS
    if unknown_top_level:
        raise ValueError(f"unknown top-level fields: {sorted(unknown_top_level)}")

    for required_key in ("name", "category", "input", "expected"):
        if required_key not in data:
            raise ValueError(f"missing required field: {required_key}")

    if data["category"] not in SPEC_CATEGORIES:
        raise ValueError(f"unsupported category: {data['category']}")

    input_data = _validate_mapping(data["input"], field_name="input")
    allowed_input_keys = ALLOWED_INPUT_KEYS_BY_CATEGORY[data["category"]]
    unknown_input = set(input_data) - allowed_input_keys
    if unknown_input:
        raise ValueError(f"unknown input fields: {sorted(unknown_input)}")
    if "source" not in input_data:
        raise ValueError("missing required field: input.source")

    expected_data = _validate_mapping(data["expected"], field_name="expected")
    allowed_expected_keys = ALLOWED_EXPECTED_KEYS_BY_CATEGORY[data["category"]]
    unknown_expected = set(expected_data) - allowed_expected_keys
    if unknown_expected:
        raise ValueError(f"unknown expected fields: {sorted(unknown_expected)}")
    if data["category"] == "ir":
        if "ir" not in expected_data:
            raise ValueError("missing required field: expected.ir")
    else:
        for required_key in ("stdout", "stderr", "exit_code"):
            if required_key not in expected_data:
                raise ValueError(f"missing required field: expected.{required_key}")

    if not isinstance(data["name"], str) or not data["name"]:
        raise ValueError("name must be a non-empty string")
    if path.stem != data["name"]:
        raise ValueError(f"spec file stem must match name: {path.stem!r} != {data['name']!r}")
    if not isinstance(input_data["source"], str):
        raise ValueError("input.source must be a string")
    if "stdin" in input_data and not isinstance(input_data["stdin"], str):
        raise ValueError("input.stdin must be a string")
    if data["category"] == "ir":
        if expected_data["ir"] is None:
            raise ValueError("expected.ir must not be null")
    else:
        if not isinstance(expected_data["stdout"], str):
            raise ValueError("expected.stdout must be a string")
        if not isinstance(expected_data["stderr"], str):
            raise ValueError("expected.stderr must be a string")
        if not isinstance(expected_data["exit_code"], int):
            raise ValueError("expected.exit_code must be an integer")

    return LoadedSpec(
        name=data["name"],
        category=data["category"],
        source=input_data["source"],
        stdin=input_data.get("stdin", ""),
        expected_stdout=expected_data.get("stdout"),
        expected_stderr=expected_data.get("stderr"),
        expected_exit_code=expected_data.get("exit_code"),
        expected_ir=expected_data.get("ir"),
        path=path,
    )


def discover_specs() -> tuple[list[LoadedSpec], list[InvalidSpec]]:
    specs: list[LoadedSpec] = []
    invalid_specs: list[InvalidSpec] = []
    seen_names: set[str] = set()
    for root in SPEC_ROOTS:
        for path in sorted(root.glob("*.yaml")):
            try:
                spec = load_spec(path)
            except Exception as exc:  # noqa: BLE001
                invalid_specs.append(InvalidSpec(path=path, message=str(exc)))
                continue
            if spec.name in seen_names:
                invalid_specs.append(InvalidSpec(path=path, message=f"duplicate spec name: {spec.name}"))
                continue
            seen_names.add(spec.name)
            specs.append(spec)
    return specs, invalid_specs
