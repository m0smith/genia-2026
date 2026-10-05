"""R28 E28-6 (issue #707): the canonical validated-record-pipeline demo over MCP.

The demo is ordinary, already-implemented Genia (`validate_record`, `validate_each`,
`collect_validated`). These Python-host tests drive it through the real launcher exactly as a
client would (`genia_parse` on the broken program, repair, `genia_parse`, `genia_run`) and check
that the public walkthrough `docs/mcp/demo.md` quotes the example files and the real results.
They add no Genia semantics.
"""

from __future__ import annotations

import json
import re

import pytest

from tests.fixtures.r28_mcp_conformance import (
    assert_closed_failure,
    assert_completed,
    direct_command_source,
    launcher_batch,
    parse_sources,
    run_sources,
)
from tests.fixtures.r28_mcp_helpers import REPO_ROOT, RUN_TOOLS, request

pytestmark = pytest.mark.unit

EXAMPLES = REPO_ROOT / "examples" / "mcp"
FIXED = EXAMPLES / "validated_records.genia"
BROKEN = EXAMPLES / "validated_records_broken.genia"
DEMO_DOC = REPO_ROOT / "docs" / "mcp" / "demo.md"

# The tokens a first-time user must never need: internal modules, issue numbers, ledger ids.
INTERNAL_TOKENS = ("hosts/python", "mcp_worker", "mcp_host", "supervisor", "E28-", "R28-H", "#70", "fixture")


def _body(path):
    """The program text after the file's documentation header (what the demo pastes)."""
    text = path.read_text(encoding="utf-8")
    start = text.index('"""', text.index('"""') + 3) + 3
    return text[start:].lstrip("\n")


def _block(label):
    doc = DEMO_DOC.read_text(encoding="utf-8")
    match = re.search(rf"```[a-z]*\s+{re.escape(label)}\n(.*?)```", doc, re.S)
    assert match, f"docs/mcp/demo.md has no block labeled {label!r}"
    return match.group(1)


def test_the_example_files_exist_with_the_required_header_structure():
    for path in (FIXED, BROKEN):
        text = path.read_text(encoding="utf-8")
        assert text.count('"""') >= 2 and "## Run" in text and "## Features Demonstrated" in text


def test_the_documented_sources_are_exactly_the_example_programs():
    assert _block("demo-broken").strip() == _body(BROKEN).strip()
    assert _block("demo-fixed").strip() == _body(FIXED).strip()


def test_the_broken_program_gets_a_structured_diagnostic_at_the_defect():
    ((response, envelope),) = parse_sources([_body(BROKEN)])
    message = envelope["error"]["message"]
    offset = int(message.rsplit(" ", 1)[1])
    body = _body(BROKEN)
    assert_closed_failure(response, "parse_error", "parse", message)
    # the offset lands on the line that holds the dangling operator, not somewhere unrelated
    assert "&&" in body.splitlines()[body[:offset].count("\n")]
    assert f"character offset {offset}" in DEMO_DOC.read_text(encoding="utf-8")


def test_the_repaired_program_parses_runs_and_matches_direct_evaluation():
    source = _body(FIXED)
    ((_, parsed),) = parse_sources([source])
    assert parsed["status"] == "ok" and parsed["result"]["kind"] == "parsed"
    ((response, _),) = run_sources([source])
    result = assert_completed(response)
    rendered, stdout, stderr = direct_command_source(source)
    assert (result["value"]["rendered"], result["stdout"], result["stderr"]) == (rendered, stdout, stderr)


def test_the_run_separates_value_stdout_and_stderr_as_documented():
    ((response, _),) = run_sources([_body(FIXED)])
    result = assert_completed(response)
    assert result["stdout"] == "2\n"  # the clean-record count
    assert result["stderr"] == "record_validation_failed\n" * 2  # one reason per invalid record
    assert result["exit_code"] == 0
    assert result["value"]["rendered"].startswith("{clean: [")
    assert _block("demo-value").strip() == result["value"]["rendered"]
    assert _block("demo-stdout") == result["stdout"]
    assert _block("demo-stderr") == result["stderr"]


def test_the_validation_outcome_is_structured_data_in_the_value():
    ((response, _),) = run_sources([_body(FIXED)])
    rendered = assert_completed(response)["value"]["rendered"]
    # clean records are preserved with every validated field; each bad record has a diagnostic
    assert '{id: 1, name: "Ada", age: 36}' in rendered and '{id: 4, name: "Edsger", age: 72}' in rendered
    assert "index: 1" in rendered and "index: 2" in rendered
    assert '"missing required field"' in rendered and "age between 0 and 150" in rendered


def test_the_demo_is_deterministic_across_launches():
    source = _body(FIXED)
    first = run_sources([source])[0][1]
    second = run_sources([source, source])
    assert first == second[0][1] == second[1][1]


def test_the_whole_walkthrough_works_in_one_session():
    messages = [
        request("tools/list", 1),
        request("tools/call", 2, {"name": "genia_parse", "arguments": {"source": _body(BROKEN)}}),
        request("tools/call", 3, {"name": "genia_parse", "arguments": {"source": _body(FIXED)}}),
        request("tools/call", 4, {"name": "genia_run", "arguments": {"source": _body(FIXED)}}),
    ]
    _, out = launcher_batch(messages)
    assert [t["name"] for t in out[0]["result"]["tools"]] == list(RUN_TOOLS)
    assert out[1]["result"]["structuredContent"]["error"]["kind"] == "parse_error"
    assert out[2]["result"]["structuredContent"]["status"] == "ok"
    assert out[3]["result"]["structuredContent"]["result"]["kind"] == "completed"


def test_the_demo_uses_no_authority_the_governed_profile_denies():
    from hosts.python.mcp_worker_profile import DENIED_NAMES

    names = set(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", _body(FIXED)))
    assert not (names & set(DENIED_NAMES))
    assert "import" not in names


def test_the_walkthrough_is_self_contained_for_a_first_time_user():
    text = DEMO_DOC.read_text(encoding="utf-8")
    for needed in ("Prerequisites", "genia_capabilities", "genia_parse", "genia_run", "Troubleshooting",
                   "versionNegotiation", "scripts/genia-mcp", "uv", "git"):
        assert needed in text, needed
    for token in INTERNAL_TOKENS:
        assert token not in text, f"the walkthrough must not require repository-internal knowledge: {token}"
    assert "Windows" in text and "Linux" in text  # platform statement is explicit
    assert json.loads(json.dumps({"ok": True}))  # keep json imported for block parsing helpers
