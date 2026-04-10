import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug, format_display


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_structured_none_values_parse_compare_and_print(run):
    assert run('none?(none("empty-list"))') is True
    assert format_debug(_run('absence_reason(none("missing-key"))')) == 'some("missing-key")'
    assert format_debug(_run('none("empty-list")')) == 'none("empty-list")'
    assert format_debug(_run('none("index-out-of-bounds", { index: 8, length: 2 })')) == 'none("index-out-of-bounds", {index: 8, length: 2})'


def test_option_display_and_debug_rendering_preserve_structure():
    assert format_display(_run("none")) == 'none("nil")'
    assert format_display(_run('none("missing-key", { key: "name" })')) == 'none("missing-key", {key: name})'
    assert format_display(_run("some(nil)")) == 'some(none("nil"))'
    assert format_debug(_run("some(nil)")) == 'some(none("nil"))'
    assert format_debug(_run('none("missing-key", { key: "name" })')) == 'none("missing-key", {key: "name"})'


def test_print_makes_none_and_nil_distinction_visible():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('print([nil, none, none("empty-list"), some(nil)])', env)
    assert outputs == ['[none("nil"), none("nil"), none("empty-list"), some(none("nil"))]\n']


def test_structured_none_predicates_and_recovery_helpers(run):
    assert run('none?(none("empty-list"))') is True
    assert run("none?(some(3))") is False
    assert run("some?(some(3))") is True
    assert run('some?(none("empty-list"))') is False
    assert run("some?(some(3)) == is_some?(some(3))") is True
    assert run('none?(none("empty-list")) == is_none?(none("empty-list"))') is True
    assert run('or_else(none("empty-list"), 42)') == 42
    assert run("or_else(some(9), 42)") == 9
    assert format_debug(_run('absence_reason(none("empty-list"))')) == 'some("empty-list")'
    assert format_debug(_run("absence_reason(none)")) == 'some("nil")'
    assert format_debug(_run('absence_context(none("empty-list"))')) == 'none("nil")'
    assert format_debug(_run('absence_meta(none("empty-list"))')) == 'some({reason: "empty-list"})'
    assert format_debug(
        _run('absence_meta(none("index-out-of-bounds", { index: 8, length: 2 }))')
    ) == 'some({reason: "index-out-of-bounds", context: {index: 8, length: 2}})'
    assert run(
        '\n'.join(
            [
                'ctx = unwrap_or({}, absence_context(none("index-out-of-bounds", { index: 8, length: 2 })))',
                '[ctx/index, ctx/length]',
            ]
        )
    ) == [8, 2]


def test_get_is_canonical_alias_for_get_question(run):
    assert run('unwrap_or(0, get("a", {a: 3}))') == 3
    assert run('is_none?(get("b", {a: 3}))') is True
    assert format_debug(_run('get("b", {a: 3})')) == 'none("missing-key", {key: "b"})'
    assert format_debug(_run('absence_reason(get("b", {a: 3}))')) == 'some("missing-key")'


def test_callable_map_and_string_projector_behavior_return_structured_none(run):
    src = '[{a:nil}("a"), {a:nil}("b"), {a:nil}("b", 7), "a"({a:nil}), "b"({a:nil}), "b"({a:nil}, 7)]'
    result = run(src)
    assert format_debug(result[0]) == 'none("nil")'
    assert format_debug(result[1]) == 'none("missing-key", {key: "b"})'
    assert result[2] == 7
    assert format_debug(result[3]) == 'none("nil")'
    assert format_debug(result[4]) == 'none("missing-key", {key: "b"})'
    assert result[5] == 7


def test_get_missing_key_returns_none(run):
    assert run('is_none?(get?("b", {a: 1}))') is True
    assert run('unwrap_or(9, get?("b", {a: 1}))') == 9
    assert format_debug(_run('absence_reason(get?("b", {a: 1}))')) == 'some("missing-key")'
    assert run(
        '\n'.join(
            [
                'ctx = unwrap_or({}, absence_context(get?("b", {a: 1})))',
                'ctx/key',
            ]
        )
    ) == "b"


def test_then_get_chain_preserves_original_absence(run):
    src = '\n'.join([
        'record = {}',
        'result = record |> get("profile") |> then_get("name")',
        'ctx = unwrap_or({}, absence_context(result))',
        '[absence_reason(result), ctx/key]',
    ])
    result = run(src)
    assert format_debug(result[0]) == 'some("missing-key")'
    assert result[1] == "profile"


def test_then_get_missing_key_returns_structured_absence(run):
    assert run('is_none?(then_get(some({a: 1}), "b"))') is True
    assert format_debug(_run('absence_reason(then_get(some({a: 1}), "b"))')) == 'some("missing-key")'


