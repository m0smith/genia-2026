"""R28 E28-2 (issue #703): the narrow host parse capability.

`hosts/python/mcp_parse_capability.parse_source(source) -> str` wraps the existing
`parse_adapter.parse_and_normalize` unchanged and returns closed JSON text. It
carries no MCP literal, envelope, or raw host text (ledger R28-H17). Expected to fail
until E28-2 lands.
"""

from __future__ import annotations

import ast
import importlib
import json

import pytest

from hosts.python.parse_adapter import parse_and_normalize
from tests.fixtures.r28_mcp_helpers import CAPABILITY_PATH, HOST_BOOTSTRAP_PATH

pytestmark = pytest.mark.unit


def _capability():
    assert CAPABILITY_PATH.is_file(), (
        "E28-2 not implemented: hosts/python/mcp_parse_capability.py does not exist"
    )
    return importlib.import_module("hosts.python.mcp_parse_capability")


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def test_success_returns_the_unchanged_normalized_ast():
    reply = json.loads(_capability().parse_source("x = 1"))
    assert reply == {"status": "parsed", "ast": parse_and_normalize("x = 1")["ast"]}


def test_syntax_error_returns_only_the_offset():
    reply = json.loads(_capability().parse_source("f(x) = x | SENTINEL ="))
    assert set(reply) == {"status", "offset"}
    assert reply["status"] == "syntax_error"
    assert isinstance(reply["offset"], int)


def test_syntax_error_without_position_has_null_offset():
    source = "pattern Between(lo, hi) = some(lo)"  # spec: arity error without ' at N'
    assert " at " not in parse_and_normalize(source)["message"]
    assert json.loads(_capability().parse_source(source)) == {
        "status": "syntax_error",
        "offset": None,
    }


def test_any_other_failure_is_internal_error_without_host_text(monkeypatch):
    capability = _capability()

    def boom(source):
        raise RuntimeError("SECRET-HOST-DETAIL /etc/passwd")

    monkeypatch.setattr(capability, "parse_and_normalize", boom)
    text = capability.parse_source("x = 1")
    assert json.loads(text) == {"status": "internal_error"}
    assert "SECRET" not in text and "RuntimeError" not in text


def test_recursion_failure_is_internal_error():
    reply = json.loads(_capability().parse_source("(" * 3000 + "1" + ")" * 3000))
    assert reply == {"status": "internal_error"}


def test_reply_is_single_line_json_text():
    text = _capability().parse_source("x = 1\ny = 2")
    assert isinstance(text, str) and "\n" not in text


def test_capability_and_bootstrap_import_only_narrow_dependencies():
    assert CAPABILITY_PATH.is_file() and HOST_BOOTSTRAP_PATH.is_file(), (
        "E28-2 not implemented: capability or host bootstrap missing"
    )
    capability_imports = _imports(CAPABILITY_PATH)
    assert capability_imports <= {"__future__", "json", "re", "hosts"}, capability_imports
    bootstrap_imports = _imports(HOST_BOOTSTRAP_PATH)
    assert "json" not in bootstrap_imports  # the bootstrap never builds JSON
    assert bootstrap_imports <= {"__future__", "sys", "pathlib", "genia", "hosts"}, (
        bootstrap_imports
    )
