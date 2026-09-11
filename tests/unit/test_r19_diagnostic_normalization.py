"""R19 E19-3: diagnostic portability normalization.

Per docs/analysis/r19-diagnostic-mechanical-inventory.md's highest-priority
finding: "No matching case" diagnostics previously rendered call arguments
with Python's own repr() (e.g. single-quote string repr, trailing-comma
tuple syntax) instead of Genia's own format_debug rendering. This is the
one concrete, approved fix E19-3 makes.
"""

import pytest

from genia import make_global_env, run_source


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_no_matching_case_renders_args_via_genia_debug_not_python_repr():
    # A string argument must render with Genia's double-quote debug
    # escaping, never Python's single-quote repr().
    src = 'f(x) =\n  1 -> "one"\nf("hello")'
    with pytest.raises(RuntimeError) as exc_info:
        _run(src)
    message = str(exc_info.value)
    assert message == 'No matching case for function f/1 with arguments ["hello"]'
    # Python repr() of a string uses single quotes; must not appear.
    assert "'hello'" not in message


def test_no_matching_case_int_argument_rendering_is_deterministic():
    src = 'f(x) =\n  1 -> "one"\nf(99)'
    with pytest.raises(RuntimeError, match=r"^No matching case for function f/1 with arguments \[99\]$"):
        _run(src)


def test_no_matching_case_lambda_pattern_miss_uses_list_rendering():
    src = "(([a, b]) -> a + b)([1])"
    with pytest.raises(RuntimeError, match=r"^No matching case for arguments \[\[1\]\]$"):
        _run(src)


def test_no_matching_case_control_character_argument_uses_u3_escaping():
    # A control character in a mismatched argument must go through the
    # same U3 debug-escaping rule as any other debug rendering, not a
    # Python-specific escape convention.
    src = 'f(x) =\n  1 -> "one"\nf("\\u0000")'
    with pytest.raises(RuntimeError) as exc_info:
        _run(src)
    message = str(exc_info.value)
    assert message == 'No matching case for function f/1 with arguments ["\\u0000"]'
