from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "docs.yml"
README_PATH = ROOT / "README.md"


def _workflow() -> dict:
    return yaml.load(WORKFLOW_PATH.read_text(), Loader=yaml.BaseLoader)


def test_docs_workflow_keeps_pages_deployment_on_main_pushes_only():
    workflow = _workflow()
    build = workflow["jobs"]["build"]
    deploy = workflow["jobs"]["deploy"]
    upload = next(
        step for step in build["steps"] if step["name"] == "Upload Pages artifact"
    )

    expected_gate = "github.event_name == 'push' && github.ref == 'refs/heads/main'"
    assert upload["if"] == expected_gate
    assert deploy["if"] == expected_gate
    assert deploy["needs"] == "build"


def test_wiki_steps_use_one_optional_job_environment_gate():
    workflow = _workflow()
    deploy = workflow["jobs"]["deploy"]
    wiki_steps = [step for step in deploy["steps"] if "wiki" in step["name"].lower()]

    assert deploy["env"] == {"WIKI_TOKEN": "${{ secrets.WIKI_TOKEN }}"}
    assert wiki_steps
    assert all(step["if"] == "env.WIKI_TOKEN != ''" for step in wiki_steps)

    workflow_text = WORKFLOW_PATH.read_text()
    assert "if: ${{ secrets.WIKI_TOKEN" not in workflow_text


def test_wiki_token_is_used_only_by_the_publish_step_remote():
    workflow = _workflow()
    deploy = workflow["jobs"]["deploy"]
    steps_with_token_environment = [
        step
        for step in deploy["steps"]
        if "WIKI_TOKEN" in str(step.get("env", {}))
    ]

    assert [step["name"] for step in steps_with_token_environment] == [
        "Publish function reference to GitHub Wiki"
    ]
    assert steps_with_token_environment[0]["env"] == {
        "WIKI_REMOTE": (
            "https://x-access-token:${{ env.WIKI_TOKEN }}@github.com/"
            "${{ github.repository }}.wiki.git"
        )
    }


def test_readme_links_to_published_function_reference():
    assert (
        "[Function Reference](https://m0smith.github.io/genia-2026/reference/)"
        in README_PATH.read_text()
    )
