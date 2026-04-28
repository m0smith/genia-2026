from __future__ import annotations

import io
import json
from pathlib import Path
import re

import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug

DOC_PATH = Path("docs/cheatsheet/piepline-flow-vs-value.md")
CASES_PATH = Path("tests/data/pipeline_flow_vs_value_cases.json")
CASE_REF_RE = re.compile(r"\[case:\s*([a-z0-9-]+)\]")


def load_cases() -> list[dict]:
    raw = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    assert isinstance(raw, list), "cases file must contain a JSON list"
    return raw


def doc_case_ids() -> list[str]:
    text = DOC_PATH.read_text(encoding="utf-8")
    return CASE_REF_RE.findall(text)


def run_case(case: dict) -> tuple[str | None, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin_data = case.get("stdin_data", [])
    env = make_global_env(stdin_data=stdin_data, stdout_stream=stdout, stderr_stream=stderr)
    result = run_source(case["source"], env, filename=f"<cheatsheet:{case['id']}>")
    rendered = None if result is None else format_debug(result)
    return rendered, stdout.getvalue() + stderr.getvalue()


def test_cheatsheet_case_references_are_unique():
    ids = doc_case_ids()
    assert ids, "no [case: ...] references found in cheatsheet"
    assert len(ids) == len(set(ids)), "duplicate [case: ...] references found in cheatsheet"


def test_cheatsheet_cases_have_unique_ids():
    cases = load_cases()
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids)), "duplicate case IDs in JSON cases file"


def test_cheatsheet_doc_and_case_file_stay_in_sync():
    doc_ids = set(doc_case_ids())
    case_ids = {case["id"] for case in load_cases()}

    missing_in_cases = sorted(doc_ids - case_ids)
    missing_in_doc = sorted(case_ids - doc_ids)

    assert not missing_in_cases, f"doc references missing in cases file: {missing_in_cases}"
    assert not missing_in_doc, f"case IDs missing in doc references: {missing_in_doc}"


@pytest.mark.parametrize("case", load_cases(), ids=lambda case: case["id"])
def test_cheatsheet_examples_execute(case: dict):
    rendered_result, stdio = run_case(case)

    if "expected_result" in case:
        assert rendered_result == case["expected_result"], (
            f"{case['id']}: expected result {case['expected_result']!r}, got {rendered_result!r}"
        )

    if "expected_stdout" in case:
        assert stdio == case["expected_stdout"], (
            f"{case['id']}: expected stdout/stderr {case['expected_stdout']!r}, got {stdio!r}"
        )

    if "expected_result" not in case and "expected_stdout" not in case:
        pytest.fail(f"{case['id']}: case must declare expected_result and/or expected_stdout")
