from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
HANDOFF_DIR = (
    REPO
    / ".genia"
    / "process"
    / "tmp"
    / "handoffs"
    / "issue-456-r4-lifecycle-truth-audit-follow-up-triage"
)
AUDIT_HANDOFF = HANDOFF_DIR / "03-audit.md"


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def read_audit_handoff() -> str:
    if not AUDIT_HANDOFF.exists():
        pytest.fail(
            "issue #456 audit/triage handoff must exist at "
            ".genia/process/tmp/handoffs/"
            "issue-456-r4-lifecycle-truth-audit-follow-up-triage/03-audit.md"
        )
    return AUDIT_HANDOFF.read_text(encoding="utf-8")


def assert_contains_all(text: str, excerpts: list[str]) -> None:
    normalized = normalize(text)
    for excerpt in excerpts:
        assert normalize(excerpt) in normalized, (
            "issue #456 audit/triage handoff is missing required text: "
            f"{excerpt}"
        )


def test_issue_456_audit_handoff_exists_at_approved_path() -> None:
    text = read_audit_handoff()

    assert text.strip(), "issue #456 audit/triage handoff must not be empty"


def test_issue_456_audit_handoff_has_required_sections() -> None:
    text = read_audit_handoff()

    required_sections = [
        "## 0. Branch / scope confirmation",
        "## 1. Sources read",
        "## 2. Commands run",
        "## 3. Audit verdict",
        "## 5. Source-of-truth check",
        "## 6. Lifecycle docs truth check",
        "## 7. Test/doc guardrail check",
        "## 8. R4 scope-slip check",
        "## 9. Issue triage table",
        "## 10. Findings ledger",
        "## 12. R4 follow-ups",
        "## 14. Recommended issue actions, not performed",
    ]
    assert_contains_all(text, required_sections)


def test_issue_456_audit_verdict_uses_approved_label() -> None:
    text = read_audit_handoff()

    verdict_match = re.search(
        r"(?im)^\s*(?:verdict|audit verdict)\s*:\s*(PASS|PASS WITH ISSUES|FAIL)\s*$",
        text,
    )
    assert verdict_match, (
        "issue #456 audit/triage handoff must record an audit verdict as one of: "
        "PASS, PASS WITH ISSUES, FAIL"
    )


def test_issue_456_issue_triage_distinguishes_closure_and_follow_up_candidates() -> None:
    text = read_audit_handoff()

    assert_contains_all(
        text,
        [
            "| Issue | State | Title | Classification | Recommended action | Rationale | Action taken? |",
            "obsolete/close candidate",
            "R4 follow-up",
            "post-R4 deferred",
            "completed/no action",
            "needs operator decision",
            "close as completed",
            "close as not planned",
            "create small follow-up issue",
            "NO",
        ],
    )


def test_issue_456_findings_use_evidence_and_action_schema() -> None:
    text = read_audit_handoff()

    assert re.search(r"(?m)^### Finding F-\d{2} ", text), (
        "issue #456 audit/triage handoff must include at least one findings-ledger "
        "entry using the stable 'Finding F-NN' schema"
    )
    assert_contains_all(
        text,
        [
            "Severity:",
            "Classification:",
            "Source(s):",
            "Problem:",
            "Evidence:",
            "Why it matters:",
            "Minimal fix or recommendation:",
            "Action performed: NO",
        ],
    )


def test_issue_456_audit_cites_authoritative_evidence_sources() -> None:
    text = read_audit_handoff()

    assert_contains_all(
        text,
        [
            "GENIA_STATE.md",
            "GENIA_RULES.md",
            "docs/architecture/lifecycle.md",
            "docs/architecture/execution-mode-lifecycle.md",
            "tests/doc/test_semantic_doc_sync.py",
            "#455",
            "#456",
        ],
    )

    evidence_markers = [
        "authoritative-state",
        "rules-invariant",
        "architecture-doc",
        "test-guardrail",
        "issue-state",
    ]
    assert any(normalize(marker) in normalize(text) for marker in evidence_markers), (
        "issue #456 audit/triage handoff must cite evidence with stable source "
        "types, not only broad prose"
    )


def test_issue_456_audit_preserves_lifecycle_non_behavior_boundaries() -> None:
    text = read_audit_handoff()

    assert_contains_all(
        text,
        [
            "GENIA_STATE.md",
            "final authority",
            "not implemented",
            "proposal",
            "no lifecycle runner",
            "execution-mode lifecycle",
            "proposal documentation",
        ],
    )

    forbidden_claims = [
        r"\bimplemented lifecycle system\b",
        r"\bgeneralized lifecycle runner is implemented\b",
        r"\bexecution-mode lifecycle runner exists\b",
        r"\bGenia runs lifecycle phases\b",
        r"\bannotations run setup/teardown hooks\b",
        r"\b@setup runs automatically\b",
        r"\b@teardown runs automatically\b",
    ]
    allowed_context = re.compile(
        r"not implemented|not current|no |does not|must not|proposal|proposed|future",
        re.IGNORECASE,
    )
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern in forbidden_claims:
            if re.search(pattern, line, flags=re.IGNORECASE):
                assert allowed_context.search(line), (
                    "issue #456 audit/triage handoff must not claim new implemented "
                    f"lifecycle behavior at line {line_number}: {line.strip()!r}"
                )


def test_issue_456_audit_does_not_instruct_automatic_github_mutation() -> None:
    text = read_audit_handoff()

    assert_contains_all(
        text,
        [
            "Recommended issue actions, not performed",
            "Action performed: NO",
            "operator approval",
        ],
    )
    forbidden_mutations = [
        r"\bclosed issue #\d+",
        r"\bcreated issue #\d+",
        r"\brelabel(?:ed)? issue #\d+",
        r"\bcommented on issue #\d+",
        r"\bAction taken\?\s*\|\s*YES\b",
        r"\bAction performed:\s*YES\b",
    ]
    for pattern in forbidden_mutations:
        assert not re.search(pattern, text, flags=re.IGNORECASE), (
            "issue #456 audit/triage handoff must recommend GitHub issue actions "
            f"without performing or instructing automatic mutations: {pattern}"
        )