def test_then_get_propagates_existing_absence_unchanged(run):
    assert format_debug(_run('then_get(none("missing-key", { key: "a" }), "b")')) == 'none("missing-key", {key: "a"})'


def test_or_else_and_or_else_with_support_direct_style_and_outer_pipeline_recovery(run):
    assert run("or_else(some(2), 5)") == 2
    assert run('or_else(none("empty-list"), 5)') == 5
    assert run("or_else_with(some(2), () -> 5)") == 2
    assert run('or_else_with(none("empty-list"), () -> 5)') == 5
    assert run('unwrap_or("?", {profile: {name: "Genia"}} |> get("profile") |> get("name"))') == "Genia"
    assert run('unwrap_or("?", {} |> get("profile") |> get("name"))') == "?"
    assert run('unwrap_or(5, none("empty-list") |> parse_int)') == 5


def test_none_pattern_rejects_too_many_inner_patterns(run):
    with pytest.raises(SyntaxError, match=r"none\(\.\.\.\) pattern expects at most 2 inner patterns"):
        run("f(x) = none(a, b, c) -> a")


def test_some_pattern_rejects_multiple_inner_patterns(run):
    with pytest.raises(SyntaxError, match="some\\(\\.\\.\\.\\) pattern expects exactly one inner pattern"):
        run('f(x) = some(a, b) -> a')


def test_option_list_helpers_work_with_pattern_matching(run):
    src = '\n'.join([
        'pick(opt) =',
        '  some(x) -> x |',
        '  none -> 0',
        'pick(first([1, 2, 3]))',
    ])
    assert run(src) == 1


def test_option_list_helpers_empty_cases(run):
    src = '\n'.join([
        'pick(opt) =',
        '  some(x) -> x |',
        '  none -> 0',
        '[pick(first([])), pick(first([nil])), unwrap_or(0, last([])), unwrap_or(0, last([1, 2, 3]))]',
    ])
    result = run(src)
    assert result[0] == 0
    assert format_debug(result[1]) == 'none("nil")'
    assert result[2:] == [0, 3]
    assert format_debug(_run("absence_reason(first([]))")) == 'some("empty-list")'
    assert format_debug(_run("absence_reason(first_opt([]))")) == 'some("empty-list")'
    assert format_debug(_run("absence_reason(last([]))")) == 'some("empty-list")'


def test_find_opt_returns_none_some_and_some_nil(run):
    assert run("is_none?(find_opt((x) -> x == 9, [1, 2, 3]))") is True
    assert run("unwrap_or(0, find_opt((x) -> x % 2 == 0, [1, 2, 4]))") == 2
    src = '\n'.join([
        'is_missing(x) =',
        '  none -> true |',
        '  _ -> false',
        'result = find_opt(is_missing, [1, nil, 2])',
        '[is_some?(result), unwrap_or(7, result)]',
    ])
    result = run(src)
    assert result[0] is True
    assert format_debug(result[1]) == 'none("nil")'
    assert format_debug(_run("absence_reason(find_opt((x) -> x == 9, [1, 2, 3]))")) == 'some("no-match")'


def test_nth_opt_returns_structured_absence(run):
    assert run("unwrap_or(0, nth(1, [10, 20, 30]))") == 20
    assert run("is_none?(nth(8, [10, 20]))") is True
    assert format_debug(_run("absence_reason(nth(8, [10, 20]))")) == 'some("index-out-of-bounds")'
    assert run("unwrap_or(0, nth_opt(1, [10, 20, 30]))") == 20
    assert run("is_none?(nth_opt(8, [10, 20]))") is True
    assert format_debug(_run("absence_reason(nth_opt(8, [10, 20]))")) == 'some("index-out-of-bounds")'
    assert run(
        '\n'.join(
            [
                'ctx = unwrap_or({}, absence_context(nth_opt(8, [10, 20])))',
                '[ctx/index, ctx/length]',
            ]
        )
    ) == [8, 2]


def test_then_nth_propagates_existing_absence_and_reports_oob(run):
    assert format_debug(_run('then_nth(none("empty-list"), 1)')) == 'none("empty-list")'
    assert run("is_none?(then_nth(some([10, 20]), 8))") is True
    assert format_debug(_run("absence_reason(then_nth(some([10, 20]), 8))")) == 'some("index-out-of-bounds")'


def test_then_first_success_and_empty_list_absence(run):
    assert run("unwrap_or(0, then_first(some([10, 20])))") == 10
    assert run("is_none?(then_first(some([])))") is True
    assert format_debug(_run("absence_reason(then_first(some([])))")) == 'some("empty-list")'


