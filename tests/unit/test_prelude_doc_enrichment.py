"""Regression guard for the bounded issue #663 prelude documentation sweep."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent.parent
PRELUDE = REPO / "src" / "genia" / "std" / "prelude"
sys.path.insert(0, str(REPO / "tools"))

from lint_doc import _extract_docs_from_file, parse_doc  # noqa: E402


# True means the public callable accepts at least one caller-visible argument.
CANDIDATE_BINDINGS: dict[str, dict[str, bool]] = {
    "json": {
        "json_parse": True,
        "json_decode": True,
        "json_schema": True,
        "parse_jsonl_record": True,
        "parse_csv_row": True,
        "json_stringify": True,
        "json_encode": True,
        "json_pretty": True,
    },
    "random": {
        "rng": True,
        "rand": True,
        "rand_int": True,
        "rand_flow": True,
        "rand_int_flow": True,
    },
    "ref": {
        "ref": True,
        "ref_get": True,
        "ref_set": True,
        "ref_is_set": True,
        "ref_update": True,
    },
    "io": {
        "write": True,
        "writeln": True,
        "flush": True,
        "clear_screen": False,
        "move_cursor": True,
        "render_grid": True,
    },
    "eval": {
        "empty_env": False,
        "lookup": True,
        "define": True,
        "set": True,
        "extend": True,
        "eval": True,
    },
    "cli": {
        "cli_parse": True,
        "cli_flag?": True,
        "cli_option": True,
        "cli_option_or": True,
    },
    "awk": {
        "fields": True,
        "awkify": True,
        "awk_filter": True,
        "awk_map": True,
        "awk_count": True,
    },
    "file": {
        "read_file": True,
        "write_file": True,
        "zip_read": True,
        "zip_write": True,
    },
    "process": {
        "spawn": True,
        "send": True,
        "process_alive?": True,
        "process_failed?": True,
        "process_error": True,
    },
    "resource": {
        "resource_ref": True,
        "discover": True,
        "read_text": True,
        "read_bytes": True,
        "write_text": True,
        "write_bytes": True,
        "delete": True,
        "copy": True,
        "resource_meta": True,
        "resource_capabilities": False,
    },
    "web": {
        "serve_http": True,
        "route": True,
        "get": True,
        "post": True,
        "route_request": True,
        "response": True,
        "with_headers": True,
        "cors": True,
        "json": True,
        "text": True,
        "ok": True,
        "ok_text": True,
        "bad_request": True,
        "not_found": False,
    },
}


@pytest.mark.parametrize("module", CANDIDATE_BINDINGS)
def test_candidate_public_docs_have_structured_contract_sections(module: str):
    path = PRELUDE / f"{module}.genia"
    docs = {
        item["binding"]: parse_doc(item["text"])
        for item in _extract_docs_from_file(str(path))
        if item["binding"] is not None
    }
    failures: list[str] = []

    for name, has_arguments in CANDIDATE_BINDINGS[module].items():
        doc = docs.get(name)
        if doc is None:
            failures.append(f"{name}: missing canonical @doc")
            continue
        if has_arguments and "## Arguments" not in doc.sections:
            failures.append(f"{name}: missing ## Arguments")
        if "## Returns" not in doc.sections:
            failures.append(f"{name}: missing ## Returns")

    assert not failures, f"{path.relative_to(REPO)}:\n" + "\n".join(failures)
