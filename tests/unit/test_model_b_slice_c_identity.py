"""Slice C RED host-local tests: failure identity, legacy wording, migration companions.

PYTHON REFERENCE HOST ONLY (issue #1269; test plan R6.E HL-6, HL-21, HL-22,
HL-23). Exception classes, exact Python error text and the before/after
record of changed outcomes are Python-host details. The portable observations
they accompany live in ``spec/{eval,error,cli}/model-b-c-*.yaml`` and are not
duplicated here.

RED phase: tests named ``*_today`` pin currently implemented behavior and pass;
every other test in a ``future`` section asserts approved Slice C behavior that
is not implemented yet and fails until GREEN. GREEN deliberately inverts only
the ``*_legacy_outcome_today`` companions (maintainer-approved breaking changes
P5 and D5); it changes nothing else here.
"""

from __future__ import annotations

import pytest

from tests.unit.model_b_slice_c_support import cli, outcome

DUPLICATE_LEGACY = "Duplicate function definition: f/1"
OWNERSHIP_LOCAL = (
    "function-declaration-not-owner: cannot declare a/2: "
    "'a' refers to function 'f' declared by another binding in this scope"
)

# --- HL-21: legacy duplicate rejection class and text (R7-D2) ------------------------------------


@pytest.mark.parametrize(
    ("source", "text"),
    [
        ("f(x) = 1\nf(y) = 2\nf(1)", "Duplicate function definition: f/1"),
        ("f(a, ..r) = 1\nf(b, ..s) = 2\nf(1)", "Duplicate function definition: f/1"),
        (
            'describe(x) = (0) -> "zero" | (n) -> "other"\ndescribe(y) = "later"\ndescribe(0)',
            "Duplicate function definition: describe/1",
        ),
    ],
    ids=["identical-header", "rest-binders", "grouped-identical-header"],
)
def test_legacy_duplicate_rejection_keeps_python_class_and_exact_text_today(source, text):
    result = outcome(source)
    assert result.error_class == "TypeError"
    assert result.message == text


def test_legacy_duplicate_rejection_is_construction_time_today():
    """The trailing call is never reached: rejection precedes any later effect."""
    result = outcome('f(x) = 1\nf(y) = 2\nprint("reached")\nf(1)')
    assert result.error_class == "TypeError"
    assert result.printed == ()


def test_legacy_duplicate_cli_rendering_today():
    """CLI stream and exit for the legacy text (the shared oracle pins the same string)."""
    completed = cli("-c", "f(x) = 1\nf(y) = 2\nf(1)")
    assert completed.returncode == 1
    assert completed.stdout == ""
    assert completed.stderr == f"Error: {DUPLICATE_LEGACY}\n"


# --- HL-22: lambda and builtin ordinary targets (R7-D3 open; pinned, no portable claim) ---------


@pytest.mark.parametrize(
    ("source", "text"),
    [
        ("g = (x) -> x\ng(a, b) = 1\ng(1, 2)", "Cannot define function g/2: name already bound to non-function value"),
        ("p = print\np(a, b) = 1\np(1, 2)", "Cannot define function p/2: name already bound to non-function value"),
    ],
    ids=["lambda", "builtin"],
)
def test_declaration_over_non_group_binding_keeps_existing_diagnostic_today(source, text):
    """Pins implemented Python behavior only; the authority question R7-D3 stays open."""
    result = outcome(source)
    assert result.error_class == "TypeError"
    assert result.message == text


# --- HL-6: distinct failure classes must not collapse into one another --------------------------

# (label, source, exception class name, exact message)
GUARD_FAILURES = [
    ("legacy-duplicate", "f(x) = 1\nf(y) = 2\nf(1)", "TypeError", DUPLICATE_LEGACY),
    ("shape-miss", "f(x) = x\nf(1, 2)", "TypeError", "No matching function: f/2. Available: f/1"),
    ("case-miss", "f(x) = (0 -> x)\nf(1)", "RuntimeError", "No matching case for function f/1 with arguments [1]"),
    (
        "varargs-ambiguity",
        "f(a, ..r) = 1\nf(a, b, ..s) = 2\nf(1, 2, 3)",
        "TypeError",
        "Ambiguous function resolution: f/3. Matching varargs: f/1+, f/2+",
    ),
]

FUTURE_FAILURES = [
    (
        "pattern-duplicate",
        "f([a, b]) = 1\nf([c, d]) = 2\nf([1, 2])",
        "OpenFunctionDuplicateClauseError",
        "open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key "
        "shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)",
    ),
    (
        "pattern-group-case-miss",
        "f(0) = 1\nf(5)",
        "RuntimeError",
        "No matching case for function f/1 with arguments [5]",
    ),
    (
        "ownership",
        "f(x) = x\na = f\na(x, y) = x + y\na(1, 2)",
        "FunctionDeclarationNotOwnerError",
        OWNERSHIP_LOCAL,
    ),
]


