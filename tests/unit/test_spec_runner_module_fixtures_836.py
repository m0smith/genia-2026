from __future__ import annotations

import json
from pathlib import Path

import pytest

from hosts.python.protocol_adapter import _spec_for_operation
from tools.spec_runner.host_executor import build_host_request, execute_spec_via_host
from tools.spec_runner.loader import load_spec
from tools.spec_runner.protocol import encode_request


def _write_case(tmp_path: Path, input_yaml: str) -> Path:
    path = tmp_path / "fixture-case.yaml"
    path.write_text(
        "name: fixture-case\ncategory: eval\ninput:\n" + input_yaml
        + 'expected:\n  stdout: "ok\\n"\n  stderr: ""\n  exit_code: 0\n',
        encoding="utf-8",
    )
    return path


def test_normalizes_files_by_logical_path_and_selects_entry_source(tmp_path: Path) -> None:
    spec = load_spec(_write_case(tmp_path, """  modules:
    entry: main.genia
    files:
      - path: zed.genia
        source: "value = 2\\n"
      - path: main.genia
        source: |
          import zed
          print("ok")
"""))
    assert spec.source == 'import zed\nprint("ok")\n'
    assert spec.module_entry == "main.genia"
    assert spec.module_files == (
        ("main.genia", 'import zed\nprint("ok")\n'),
        ("zed.genia", "value = 2\n"),
    )


@pytest.mark.parametrize("path", ["/main.genia", "../main.genia", "a/../main.genia", "C:/main.genia", "a\\main.genia", "a//main.genia", "main.txt"])
def test_rejects_nonportable_or_traversing_logical_paths(tmp_path: Path, path: str) -> None:
    with pytest.raises(ValueError, match="portable relative .genia path"):
        load_spec(_write_case(tmp_path, f"""  modules:
    entry: {json.dumps(path)}
    files:
      - path: {json.dumps(path)}
        source: "1\\n"
"""))


@pytest.mark.parametrize("input_yaml, message", [
    ("  source: '1'\n  modules: {}\n", "mutually exclusive"),
    ("  modules:\n    entry: main.genia\n    files: []\n", "entry must name"),
    ("  modules:\n    entry: main.genia\n    files:\n      - {path: main.genia, source: '1'}\n      - {path: main.genia, source: '2'}\n", "unique"),
    ("  modules:\n    entry: missing.genia\n    files:\n      - {path: main.genia, source: '1'}\n", "entry must name"),
])
def test_rejects_malformed_module_fixtures(tmp_path: Path, input_yaml: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        load_spec(_write_case(tmp_path, input_yaml))


def test_single_file_case_normalization_is_unchanged(tmp_path: Path) -> None:
    spec = load_spec(_write_case(tmp_path, "  source: 'print(\"ok\")'\n"))
    assert spec.source == 'print("ok")'
    assert spec.module_entry is None
    assert spec.module_files == ()


def test_subprocess_request_preserves_normalized_fixture_exactly(tmp_path: Path) -> None:
    spec = load_spec(_write_case(tmp_path, """  modules:
    entry: main.genia
    files:
      - {path: helper.genia, source: "value = 1\\n"}
      - path: main.genia
        source: |
          print("ok")
"""))
    request = build_host_request(spec)
    expected_modules = {
        "entry": "main.genia",
        "files": [
            {"path": "helper.genia", "source": "value = 1\n"},
            {"path": "main.genia", "source": 'print("ok")\n'},
        ],
    }
    assert request["input"]["modules"] == expected_modules
    assert json.loads(encode_request(request))["input"]["modules"] == expected_modules
    reconstructed = _spec_for_operation("eval", request["input"])
    assert reconstructed.module_entry == "main.genia"
    assert reconstructed.module_files == spec.module_files


def test_unmet_open_functions_capability_is_unsupported_before_adapter_invocation(tmp_path: Path) -> None:
    spec = load_spec(_write_case(tmp_path, """  modules:
    entry: main.genia
    files:
      - path: main.genia
        source: |
          print("ok")
""").with_name("fixture-case.yaml"))
    object.__setattr__(spec, "requires", ("open_functions",))
    result = execute_spec_via_host(spec, ["definitely-not-an-adapter"], timeout=1, host_capabilities={"open_functions": "unsupported"})
    assert result.kind == "unsupported"
    assert "open_functions" in (result.reason or "")
