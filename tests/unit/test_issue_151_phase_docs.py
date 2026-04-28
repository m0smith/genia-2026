from pathlib import Path


REPO = Path(__file__).resolve().parent.parent.parent


def _read(relpath: str) -> str:
    return (REPO / relpath).read_text(encoding="utf-8")


def _extract_steps_block(text: str) -> list[str]:
    marker = "Steps:"
    start = text.find(marker)
    assert start != -1, "preflight doc missing 'Steps:' marker"

    tail = text[start + len(marker):]
    end = tail.find("---")
    if end != -1:
        tail = tail[:end]

    return [line.strip() for line in tail.splitlines() if line.strip().startswith("-")]


def test_issue_151_phase_artifacts_exist():
    for relpath in [
        "docs/architecture/issue-151-preflight.md",
        "docs/architecture/issue-151-spec.md",
        "docs/architecture/issue-151-design.md",
    ]:
        assert (REPO / relpath).is_file(), f"missing required phase artifact: {relpath}"


def test_issue_151_preflight_prompt_plan_lists_all_pipeline_phases():
    """
    Guardrail: preflight prompt plan must enumerate the full pipeline,
    including preflight itself.
    """
    text = _read("docs/architecture/issue-151-preflight.md")
    steps = _extract_steps_block(text)

    assert steps == [
        "- Preflight",
        "- Spec",
        "- Design",
        "- Test",
        "- Implementation",
        "- Docs",
        "- Audit",
    ]
