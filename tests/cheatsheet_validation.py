from __future__ import annotations

import io
import json
from pathlib import Path
import re

import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug

CASE_REF_RE = re.compile(r"\[case:\s*([a-z0-9-]+)\]")


def load_cases(cases_path: Path) -> list[dict]:
    raw = json.loads(cases_path.read_text(encoding="utf-8"))
    assert isinstance(raw, list), f"{cases_path}: cases file must contain a JSON list"
    return raw


def doc_case_ids(doc_path: Path) -> list[str]:
    text = doc_path.read_text(encoding="utf-8")
    return CASE_REF_RE.findall(text)


def run_case(case: dict) -> tuple[str | None, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin_data = case.get("stdin_data", [])
    env = make_global_env(stdin_data=stdin_data, stdout_stream=stdout, stderr_stream=stderr)
    result = run_source(case["source"], env, filename=f"<cheatsheet:{case['id']}>")
    rendered = None if result is None else format_debug(result)
    return rendered, stdout.getvalue() + stderr.getvalue()


def assert_doc_and_cases_synced(doc_path: Path, cases_path: Path) -> list[dict]:
    ids = doc_case_ids(doc_path)
    assert ids, f"{doc_path}: no [case: ...] references found"
    assert len(ids) == len(set(ids)), f"{doc_path}: duplicate [case: ...] references found"

    cases = load_cases(cases_path)
    case_ids = [case["id"] for case in cases]
    assert len(case_ids) == len(set(case_ids)), f"{cases_path}: duplicate case IDs"

    doc_id_set = set(ids)
    case_id_set = set(case_ids)
    missing_in_cases = sorted(doc_id_set - case_id_set)
    missing_in_doc = sorted(case_id_set - doc_id_set)

    assert not missing_in_cases, f"{cases_path}: missing case entries for doc IDs {missing_in_cases}"
    assert not missing_in_doc, f"{doc_path}: missing [case: ...] markers for case IDs {missing_in_doc}"

    return cases


def assert_case_result(case: dict) -> None:
    rendered_result, stdio = run_case(case)

    if "expected_result" in case:
        assert rendered_result == case["expected_result"], (
            f"{case['id']}: expected result {case['expected_result']!r}, got {rendered_result!r}"
        )

    if "expected_stdout" in case:
        assert stdio == case["expected_stdout"], (
            f"{case['id']}: expected stdout/stderr {case['expected_stdout']!r}, got {stdio!r}"
        )

    if "expected_error_contains" in case:
        pytest.fail(
            f"{case['id']}: expected_error_contains is not supported in this validator path yet"
        )

    if "expected_result" not in case and "expected_stdout" not in case:
        pytest.fail(f"{case['id']}: case must declare expected_result and/or expected_stdout")
