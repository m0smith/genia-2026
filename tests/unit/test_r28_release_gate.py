"""R28 E28-6 (issue #707): the release-completion gate.

R28 may be called Complete only when contract section 12.2 is satisfied by an authentic VS Code +
GitHub Copilot run (ledger R28-H39), which also decides R28-H36. This module makes that rule
mechanical so it cannot be forgotten and cannot be bypassed by wording:

* the evidence record `docs/mcp/acceptance/vscode-copilot-evidence.md` has a fixed machine-checkable
  shape;
* while it is not fully executed (or the host negotiated the legacy handshake), no authoritative
  document may claim R28 is complete, the release page must say Release Candidate, and H36/H39 stay
  open in the ledger;
* if it is executed, it must be complete, secret-free, and internally consistent;
* the roadmap keeps the R20 follow-up (#1067) after R28 and before R29.

Documentation-consistency tests of the Python-host test suite; no runtime behavior.
"""

from __future__ import annotations

import re

import pytest

from tests.fixtures.r28_mcp_helpers import REPO_ROOT

pytestmark = pytest.mark.unit

EVIDENCE = REPO_ROOT / "docs" / "mcp" / "acceptance" / "vscode-copilot-evidence.md"
RELEASE_PAGE = REPO_ROOT / "docs" / "releases" / "R28.md"
RELEASES_README = REPO_ROOT / "docs" / "releases" / "README.md"
ROADMAP = REPO_ROOT / "docs" / "strategy" / "release-roadmap.md"
ROADMAP_R25 = REPO_ROOT / "docs" / "strategy" / "roadmap" / "r25-r29.md"
SEQUENCE = REPO_ROOT / "docs" / "strategy" / "roadmap" / "sequence.md"
STATE = REPO_ROOT / "GENIA_STATE.md"
README = REPO_ROOT / "README.md"
LEDGER = REPO_ROOT / "docs" / "analysis" / "r28-host-dependency-inventory.md"

REQUIRED_FIELDS = (
    "status",
    "executed_on",
    "vscode_version",
    "copilot_extension_version",
    "repository_revision",
    "workspace_trusted",
    "mcp_json_discovered",
    "server_state_shown",
    "tools_visible",
    "resources_or_prompts_visible",
    "parse_invoked_from_host",
    "invalid_source_feedback",
    "corrected_source_parsed",
    "run_invoked_from_host",
    "run_result",
    "channel_separation_visible",
    "negotiation_path",
    "clean_lifecycle_after_disconnect",
    "host_log_excerpt",
    "disposition",
)
EXPECTED_TOOLS = "genia_capabilities, genia_parse, genia_run"


def _record():
    text = EVIDENCE.read_text(encoding="utf-8")
    match = re.search(r"```evidence\n(.*?)```", text, re.S)
    assert match, "the evidence record has no ```evidence block"
    fields = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def _executed(fields):
    return fields.get("status") == "EXECUTED"


def _complete_and_clean(fields):
    problems = []
    for name in REQUIRED_FIELDS:
        if not fields.get(name):
            problems.append(f"{name} is empty")
    if fields.get("tools_visible") != EXPECTED_TOOLS:
        problems.append("tools_visible must be exactly the three tools")
    if fields.get("resources_or_prompts_visible") != "none":
        problems.append("resources_or_prompts_visible must be none")
    if fields.get("negotiation_path") not in {"server/discover", "initialize"}:
        problems.append("negotiation_path must be server/discover or initialize")
    if fields.get("disposition") not in {"PASS", "FAIL"}:
        problems.append("disposition must be PASS or FAIL")
    for yes in ("workspace_trusted", "mcp_json_discovered", "parse_invoked_from_host",
                "corrected_source_parsed", "run_invoked_from_host", "clean_lifecycle_after_disconnect"):
        if fields.get(yes) != "yes":
            problems.append(f"{yes} must be yes")
    return problems


def _release_satisfied(fields):
    """True only for an executed, complete, passing run whose host negotiated the modern protocol."""
    return (
        _executed(fields)
        and not _complete_and_clean(fields)
        and fields.get("disposition") == "PASS"
        and fields.get("negotiation_path") == "server/discover"
    )


def _claims_complete(text):
    """Lines that call R28 complete (a negated or conditional mention is not a claim)."""
    claims = []
    for line in text.splitlines():
        if "R28" not in line:
            continue
        for match in re.finditer(r"\bcomplete(d)?\b", line, re.I):
            before = line[max(0, match.start() - 40): match.start()].lower()
            if re.search(r"\bnot\b|\bis not\b|until|only when|only after|before|incomplete|never|cannot|"
                         r"may not|must not|become|becomes|marked", before):
                continue
            claims.append(line.strip())
    return claims


