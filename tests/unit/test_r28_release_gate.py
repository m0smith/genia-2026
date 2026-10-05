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
CONTRACT = REPO_ROOT / "docs" / "design" / "r28-genia-mcp-contract-threat-model.md"
NATIVE_SERVER = REPO_ROOT / "apps" / "mcp" / "mcp.genia"

REQUIRED_FIELDS = (
    "status",
    "executed_on",
    "vscode_version",
    "copilot_extension_version",
    "repository_revision",
    "failed_at",
    "workspace_trusted",
    "mcp_json_discovered",
    "server_state_shown",
    "negotiation_path",
    "negotiated_protocol_version",
    "host_log_excerpt",
    "tools_visible",
    "resources_or_prompts_visible",
    "parse_invoked_from_host",
    "invalid_source_feedback",
    "corrected_source_parsed",
    "run_invoked_from_host",
    "run_result",
    "channel_separation_visible",
    "clean_lifecycle_after_disconnect",
    "disposition",
)
EXPECTED_TOOLS = "genia_capabilities, genia_parse, genia_run"

# The acceptance steps in order. `failed_at` names the first step a failed run could not pass; every field
# of a later step must say `not reached` (a failed run may not claim a later success), and no field of the
# failing or an earlier step may.
STAGES = ("start", "initialize", "tools", "parse", "run", "disconnect")
FIELD_STAGE = {
    "workspace_trusted": "start",
    "mcp_json_discovered": "start",
    "server_state_shown": "start",
    "negotiation_path": "initialize",
    "negotiated_protocol_version": "initialize",
    "host_log_excerpt": "initialize",
    "tools_visible": "tools",
    "resources_or_prompts_visible": "tools",
    "parse_invoked_from_host": "parse",
    "invalid_source_feedback": "parse",
    "corrected_source_parsed": "parse",
    "run_invoked_from_host": "run",
    "run_result": "run",
    "channel_separation_visible": "run",
    "clean_lifecycle_after_disconnect": "disconnect",
}
NOT_REACHED = "not reached"
NOT_RECORDED = "not recorded"
SECRET_PATTERNS = (
    r"ghp_[A-Za-z0-9]{10,}",
    r"github_pat_",
    r"sk-[A-Za-z0-9]{10,}",
    r"[\w.+-]+@[\w-]+\.[\w.]+",
    r"/Users/\w+",
    r"/home/\w+",
    r"Bearer\s+\S+",
    r"BEGIN [A-Z ]*PRIVATE KEY",
)


