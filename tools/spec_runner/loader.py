from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised in runtime environments
    yaml = None


REPO_ROOT = Path(__file__).resolve().parents[2]

# Only executable shared-spec categories belong here.
SPEC_CATEGORIES = ["eval", "cli", "ir", "flow", "error", "parse"]
SPEC_ROOTS = [REPO_ROOT / "spec" / cat for cat in SPEC_CATEGORIES]

# All categories use the same top-level envelope.
ALLOWED_TOP_LEVEL_KEYS = {
    "name",
    "id",
    "category",
    "description",
    "input",
    "expected",
    "notes",
}

ALLOWED_INPUT_KEYS_BY_CATEGORY = {
    "eval": {"source", "stdin"},
    "ir": {"source"},
    "cli": {"source", "file", "command", "stdin", "argv", "debug_stdio"},
    "flow": {"source", "stdin"},
    "error": {"source", "stdin"},
    "parse": {"source"},
}

ALLOWED_EXPECTED_KEYS_BY_CATEGORY = {
    "eval": {"stdout", "stderr", "exit_code"},
    "ir": {"ir"},
    "cli": {"stdout", "stderr", "exit_code"},
    "flow": {"stdout", "stderr", "exit_code"},
    "error": {"stdout", "stderr", "exit_code"},
    "parse": {"parse"},
}

FLOW_TERMINAL_PATTERN = re.compile(r"\b(?:collect|run)\b")


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
    description: str = ""
    file: str | None = None
    command: str | None = None
    argv: list[str] | None = None
    debug_stdio: bool = False
    spec_id: str | None = None
    expected_parse: Any | None = None


@dataclass(frozen=True)
class InvalidSpec:
    path: Path
    message: str