AUTHORITATIVE = (STATE, README, ROADMAP, ROADMAP_R25, SEQUENCE, RELEASES_README, RELEASE_PAGE)


def test_the_evidence_record_exists_with_every_required_field():
    assert EVIDENCE.is_file(), "docs/mcp/acceptance/vscode-copilot-evidence.md is missing"
    fields = _record()
    assert set(REQUIRED_FIELDS) <= set(fields)
    assert fields["status"] in {"NOT EXECUTED", "EXECUTED"}


def test_an_executed_record_is_complete_secret_free_and_consistent():
    fields = _record()
    if not _executed(fields):
        pytest.skip("the VS Code/Copilot run has not been executed (ledger R28-H39 is open)")
    assert _complete_and_clean(fields) == []
    text = EVIDENCE.read_text(encoding="utf-8")
    for pattern in (r"ghp_[A-Za-z0-9]{10,}", r"github_pat_", r"sk-[A-Za-z0-9]{10,}", r"[\w.+-]+@[\w-]+\.[\w.]+",
                    r"/Users/\w+", r"/home/\w+", r"Bearer\s+\S+", r"BEGIN [A-Z ]*PRIVATE KEY"):
        assert not re.search(pattern, text), f"the evidence record must not contain {pattern!r}"
    assert re.fullmatch(r"[0-9a-f]{40}", fields["repository_revision"])


def test_a_not_executed_record_has_blank_run_fields_and_says_so():
    fields = _record()
    if _executed(fields):
        pytest.skip("executed")
    assert fields["disposition"] in {"", "NOT EXECUTED"}
    assert fields["vscode_version"] == "" and fields["copilot_extension_version"] == ""


def test_no_authoritative_document_claims_r28_complete_unless_the_evidence_allows_it():
    fields = _record()
    claims = {path.name: _claims_complete(path.read_text(encoding="utf-8")) for path in AUTHORITATIVE
              if path.exists()}
    claims = {name: found for name, found in claims.items() if found}
    if _release_satisfied(fields):
        return  # the completion synchronization is allowed (it is a separate, reviewed change)
    assert claims == {}, f"R28 is claimed complete without the VS Code/Copilot evidence: {claims}"


def test_the_release_page_states_its_real_status():
    assert RELEASE_PAGE.is_file()
    text = RELEASE_PAGE.read_text(encoding="utf-8")
    first = next(line for line in text.splitlines() if line.startswith("Status:"))
    if _release_satisfied(_record()):
        assert "Complete" in first or "Release Candidate" in first
    else:
        assert "Release Candidate" in first and "not complete" in first.lower(), first


def test_the_release_page_covers_every_required_topic():
    text = RELEASE_PAGE.read_text(encoding="utf-8").lower()
    for topic in ("release purpose", "architecture", "exactly three tools", "stdio", "governed execution",
                  "client integration", "conformance evidence", "demo", "security", "limitations",
                  "host portability", "out of scope", "verification evidence", "vs code"):
        assert topic in text, f"docs/releases/R28.md must cover {topic!r}"


def test_the_ledger_keeps_h36_and_h39_open_until_the_evidence_is_released():
    ledger = LEDGER.read_text(encoding="utf-8")
    parts = dict(re.findall(r"(?ms)^\*\*(R28-H\d{2}) — (.*?)(?=^\*\*R28-H|\Z)", ledger))
    for entry in ("R28-H36", "R28-H39"):
        status = re.search(r"Status: `(\w+)`", parts[entry]).group(1)
        if _release_satisfied(_record()):
            continue
        assert status == "open", f"{entry} must stay open until the VS Code/Copilot evidence passes"


def test_every_non_closed_ledger_entry_has_a_recorded_final_disposition():
    ledger = LEDGER.read_text(encoding="utf-8")
    entries = dict(re.findall(r"(?ms)^\*\*(R28-H\d{2}) — (.*?)(?=^\*\*R28-H|^### |\Z)", ledger))
    assert len(entries) >= 43
    for entry, body in entries.items():
        if "Status: `closed`" in body:
            continue
        assert "E28-6 final disposition:" in body, f"{entry} lacks the E28-6 final disposition"


def test_the_r20_followup_stays_after_r28_and_before_r29():
    text = ROADMAP.read_text(encoding="utf-8")
    assert re.search(r"#1067[^\n]*after R28 and before R29", text)
    assert text.index("**R28 — Genia MCP Server**") < text.index("issue #1067; unnumbered") < text.index("**R29")
    sequence = SEQUENCE.read_text(encoding="utf-8")
    assert "Issue #1067 is scheduled after R28 and before R29" in sequence