@pytest.mark.parametrize(("label", "source", "klass", "message"), GUARD_FAILURES, ids=[f[0] for f in GUARD_FAILURES])
def test_existing_failure_classes_and_text_today(label, source, klass, message):
    result = outcome(source)
    assert (result.error_class, result.message) == (klass, message), label


@pytest.mark.parametrize(("label", "source", "klass", "message"), FUTURE_FAILURES, ids=[f[0] for f in FUTURE_FAILURES])
def test_future_failure_classes_and_text(label, source, klass, message):
    result = outcome(source)
    assert (result.error_class, result.message) == (klass, message), label


def test_six_failure_classes_stay_distinct():
    """No two of the six observable failure kinds may share a (class, text-prefix) identity."""
    identities = []
    for label, source, _klass, _message in GUARD_FAILURES + FUTURE_FAILURES:
        result = outcome(source)
        identities.append((label, result.error_class, (result.message or "").split(":")[0]))
    # Case-miss RuntimeError may repeat between the legacy and pattern-group forms
    # (the pattern-group miss must reuse the legacy identity); every other pair differs.
    distinct = {(klass, prefix) for label, klass, prefix in identities if label != "pattern-group-case-miss"}
    assert len(distinct) == len(identities) - 1
    legacy_miss = next(i for i in identities if i[0] == "case-miss")
    pattern_miss = next(i for i in identities if i[0] == "pattern-group-case-miss")
    assert legacy_miss[1:] == pattern_miss[1:]


# --- HL-23: migration companions for every changed outcome of old syntax (R7-D1) ---------------

IMPORTED_LIB = "g(x) = x\n"
IMPORTED_MAIN = "import lib\nh = lib.g\nh(x, y) = x + y\nh(1, 2)\n"


def test_p5_varargs_minima_legacy_outcome_today():
    """Before: the highest-minimum clause is silently chosen. GREEN inverts this companion."""
    assert outcome('f(a, ..r) = "min1"\nf(a, b, ..s) = "min2"\nf(1, 2)').value == "min2"


def test_p5_varargs_minima_new_outcome():
    result = outcome('f(a, ..r) = "min1"\nf(a, b, ..s) = "min2"\nf(1, 2)')
    assert result.error_class == "TypeError"
    assert result.message == "Ambiguous function resolution: f/2. Matching varargs: f/1+, f/2+"


def test_alias_declaration_legacy_outcome_today():
    """Before: declaring through a local alias appends to the aliased group."""
    assert outcome("f(x) = x\na = f\na(x, y) = x + y\na(1, 2)").value == 3


def test_alias_declaration_new_outcome():
    result = outcome("f(x) = x\na = f\na(x, y) = x + y\na(1, 2)")
    assert result.message == OWNERSHIP_LOCAL


def test_annotated_alias_declaration_legacy_outcome_today():
    assert outcome('f(x) = x\na = f\n@doc "d"\na(x, y) = x + y\na(1, 2)').value == 3


def test_annotated_alias_declaration_new_outcome():
    result = outcome('f(x) = x\na = f\n@doc "d"\na(x, y) = x + y\na(1, 2)')
    assert result.message == OWNERSHIP_LOCAL


def test_alias_varargs_declaration_legacy_outcome_today():
    """Before: the alias declaration collides with the fixed clause at the same required arity."""
    result = outcome("f(x) = x\na = f\na(x, ..r) = x\na(1, 2)")
    assert result.message == "Duplicate function definition: a/1"


def test_alias_varargs_declaration_new_outcome():
    result = outcome("f(x) = x\na = f\na(x, ..r) = x\na(1, 2)")
    assert result.message == (
        "function-declaration-not-owner: cannot declare a/1+: "
        "'a' refers to function 'f' declared by another binding in this scope"
    )


def test_imported_alias_declaration_legacy_outcome_today(tmp_path):
    (tmp_path / "lib.genia").write_text(IMPORTED_LIB, encoding="utf-8")
    (tmp_path / "main.genia").write_text(IMPORTED_MAIN, encoding="utf-8")
    completed = cli("main.genia", cwd=tmp_path)
    assert (completed.returncode, completed.stdout, completed.stderr) == (0, "3\n", "")


def test_imported_alias_declaration_new_outcome(tmp_path):
    (tmp_path / "lib.genia").write_text(IMPORTED_LIB, encoding="utf-8")
    (tmp_path / "main.genia").write_text(IMPORTED_MAIN, encoding="utf-8")
    completed = cli("main.genia", cwd=tmp_path)
    assert completed.returncode == 1
    assert completed.stdout == ""
    assert completed.stderr == (
        "Error: function-declaration-not-owner: cannot declare h/2: "
        "'h' refers to function 'g' owned by module 'lib'\n"
    )
