import pytest


def test_eval_self_evaluating(run):
    assert run("eval(quote(42), empty_env())") == 42


def test_eval_variable_lookup(run):
    src = """
    env = define(empty_env(), quote(x), 10)
    eval(quote(x), env)
    """
    assert run(src) == 10


def test_eval_quote_expression(run):
    assert run("eval(quote(quote(x)), empty_env()) == quote(x)") is True


def test_eval_assignment_updates_environment(run):
    src = """
    env = define(empty_env(), quote(x), 1)
    [eval(quote(x = 2), env), lookup(env, quote(x))]
    """
    assert run(src) == [2, 2]


def test_eval_lambda_and_apply(run):
    src = """
    env = empty_env()
    f = eval(quote((x) -> x + 1), env)
    apply(f, [10])
    """
    assert run(src) == 11


def test_eval_application(run):
    assert run("eval(quote(((x) -> x + 1)(5)), empty_env())") == 6


def test_eval_named_application_after_assignment(run):
    src = """
    env = empty_env()
    eval(quote(f = (x) -> x + 1), env)
    eval(quote(f(5)), env)
    """
    assert run(src) == 6


def test_eval_block(run):
    src = """
    eval(
      quote({
        x = 1
        x + 2
      }),
      empty_env()
    )
    """
    assert run(src) == 3


def test_eval_closure_capture(run):
    src = """
    expr = quote({
      make_adder = (n) -> (x) -> x + n
      add5 = make_adder(5)
      add5(10)
    })
    eval(expr, empty_env())
    """
    assert run(src) == 15


def test_eval_block_scope_is_local(run):
    src = """
    env = empty_env()
    eval(
      quote({
        x = 1
        x
      }),
      env
    )
    lookup(env, quote(x))
    """
    with pytest.raises(NameError, match="Undefined name: x"):
        run(src)


def test_eval_match_expression_returns_matcher(run):
    src = """
    matcher = eval(quote(0 -> 1 | _ -> 2), empty_env())
    [apply(matcher, [0]), apply(matcher, [9])]
    """
    assert run(src) == [1, 2]


def test_eval_guarded_match_expression(run):
    src = """
    matcher = eval(quote(x ? x > 0 -> x | _ -> 0), empty_env())
    [apply(matcher, [5]), apply(matcher, [-1])]
    """
    assert run(src) == [5, 0]


def test_eval_match_failure_is_clear(run):
    with pytest.raises(RuntimeError, match="metacircular match failed"):
        run("apply(eval(quote(0 -> 1), empty_env()), [9])")


def test_eval_unsupported_form_remains_clearly_limited(run):
    with pytest.raises(RuntimeError, match="metacircular eval does not support expression"):
        run("eval(quote(quasiquote([x])), empty_env())")


def test_eval_match_expression_with_decimal_literal_pattern(run):
    """Regression coverage for issue #844 (found by issue #843's Step 8 audit).

    A decimal-classified literal used as a quoted match pattern is a
    ``numeric_values.Decimal`` since issue #840 retired the legacy
    decimal-literal-to-float bridge, not a host ``float``; the metacircular
    quoted-pattern lowering must recognize it as a literal pattern rather
    than raising ``TypeError: metacircular quoted match pattern is
    unsupported``.
    """
    src = """
    matcher = eval(quote(1.5 -> "matched" | _ -> "fallback"), empty_env())
    [apply(matcher, [1.5]), apply(matcher, [2.5])]
    """
    assert run(src) == ["matched", "fallback"]


def test_meta_lower_quoted_pattern_accepts_decimal_direct_call():
    """Direct-call coverage matching the issue #843 audit reproducer.

    Exercises evaluator.py's copy of ``_meta_lower_quoted_pattern`` directly,
    the same way section 6.4 of the audit demonstrated the defect.
    """
    from genia import evaluator as genia_evaluator
    from genia.numeric_values import Decimal
    from genia.pattern_match import IrPatLiteral

    pattern = genia_evaluator._meta_lower_quoted_pattern(Decimal(15, -1))
    assert isinstance(pattern, IrPatLiteral)
    assert pattern.value == Decimal(15, -1)


def test_meta_match_pattern_env_builtin_accepts_decimal_rational_float64(run):
    """``_meta_match_pattern_env`` backs ``extend`` and uses builtins.py's
    independently-duplicated copy of ``_meta_lower_quoted_pattern`` (issue
    #844); Rational and Float64 have no source literal syntax (contract
    section 4/5) so they are exercised by quoting a computed value rather
    than a literal token.
    """
    matched_helper = """
    matched(result) = (some(_)) -> true | none -> false
    """

    src_decimal = matched_helper + """
    [matched(_meta_match_pattern_env(empty_env(), quote(1.5), [1.5])),
     matched(_meta_match_pattern_env(empty_env(), quote(1.5), [2.5]))]
    """
    assert run(src_decimal) == [True, False]

    src_rational = matched_helper + """
    quoted_rational = quasiquote(unquote(1 / 3))
    [matched(_meta_match_pattern_env(empty_env(), quoted_rational, [1 / 3])),
     matched(_meta_match_pattern_env(empty_env(), quoted_rational, [1 / 2]))]
    """
    assert run(src_rational) == [True, False]

    src_float64 = matched_helper + """
    quoted_f64 = quasiquote(unquote(float64(1.5)))
    [matched(_meta_match_pattern_env(empty_env(), quoted_f64, [float64(1.5)])),
     matched(_meta_match_pattern_env(empty_env(), quoted_f64, [float64(2.5)]))]
    """
    assert run(src_float64) == [True, False]