def _contract_versions():
    """The supported protocol versions, read from the amended contract (section 18, A5.1)."""
    match = re.search(r"```supported-protocol-versions\n(.*?)```", CONTRACT.read_text(encoding="utf-8"), re.S)
    assert match, "the contract has no supported-protocol-versions block (amendment A5)"
    versions = dict(line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
    return {era.strip(): version.strip() for era, version in versions.items()}


def _allowed_paths():
    """The negotiation paths the amended contract permits: modern via server/discover, compat via initialize."""
    versions = _contract_versions()
    return {("server/discover", versions["modern"]), ("initialize", versions["compat"])}


def _parse_runs(text):
    runs = []
    for match in re.finditer(r"```evidence run=(\d+)\n(.*?)```", text, re.S):
        fields = {}
        for line in match.group(2).splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key, _, value = line.partition(":")
            fields[key.strip()] = re.sub(r"^#.*$|\s{2,}#.*$", "", value.strip()).strip()
        runs.append((int(match.group(1)), fields))
    return [fields for _, fields in sorted(runs, key=lambda item: item[0])]


def _runs():
    assert EVIDENCE.is_file(), "docs/mcp/acceptance/vscode-copilot-evidence.md is missing"
    return _parse_runs(EVIDENCE.read_text(encoding="utf-8"))


def _state(run):
    """not executed / failed / passed. Anything else is a malformed record."""
    if run.get("status") == "NOT EXECUTED":
        return "not executed"
    if run.get("status") == "EXECUTED" and run.get("disposition") == "FAIL":
        return "failed"
    if run.get("status") == "EXECUTED" and run.get("disposition") == "PASS":
        return "passed"
    return "malformed"


def _problems(run, allowed=None):
    """Everything wrong with one run record, by its state."""
    allowed = _allowed_paths() if allowed is None else allowed
    problems = []
    state = _state(run)
    for name in REQUIRED_FIELDS:
        if name not in run:
            problems.append(f"{name} is missing")
    if problems:
        return problems
    if state == "malformed":
        return ["status must be NOT EXECUTED, or EXECUTED with disposition PASS or FAIL"]
    if state == "not executed":
        return [f"{name} must be empty in a run that was not executed" for name in REQUIRED_FIELDS
                if name != "status" and run[name]]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", run["executed_on"]):
        problems.append("executed_on must be YYYY-MM-DD")
    if not run["vscode_version"] or not run["copilot_extension_version"]:
        problems.append("the VS Code and Copilot extension versions are required")
    if state == "passed":
        for name in REQUIRED_FIELDS:
            if not run[name] or run[name] in {NOT_REACHED, NOT_RECORDED}:
                problems.append(f"{name} must be a real observation in a passing run")
        if run["failed_at"] != "none":
            problems.append("a passing run has failed_at: none")
        if run["tools_visible"] != EXPECTED_TOOLS:
            problems.append("tools_visible must be exactly the three tools")
        if run["resources_or_prompts_visible"] != "none":
            problems.append("resources_or_prompts_visible must be none")
        for yes in ("workspace_trusted", "mcp_json_discovered", "parse_invoked_from_host",
                    "corrected_source_parsed", "run_invoked_from_host", "clean_lifecycle_after_disconnect"):
            if run[yes] != "yes":
                problems.append(f"{yes} must be yes")
        if (run["negotiation_path"], run["negotiated_protocol_version"]) not in allowed:
            problems.append("the negotiation path and protocol version must be one the contract supports")
        if not re.fullmatch(r"[0-9a-f]{40}", run["repository_revision"]):
            problems.append("repository_revision must be a 40-hex commit")
    else:  # failed
        if run["failed_at"] not in STAGES:
            problems.append(f"failed_at must be one of {STAGES}")
            return problems
        failed = STAGES.index(run["failed_at"])
        for name, stage in FIELD_STAGE.items():
            later = STAGES.index(stage) > failed
            if later and run[name] != NOT_REACHED:
                problems.append(f"{name} comes after the failure and must say {NOT_REACHED!r}")
            if not later and (not run[name] or run[name] == NOT_REACHED):
                problems.append(f"{name} was reached before the failure and must be recorded")
        if run["negotiation_path"] not in {"server/discover", "initialize", NOT_RECORDED}:
            problems.append("negotiation_path must be server/discover or initialize when reached")
    return problems


def _release_satisfied(runs, allowed=None):
    """The latest run governs: executed, complete, PASS, on a path the amended contract supports."""
    return bool(runs) and _state(runs[-1]) == "passed" and not _problems(runs[-1], allowed)


def _claims_complete(text):
    """Sentences in which R28 itself is called complete (a negated or conditional mention is not a claim)."""
    claims = []
    for line in text.splitlines():
        for match in re.finditer(r"R28", line):
            tail = re.split(r"[.;]", line[match.start(): match.start() + 90])[0]
            found = re.search(r"\bcomplete(d)?\b", tail, re.I)
            if not found:
                continue
            context = line[max(0, match.start() - 50): match.start()] + tail[: found.start()]
            if re.search(r"\bnot\b|until|only when|only after|before|incomplete|never|cannot|may not|must not|"
                         r"become|becomes|marked|\bmark\b|\bcall\b|\bclaims?\b|\bif\b|unless", context, re.I):
                continue
            claims.append(line.strip())
    return claims


AUTHORITATIVE = (STATE, README, ROADMAP, ROADMAP_R25, SEQUENCE, RELEASES_README, RELEASE_PAGE)


def test_the_evidence_record_keeps_every_run_in_order_and_every_required_field():
    runs = _runs()
    assert len(runs) >= 2, "run 1 (the failure) and run 2 (post-amendment) must both be recorded"
    for run in runs:
        assert set(REQUIRED_FIELDS) <= set(run)
        assert _state(run) != "malformed", run
        assert _problems(run) == [], _problems(run)


def test_run_1_is_preserved_as_the_authentic_failure_that_triggered_amendment_a5():
    run1 = _runs()[0]
    assert _state(run1) == "failed"
    assert (run1["executed_on"], run1["vscode_version"], run1["copilot_extension_version"]) == (
        "2026-10-05", "1.138.0", "0.66.0")
    assert (run1["failed_at"], run1["negotiation_path"], run1["negotiated_protocol_version"]) == (
        "initialize", "initialize", "none")
    assert run1["mcp_json_discovered"] == "yes" and run1["disposition"] == "FAIL"
    text = EVIDENCE.read_text(encoding="utf-8")
    assert '"method":"initialize"' in text and '"protocolVersion":"2025-11-25"' in text
    assert '"error":{"code":-32601,"message":"Method not found"}' in text  # the pre-amendment answer


def test_run_2_is_preserved_as_protocol_success_and_the_genia_run_failure_on_macos():
    run1, run2 = _runs()[:2]
    assert run1["failed_at"] == "initialize"  # run 1 is never rewritten by run 2
    assert _state(run2) == "failed" and run2["failed_at"] == "run" and run2["disposition"] == "FAIL"
    assert run2["repository_revision"] == "66b505949cb17a4a017291115efb8a1cc5970cab"
    assert (run2["negotiation_path"], run2["negotiated_protocol_version"]) == ("initialize", "2025-11-25")
    assert run2["tools_visible"] == "genia_capabilities, genia_parse, genia_run"
    assert "offset 171" in run2["invalid_source_feedback"] and run2["corrected_source_parsed"] == "yes"
    assert "internal_error" in run2["run_result"] and run2["run_result"].startswith("FAIL")
    assert run2["clean_lifecycle_after_disconnect"] == "not reached"
    assert not _release_satisfied(_runs()[:2])  # a failed latest run never releases


def test_the_gate_distinguishes_not_executed_failed_and_passed_runs():
    states = [_state(run) for run in _runs()]
    assert states[0] == "failed"
    assert states[-1] in {"not executed", "failed", "passed"}


def test_an_executed_passing_run_is_complete_secret_free_and_consistent():
    latest = _runs()[-1]
    if _state(latest) != "passed":
        pytest.skip("the post-amendment VS Code/Copilot run has not passed (ledger R28-H39 is open)")
    text = EVIDENCE.read_text(encoding="utf-8")
    for pattern in SECRET_PATTERNS:
        assert not re.search(pattern, text), f"the evidence record must not contain {pattern!r}"


def test_a_not_executed_latest_run_has_blank_fields():
    latest = _runs()[-1]
    if _state(latest) != "not executed":
        pytest.skip("executed")
    assert _problems(latest) == []


def test_no_authoritative_document_claims_r28_complete_unless_the_evidence_allows_it():
    runs = _runs()
    claims = {path.name: _claims_complete(path.read_text(encoding="utf-8")) for path in AUTHORITATIVE
              if path.exists()}
    claims = {name: found for name, found in claims.items() if found}
    if _release_satisfied(runs):
        return  # the completion synchronization is allowed (it is a separate, reviewed change)
    assert claims == {}, f"R28 is claimed complete without the VS Code/Copilot evidence: {claims}"


def test_the_release_page_states_its_real_status():
    assert RELEASE_PAGE.is_file()
    text = RELEASE_PAGE.read_text(encoding="utf-8")
    first = next(line for line in text.splitlines() if line.startswith("Status:"))
    if _release_satisfied(_runs()):
        assert "Complete" in first or "Release Candidate" in first
    else:
        assert "Release Candidate" in first and "not complete" in first.lower(), first


def test_the_release_page_covers_every_required_topic():
    text = RELEASE_PAGE.read_text(encoding="utf-8").lower()
    for topic in ("release purpose", "architecture", "exactly three tools", "stdio", "governed execution",
                  "client integration", "conformance evidence", "demo", "security", "limitations",
                  "host portability", "out of scope", "verification evidence", "vs code"):
        assert topic in text, f"docs/releases/R28.md must cover {topic!r}"


def test_the_ledger_keeps_h39_and_h47_open_until_the_evidence_is_released():
    ledger = LEDGER.read_text(encoding="utf-8")
    parts = dict(re.findall(r"(?ms)^\*\*(R28-H\d{2}) — (.*?)(?=^\*\*R28-H|\Z)", ledger))
    status = {entry: re.search(r"Status: `(\w+)`", parts[entry]).group(1) for entry in ("R28-H36", "R28-H39", "R28-H47")}
    if not _release_satisfied(_runs()):
        assert status["R28-H39"] == "open", "H39 must stay open until the VS Code/Copilot evidence passes"
        assert status["R28-H47"] == "open", "H47 must stay open until macOS governed execution is verified"
    # H36 (protocol compatibility) may close only on authentic evidence that VS Code negotiated and listed tools.
    if status["R28-H36"] == "closed":
        proof = [r for r in _runs() if r["negotiated_protocol_version"] in {"2025-11-25", "2026-07-28"}
                 and r["tools_visible"] == "genia_capabilities, genia_parse, genia_run"]
        assert proof, "H36 closed without a run that negotiated and discovered the three tools"


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


# --- the gate itself, mutation-tested permanently (pure functions over synthetic run records) ----------


def _passing_run(**changes):
    run = {
        "status": "EXECUTED",
        "executed_on": "2026-10-06",
        "vscode_version": "1.138.0",
        "copilot_extension_version": "0.66.0",
        "repository_revision": "a" * 40,
        "failed_at": "none",
        "workspace_trusted": "yes",
        "mcp_json_discovered": "yes",
        "server_state_shown": "Running",
        "negotiation_path": "initialize",
        "negotiated_protocol_version": "2025-11-25",
        "host_log_excerpt": "initialize ok",
        "tools_visible": EXPECTED_TOOLS,
        "resources_or_prompts_visible": "none",
        "parse_invoked_from_host": "yes",
        "invalid_source_feedback": "parse_error at character offset 171",
        "corrected_source_parsed": "yes",
        "run_invoked_from_host": "yes",
        "run_result": "value, stdout 2, stderr two lines, exit code 0",
        "channel_separation_visible": "yes",
        "clean_lifecycle_after_disconnect": "yes",
        "disposition": "PASS",
    }
    run.update(changes)
    return run


def _failed_run(failed_at="initialize", **changes):
    run = _passing_run(status="EXECUTED", disposition="FAIL", failed_at=failed_at)
    failed = STAGES.index(failed_at)
    for name, stage in FIELD_STAGE.items():
        if STAGES.index(stage) > failed:
            run[name] = NOT_REACHED
    run.update(changes)
    return run


def _blank_run():
    return {name: "" for name in REQUIRED_FIELDS} | {"status": "NOT EXECUTED"}


MODERN = ("server/discover", "2026-07-28")
COMPAT = ("initialize", "2025-11-25")


def test_the_allowed_negotiation_paths_derive_from_the_amended_contract():
    assert _contract_versions() == {"modern": "2026-07-28", "compat": "2025-11-25"}
    assert _allowed_paths() == {MODERN, COMPAT}


def test_the_native_server_implements_exactly_the_versions_the_contract_names():
    text = NATIVE_SERVER.read_text(encoding="utf-8")
    versions = _contract_versions()
    assert f'PROTOCOL_VERSION = "{versions["modern"]}"' in text
    assert f'COMPAT_PROTOCOL_VERSION = "{versions["compat"]}"' in text
    assert set(re.findall(r'"(20\d\d-\d\d-\d\d)"', text)) == set(versions.values())  # no third version


def test_a_passing_run_over_either_supported_path_satisfies_the_gate():
    assert _problems(_passing_run()) == []
    assert _release_satisfied([_failed_run(), _passing_run()])
    modern = _passing_run(negotiation_path="server/discover", negotiated_protocol_version="2026-07-28")
    assert _problems(modern) == [] and _release_satisfied([modern])


@pytest.mark.parametrize(
    "mutation",
    [
        {"tools_visible": "genia_capabilities, genia_parse"},
        {"tools_visible": "genia_capabilities, genia_parse, genia_run, genia_extra"},
        {"resources_or_prompts_visible": "resources: 1"},
        {"negotiation_path": "initialize", "negotiated_protocol_version": "2026-07-28"},
        {"negotiation_path": "server/discover", "negotiated_protocol_version": "2025-11-25"},
        {"negotiation_path": "initialize", "negotiated_protocol_version": "2025-06-18"},
        {"negotiation_path": "anything-that-connects", "negotiated_protocol_version": "2025-11-25"},
        {"parse_invoked_from_host": "no"},
        {"corrected_source_parsed": "no"},
        {"run_invoked_from_host": "no"},
        {"clean_lifecycle_after_disconnect": "no"},
        {"mcp_json_discovered": "no"},
        {"run_result": NOT_REACHED},
        {"host_log_excerpt": NOT_RECORDED},
        {"repository_revision": "not recorded"},
        {"failed_at": "initialize"},
        {"disposition": "FAIL"},
        {"executed_on": "yesterday"},
        {"vscode_version": ""},
    ],
    ids=lambda m: ",".join(f"{k}={v}" for k, v in m.items()),
)
def test_a_passing_run_that_fails_any_acceptance_requirement_does_not_satisfy_the_gate(mutation):
    run = _passing_run(**mutation)
    assert not (_state(run) == "passed" and _problems(run) == [] and _release_satisfied([run]))


def test_a_pass_on_the_legacy_path_needs_the_contract_to_allow_it():
    # Mutation: if the contract supported only the modern era, an initialize run could not satisfy the gate.
    only_modern = {MODERN}
    assert _problems(_passing_run(), allowed=only_modern)
    assert not _release_satisfied([_passing_run()], allowed=only_modern)


def test_the_latest_run_governs_the_release():
    assert not _release_satisfied([_passing_run(), _failed_run()])  # a later failure reopens the gate
    assert not _release_satisfied([_passing_run(), _blank_run()])
    assert not _release_satisfied([_failed_run(), _blank_run()])
    assert not _release_satisfied([])


def test_a_failed_run_cannot_claim_success_after_its_failure_point():
    assert _problems(_failed_run()) == []
    assert _problems(_failed_run("tools")) == []
    assert any("must say" in p for p in _problems(_failed_run(tools_visible=EXPECTED_TOOLS)))
    assert any("must be recorded" in p for p in _problems(_failed_run(negotiation_path=NOT_REACHED)))
    assert _problems(_failed_run() | {"failed_at": "nowhere"})


def test_a_not_executed_run_must_be_blank_and_a_malformed_status_is_rejected():
    assert _problems(_blank_run()) == []
    assert _problems(_blank_run() | {"vscode_version": "1.138.0"})
    assert _state(_blank_run() | {"status": "DONE"}) == "malformed"
    assert _state(_passing_run(disposition="MAYBE")) == "malformed"
    states = {_state(_blank_run()), _state(_failed_run()), _state(_passing_run())}
    assert states == {"not executed", "failed", "passed"}


def test_a_passing_record_with_a_secret_is_detected():
    sample = "token ghp_" + "a" * 20
    assert any(re.search(pattern, sample) for pattern in SECRET_PATTERNS)
    assert any(re.search(pattern, "path /Users/someone/x") for pattern in SECRET_PATTERNS)