def _validate_mapping(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def _validate_top_level(data: dict[str, Any], path: Path) -> None:
    unknown_top_level = set(data) - ALLOWED_TOP_LEVEL_KEYS
    if unknown_top_level:
        raise ValueError(f"unknown top-level fields: {sorted(unknown_top_level)}")

    for required_key in ("name", "category", "input", "expected"):
        if required_key not in data:
            raise ValueError(f"missing required field: {required_key}")

    if data["category"] not in SPEC_CATEGORIES:
        raise ValueError(f"unsupported category: {data['category']}")

    if not isinstance(data["name"], str) or not data["name"]:
        raise ValueError("name must be a non-empty string")

    if path.stem != data["name"]:
        raise ValueError(f"spec file stem must match name: {path.stem!r} != {data['name']!r}")

    if "id" in data and (not isinstance(data["id"], str) or not data["id"]):
        raise ValueError("id must be a non-empty string when present")

    if "description" in data and not isinstance(data["description"], str):
        raise ValueError("description must be a string when present")

    if "notes" in data and not isinstance(data["notes"], str):
        raise ValueError("notes must be a string when present")


def _validate_input(category: str, input_data: dict[str, Any]) -> None:
    allowed_input_keys = ALLOWED_INPUT_KEYS_BY_CATEGORY[category]
    unknown_input = set(input_data) - allowed_input_keys
    if unknown_input:
        raise ValueError(f"unknown input fields: {sorted(unknown_input)}")

    if "source" not in input_data:
        raise ValueError("missing required field: input.source")
    if not isinstance(input_data["source"], str):
        raise ValueError("input.source must be a string")

    if category in ("eval", "error"):
        if "stdin" in input_data and not isinstance(input_data["stdin"], str):
            raise ValueError("input.stdin must be a string")
        return

    if category in ("ir", "parse"):
        return

    if category == "flow":
        if "stdin" in input_data and not isinstance(input_data["stdin"], str):
            raise ValueError("input.stdin must be a string")
        if not FLOW_TERMINAL_PATTERN.search(input_data["source"]):
            raise ValueError("flow spec input.source must explicitly consume the flow with collect or run")
        return

    # CLI validation
    if "stdin" not in input_data:
        raise ValueError("missing required field: input.stdin")
    if not isinstance(input_data["stdin"], str):
        raise ValueError("input.stdin must be a string")

    for optional_text_key in ("file", "command", "stdin"):
        if optional_text_key in input_data:
            value = input_data[optional_text_key]
            if value is not None and not isinstance(value, str):
                raise ValueError(f"input.{optional_text_key} must be a string or null")

    if "argv" not in input_data:
        raise ValueError("missing required field: input.argv")
    if not isinstance(input_data["argv"], list) or not all(isinstance(x, str) for x in input_data["argv"]):
        raise ValueError("input.argv must be a list of strings")

    if "debug_stdio" in input_data and not isinstance(input_data["debug_stdio"], bool):
        raise ValueError("input.debug_stdio must be a boolean")

    file_value = input_data.get("file")
    command_value = input_data.get("command")
    stdin_value = input_data["stdin"]

    has_file = isinstance(file_value, str) and file_value != ""
    has_command = isinstance(command_value, str) and command_value != ""
    has_stdin = isinstance(stdin_value, str) and stdin_value != ""

    # Valid CLI modes:
    # - file mode: file only, stdin empty
    # - command mode: command only, stdin empty
    # - pipe mode: command required, stdin may be non-empty
    if has_file:
        if has_command or has_stdin:
            raise ValueError("cli file mode requires input.file only; command/stdin must be empty")
        if input_data["source"] != file_value:
            raise ValueError("cli file mode requires input.source to match input.file")
        return

    if has_command and not has_stdin:
        if input_data["source"] != command_value:
            raise ValueError("cli command mode requires input.source to match input.command")
        return  # command mode

    if has_command:
        if input_data["source"] != command_value:
            raise ValueError("cli pipe mode requires input.source to match input.command")
        if input_data["argv"]:
            raise ValueError("cli pipe mode requires input.argv to be empty")
        return  # pipe mode (command + stdin)

    raise ValueError("cli spec must provide input.file or input.command")


def _validate_expected(category: str, expected_data: dict[str, Any]) -> None:
    allowed_expected_keys = ALLOWED_EXPECTED_KEYS_BY_CATEGORY[category]
    unknown_expected = set(expected_data) - allowed_expected_keys
    if unknown_expected:
        raise ValueError(f"unknown expected fields: {sorted(unknown_expected)}")

    if category == "ir":
        if "ir" not in expected_data:
            raise ValueError("missing required field: expected.ir")
        if expected_data["ir"] is None:
            raise ValueError("expected.ir must not be null")
        return

    if category == "parse":
        if "parse" not in expected_data:
            raise ValueError("missing required field: expected.parse")
        parse_result = expected_data["parse"]
        if not isinstance(parse_result, dict):
            raise ValueError("expected.parse must be a mapping")
        if "kind" not in parse_result:
            raise ValueError("expected.parse.kind is required")
        kind = parse_result["kind"]
        if kind not in ("ok", "error"):
            raise ValueError(f"expected.parse.kind must be 'ok' or 'error', got {kind!r}")
        if kind == "ok":
            if "ast" not in parse_result:
                raise ValueError("expected.parse.ast is required when kind is 'ok'")
        else:
            if "type" not in parse_result:
                raise ValueError("expected.parse.type is required when kind is 'error'")
            if "message" not in parse_result:
                raise ValueError("expected.parse.message is required when kind is 'error'")
        return

    for required_key in ("stdout", "stderr", "exit_code"):
        if required_key not in expected_data:
            raise ValueError(f"missing required field: expected.{required_key}")

    if not isinstance(expected_data["stdout"], str):
        raise ValueError("expected.stdout must be a string")
    if not isinstance(expected_data["stderr"], str):
        raise ValueError("expected.stderr must be a string")
    if not isinstance(expected_data["exit_code"], int):
        raise ValueError("expected.exit_code must be an integer")


def load_spec(path: Path) -> LoadedSpec:
    source_text = path.read_text(encoding="utf-8")
    if yaml is not None:
        raw = yaml.safe_load(source_text)
    else:
        raw = _safe_load_with_ruby(source_text)
    data = _validate_mapping(raw, field_name="spec")

    _validate_top_level(data, path)

    input_data = _validate_mapping(data["input"], field_name="input")
    expected_data = _validate_mapping(data["expected"], field_name="expected")

    category = data["category"]
    _validate_input(category, input_data)
    _validate_expected(category, expected_data)

    return LoadedSpec(
        name=data["name"],
        category=category,
        source=input_data["source"],
        stdin=input_data.get("stdin", ""),
        expected_stdout=expected_data.get("stdout"),
        expected_stderr=expected_data.get("stderr"),
        expected_exit_code=expected_data.get("exit_code"),
        expected_ir=expected_data.get("ir"),
        path=path,
        description=data.get("description", ""),
        file=input_data.get("file"),
        command=input_data.get("command"),
        argv=input_data.get("argv", []),
        debug_stdio=input_data.get("debug_stdio", False),
        spec_id=data.get("id"),
        expected_parse=expected_data.get("parse"),
    )


def _safe_load_with_ruby(source_text: str) -> Any:
    ruby_cmd = [
        "ruby",
        "-rjson",
        "-ryaml",
        "-e",
        (
            "src = STDIN.read\n"
            "obj = YAML.safe_load(src, permitted_classes: [], aliases: false)\n"
            "STDOUT.write(JSON.generate(obj))\n"
        ),
    ]
    try:
        proc = subprocess.run(
            ruby_cmd,
            input=source_text,
            text=True,
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "tools.spec_runner requires PyYAML, or a Ruby runtime with YAML support"
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or "unknown YAML parse error"
        raise ValueError(f"invalid YAML: {detail}") from exc

    try:
        import json

        return json.loads(proc.stdout)
    except Exception as exc:  # pragma: no cover - defensive parsing guard
        raise ValueError("invalid YAML: ruby conversion returned invalid JSON") from exc


def discover_specs() -> tuple[list[LoadedSpec], list[InvalidSpec]]:
    specs: list[LoadedSpec] = []
    invalid_specs: list[InvalidSpec] = []
    seen_names: set[str] = set()

    for root in SPEC_ROOTS:
        if not root.exists():
            continue
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