def test_then_find_success_and_propagation(run):
    assert run('unwrap_or(-1, then_find(some("abc"), "b"))') == 1
    assert run('unwrap_or(-1, some("abc") |> then_find("b"))') == 1
    assert run('unwrap_or(-1, "abc" |> then_find("b"))') == 1
    assert format_debug(_run('then_find(none("missing-key", { key: "name" }), "b")')) == 'none("missing-key", {key: "name"})'
    assert run('is_none?(then_find(some("abc"), "x"))') is True
    assert format_debug(_run('absence_reason(then_find(some("abc"), "x"))')) == 'some("not-found")'


def test_map_some_and_flat_map_some_propagate_structured_absence(run):
    assert run("unwrap_or(0, map_some((x) -> x + 1, some(2)))") == 3
    assert format_debug(_run('map_some((x) -> x + 1, none("empty-list"))')) == 'none("empty-list")'
    assert run("unwrap_or(0, flat_map_some((x) -> some(x + 1), some(2)))") == 3
    assert format_debug(_run('flat_map_some((x) -> some(x + 1), none("index-out-of-bounds", { index: 8, length: 2 }))')) == 'none("index-out-of-bounds", {index: 8, length: 2})'


def test_option_helpers_report_received_runtime_types(run):
    with pytest.raises(TypeError, match="unwrap_or expected an option value, received int"):
        run("unwrap_or(0, 42)")
    with pytest.raises(TypeError, match="map_some expected an option value, received int"):
        run("map_some((x) -> x + 1, 42)")
    with pytest.raises(TypeError, match="flat_map_some expected an option value, received int"):
        run("flat_map_some((x) -> some(x + 1), 42)")
    with pytest.raises(TypeError, match="flat_map_some expected function to return an option value, received int"):
        run("flat_map_some((x) -> x + 1, some(2))")


def test_safe_chaining_pipeline_examples(run):
    src = '\n'.join([
        'record = { user: { address: { zip: "80302" } } }',
        'unwrap_or("unknown", record |> get("user") |> get("address") |> get("zip"))',
    ])
    assert run(src) == "80302"

    src = '\n'.join([
        'data = { items: [{ name: "A" }, { name: "B" }] }',
        'unwrap_or("?", data |> get("items") |> then_nth(0) |> then_get("name"))',
    ])
    assert run(src) == "A"

    src = '\n'.join([
        'data = { users: [] }',
        'result = data |> get("users") |> then_first() |> then_get("email")',
        '[absence_reason(result), is_none?(result)]',
    ])
    result = run(src)
    assert format_debug(result[0]) == 'some("empty-list")'
    assert result[1] is True


def test_pipeline_short_circuits_none_for_generic_calls(run):
    assert format_debug(_run('none("empty-list") |> parse_int')) == 'none("empty-list")'


def test_pipeline_preserves_none_metadata_for_debug_inspection(run):
    src = '\n'.join([
        'result = none("parse_error", { source: "parser", input: "x" }) |> parse_int |> then_get("value")',
        '[absence_reason(result), absence_meta(result)]',
    ])
    result = run(src)
    assert format_debug(result[0]) == 'some("parse_error")'
    assert format_debug(result[1]) == 'some({reason: "parse_error", context: {source: "parser", input: "x"}})'


def test_then_helpers_fail_clearly_on_wrong_targets(run):
    with pytest.raises(TypeError, match="then_nth expected a list, some\\(list\\), or none target"):
        run("then_nth(0, 42)")
    with pytest.raises(TypeError, match="then_nth expected an integer index"):
        run('then_nth(some([1, 2]), "0")')
    with pytest.raises(TypeError, match="then_find expected a string"):
        run("then_find(42, \"a\")")


def test_safe_chaining_does_not_change_ordinary_arithmetic_or_option_errors(run):
    assert format_debug(_run("some(2) + 3")) == 'none("type-error", {source: "+", left: "some", right: "int"})'
    assert format_debug(_run('none("empty-list") + 3')) == 'none("empty-list")'


def test_slash_access_returns_structured_none_for_missing_keys(run):
    src = '\n'.join([
        'record = { name: "Genia" }',
        'none?(record/missing)',
    ])
    assert run(src) is True


def test_string_find_is_canonical_maybe_returning_search(run):
    assert run('unwrap_or(-1, find("abc", "b"))') == 1
    assert run('is_none?(find("abc", "x"))') is True
    assert format_debug(_run('absence_reason(find("abc", "x"))')) == 'some("not-found")'


def test_absence_context_and_or_else_wrong_inputs_still_fail_clearly(run):
    with pytest.raises(TypeError, match="absence_context expected a none value"):
        run("absence_context(some(1))")
    with pytest.raises(TypeError, match="or_else expected an option value"):
        run("or_else(42, 0)")
