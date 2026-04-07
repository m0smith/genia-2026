import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug, format_display


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_some_value(run):
    result = run("some(2)")
    assert run("is_some?(some(2))") is True
    assert run("unwrap_or(0, some(2))") == 2
    assert "some(2" in repr(result)


def test_option_public_wrappers_work_as_function_values(run):
    assert run('unwrap_or(0, apply(get, ["a", {a: 7}]))') == 7
    assert run("apply(some?, [some(3)])") is True


def test_none_value(run):
    assert run("none") == run("none")
    assert run("is_none?(none)") is True


def test_structured_none_values_parse_compare_and_print(run):
    assert run("none(empty_list) == none(empty_list)") is True
    assert run("none(empty_list) != none(missing_key)") is True
    assert format_debug(_run("none(empty_list)")) == "none(empty_list)"
    assert format_debug(_run("none(index_out_of_bounds, { index: 8, length: 2 })")) == 'none(index_out_of_bounds, {index: 8, length: 2})'


def test_option_display_and_debug_rendering_preserve_structure():
    assert format_display(_run("none")) == "none"
    assert format_display(_run("none(missing_key, { key: \"name\" })")) == "none(missing_key, {key: name})"
    assert format_display(_run("some(nil)")) == "some(nil)"
    assert format_debug(_run("some(nil)")) == "some(nil)"
    assert format_debug(_run("none(missing_key, { key: \"name\" })")) == 'none(missing_key, {key: "name"})'


def test_print_makes_none_and_nil_distinction_visible():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('print([nil, none, none(empty_list), some(nil)])', env)
    assert outputs == ['[nil, none, none(empty_list), some(nil)]\n']


def test_structured_none_predicates_and_recovery_helpers(run):
    assert run("none?(none(empty_list))") is True
    assert run("none?(some(3))") is False
    assert run("some?(some(3))") is True
    assert run("some?(none(empty_list))") is False
    assert run("some?(some(3)) == is_some?(some(3))") is True
    assert run("none?(none(empty_list)) == is_none?(none(empty_list))") is True
    assert run("or_else(none(empty_list), 42)") == 42
    assert run("or_else(some(9), 42)") == 9
    assert format_debug(_run("absence_reason(none(empty_list))")) == "some(empty_list)"
    assert format_debug(_run("absence_reason(none)")) == "none"
    assert format_debug(_run("absence_context(none(empty_list))")) == "none"
    assert run(
        '\n'.join(
            [
                'ctx = unwrap_or({}, absence_context(none(index_out_of_bounds, { index: 8, length: 2 })))',
                '[ctx/index, ctx/length]',
            ]
        )
    ) == [8, 2]


def test_absence_helpers_fail_clearly_on_wrong_input(run):
    with pytest.raises(TypeError, match="absence_reason expected a none value"):
        run("absence_reason(some(1))")
    with pytest.raises(TypeError, match="absence_context expected a none value"):
        run("absence_context(some(1))")
    with pytest.raises(TypeError, match="or_else expected an option value"):
        run("or_else(42, 0)")


def test_none_special_form_rejects_invalid_arity(run):
    with pytest.raises(SyntaxError, match=r"none\(\.\.\.\) expects 1 or 2 arguments"):
        _run("none()")
    with pytest.raises(SyntaxError, match=r"none\(\.\.\.\) expects at most 2 arguments"):
        _run("none(a, b, c)")




def test_get_none_target_returns_none(run):
    assert run('is_none?(get?("a", none))') is True


def test_get_some_map_target_unwraps_and_queries(run):
    assert run('unwrap_or(0, get?("a", some({a: 3})))') == 3


def test_get_is_canonical_alias_for_get_question(run):
    assert run('unwrap_or(0, get("a", {a: 3}))') == 3
    assert run('is_none?(get("b", {a: 3}))') is True
    assert format_debug(_run('get("b", {a: 3})')) == 'none(missing_key, {key: "b"})'
    assert format_debug(_run('absence_reason(get("b", {a: 3}))')) == "some(missing_key)"


def test_callable_map_and_string_projector_behavior_unchanged(run):
    src = '[{a:nil}("a"), {a:nil}("b"), {a:nil}("b", 7), "a"({a:nil}), "b"({a:nil}), "b"({a:nil}, 7)]'
    assert run(src) == [None, None, 7, None, None, 7]


def test_get_present_key_returns_some(run):
    assert run('is_some?(get?("a", {a: 1}))') is True
    assert run('unwrap_or(0, get?("a", {a: 1}))') == 1


def test_get_missing_key_returns_none(run):
    assert run('is_none?(get?("b", {a: 1}))') is True
    assert run('unwrap_or(9, get?("b", {a: 1}))') == 9
    assert format_debug(_run('absence_reason(get?("b", {a: 1}))')) == "some(missing_key)"
    assert run(
        '\n'.join(
            [
                'ctx = unwrap_or({}, absence_context(get?("b", {a: 1})))',
                'ctx/key',
            ]
        )
    ) == "b"


def test_get_nested_pipeline_success(run):
    src = '\n'.join([
        'record = some({ profile: { name: "Genia" } })',
        'record |> get?("profile") |> get?("name") |> unwrap_or("?")',
    ])
    assert run(src) == "Genia"


def test_get_nested_pipeline_success_with_canonical_get(run):
    src = '\n'.join([
        'record = { profile: { name: "Genia" } }',
        'record |> get("profile") |> then_get("name") |> unwrap_or("?")',
    ])
    assert run(src) == "Genia"


def test_get_nested_pipeline_missing(run):
    src = '\n'.join([
        'record = some({ profile: {} })',
        'record |> get?("profile") |> get?("name") |> unwrap_or("?")',
    ])
    assert run(src) == "?"


def test_then_get_chain_preserves_original_absence(run):
    src = '\n'.join([
        'record = {}',
        'result = record |> get("profile") |> then_get("name")',
        'ctx = unwrap_or({}, absence_context(result))',
        '[absence_reason(result), ctx/key]',
    ])
    result = run(src)
    assert format_debug(result[0]) == "some(missing_key)"
    assert result[1] == "profile"


def test_then_get_direct_and_pipeline_orders_both_work(run):
    assert run('unwrap_or(0, then_get(some({b: 2}), "b"))') == 2
    assert run('unwrap_or(0, some({b: 2}) |> then_get("b"))') == 2


def test_then_get_missing_key_returns_structured_absence(run):
    assert run('is_none?(then_get(some({a: 1}), "b"))') is True
    assert format_debug(_run('absence_reason(then_get(some({a: 1}), "b"))')) == "some(missing_key)"


def test_then_get_propagates_existing_absence_unchanged(run):
    assert format_debug(_run('then_get(none(missing_key, { key: "a" }), "b")')) == 'none(missing_key, {key: "a"})'


def test_get_preserves_present_nil_vs_missing(run):
    src = '[is_some?(get?("a", {a:nil})), is_none?(get?("b", {a:nil})), unwrap_or("d", get?("a", {a:nil}))]'
    assert run(src) == [True, True, None]


def test_unwrap_or_some_and_none(run):
    assert run('unwrap_or(5, some(2))') == 2
    assert run('unwrap_or(5, none)') == 5


def test_or_else_and_or_else_with_support_direct_and_pipeline_styles(run):
    assert run("or_else(some(2), 5)") == 2
    assert run("some(2) |> or_else(5)") == 2
    assert run("or_else(none(empty_list), 5)") == 5
    assert run("none(empty_list) |> or_else(5)") == 5
    assert run("or_else_with(some(2), () -> 5)") == 2
    assert run("some(2) |> or_else_with(() -> 5)") == 2
    assert run("or_else_with(none(empty_list), () -> 5)") == 5
    assert run("none(empty_list) |> or_else_with(() -> 5)") == 5


def test_option_predicates(run):
    assert run('is_some?(some(1))') is True
    assert run('is_some?(none)') is False
    assert run('is_none?(none)') is True
    assert run('is_none?(some(1))') is False


def test_get_unsupported_target_type_error(run):
    with pytest.raises(TypeError, match="get\\? expected a map, some\\(map\\), or none target"):
        run('get?("a", 42)')

    with pytest.raises(TypeError, match="get expected a map, some\\(map\\), or none target"):
        run('get("a", 42)')



def test_get_some_non_map_target_type_error(run):
    with pytest.raises(TypeError, match=r"get\? expected a map, some\(map\), or none target"):
        run('get?("a", some(42))')


def test_option_values_work_with_pattern_matching(run):
    src = '\n'.join([
        'status(opt) =',
        '  none -> "missing" |',
        '  some(x) -> x',
        '[status(get?("name", {name: "Genia"})), status(none)]',
    ])
    assert run(src) == ["Genia", "missing"]


def test_some_pattern_supports_nested_shapes(run):
    src = '\n'.join([
        'extract_name(opt) =',
        '  some({name}) -> name |',
        '  _ -> "?"',
        '[extract_name(some({name: "Genia"})), extract_name(some({})), extract_name(none)]',
    ])
    assert run(src) == ["Genia", "?", "?"]


def test_none_pattern_supports_reason_and_context(run):
    src = '\n'.join([
        'describe(opt) =',
        '  none(empty_list) -> "empty" |',
        '  none(index_out_of_bounds, info) -> info/index |',
        '  none(_) -> "missing" |',
        '  some(v) -> v',
        '[describe(none(empty_list)), describe(none(index_out_of_bounds, { index: 8, length: 2 })), describe(none(missing_key, { key: "name" })), describe(some(3))]',
    ])
    assert run(src) == ["empty", 8, "missing", 3]


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
    assert run(src) == [0, None, 0, 3]
    assert format_debug(_run("absence_reason(first([]))")) == "some(empty_list)"
    assert format_debug(_run("absence_reason(first_opt([]))")) == "some(empty_list)"
    assert format_debug(_run("absence_reason(last([]))")) == "some(empty_list)"


def test_find_opt_returns_none_some_and_some_nil(run):
    assert run("is_none?(find_opt((x) -> x == 9, [1, 2, 3]))") is True
    assert run("unwrap_or(0, find_opt((x) -> x % 2 == 0, [1, 2, 4]))") == 2
    assert run("is_some?(find_opt((x) -> x == nil, [1, nil, 2]))") is True
    assert run("unwrap_or(7, find_opt((x) -> x == nil, [1, nil, 2]))") is None
    assert format_debug(_run("absence_reason(find_opt((x) -> x == 9, [1, 2, 3]))")) == "some(no_match)"


def test_nth_opt_returns_structured_absence(run):
    assert run("unwrap_or(0, nth(1, [10, 20, 30]))") == 20
    assert run("is_none?(nth(8, [10, 20]))") is True
    assert format_debug(_run("absence_reason(nth(8, [10, 20]))")) == "some(index_out_of_bounds)"
    assert run("unwrap_or(0, nth_opt(1, [10, 20, 30]))") == 20
    assert run("is_none?(nth_opt(8, [10, 20]))") is True
    assert format_debug(_run("absence_reason(nth_opt(8, [10, 20]))")) == "some(index_out_of_bounds)"
    assert run(
        '\n'.join(
            [
                'ctx = unwrap_or({}, absence_context(nth_opt(8, [10, 20])))',
                '[ctx/index, ctx/length]',
            ]
        )
    ) == [8, 2]


def test_then_nth_direct_and_pipeline_orders_both_work(run):
    assert run("unwrap_or(0, then_nth(some([10, 20, 30]), 1))") == 20
    assert run("unwrap_or(0, some([10, 20, 30]) |> then_nth(1))") == 20


def test_then_nth_propagates_existing_absence_and_reports_oob(run):
    assert format_debug(_run("then_nth(none(empty_list), 1)")) == "none(empty_list)"
    assert run("is_none?(then_nth(some([10, 20]), 8))") is True
    assert format_debug(_run("absence_reason(then_nth(some([10, 20]), 8))")) == "some(index_out_of_bounds)"


def test_then_first_success_and_empty_list_absence(run):
    assert run("unwrap_or(0, then_first(some([10, 20])))") == 10
    assert run("is_none?(then_first(some([])))") is True
    assert format_debug(_run("absence_reason(then_first(some([])))")) == "some(empty_list)"


def test_then_find_success_and_propagation(run):
    assert run('unwrap_or(-1, then_find(some("abc"), "b"))') == 1
    assert run('unwrap_or(-1, some("abc") |> then_find("b"))') == 1
    assert format_debug(_run('then_find(none(missing_key, { key: "name" }), "b")')) == 'none(missing_key, {key: "name"})'
    assert run('is_none?(then_find(some("abc"), "x"))') is True
    assert format_debug(_run('absence_reason(then_find(some("abc"), "x"))')) == "some(not_found)"


def test_map_some_and_flat_map_some_propagate_structured_absence(run):
    assert run("unwrap_or(0, map_some((x) -> x + 1, some(2)))") == 3
    assert format_debug(_run("map_some((x) -> x + 1, none(empty_list))")) == "none(empty_list)"
    assert run("unwrap_or(0, flat_map_some((x) -> some(x + 1), some(2)))") == 3
    assert format_debug(_run("flat_map_some((x) -> some(x + 1), none(index_out_of_bounds, { index: 8, length: 2 }))")) == 'none(index_out_of_bounds, {index: 8, length: 2})'


def test_flat_map_some_requires_option_result(run):
    with pytest.raises(TypeError, match="flat_map_some expected function to return an option value"):
        run("flat_map_some((x) -> x + 1, some(2))")


def test_or_else_with_is_lazy_and_recovers_from_none(run):
    src = '\n'.join([
        'n = 0',
        'a = or_else_with(some(3), () -> { n = n + 1 n })',
        'b = or_else_with(none(empty_list), () -> { n = n + 1 n })',
        '[a, b, n]',
    ])
    assert run(src) == [3, 1, 1]


def test_safe_chaining_pipeline_examples(run):
    src = '\n'.join([
        'record = { user: { address: { zip: "80302" } } }',
        'record |> get("user") |> then_get("address") |> then_get("zip") |> or_else("unknown")',
    ])
    assert run(src) == "80302"

    src = '\n'.join([
        'data = { items: [{ name: "A" }, { name: "B" }] }',
        'data |> get("items") |> then_nth(0) |> then_get("name") |> or_else("?")',
    ])
    assert run(src) == "A"

    src = '\n'.join([
        'data = { users: [] }',
        'result = data |> get("users") |> then_first() |> then_get("email")',
        '[absence_reason(result), is_none?(result)]',
    ])
    result = run(src)
    assert format_debug(result[0]) == "some(empty_list)"
    assert result[1] is True


def test_pipeline_rewrite_is_unchanged_for_generic_calls(run):
    with pytest.raises(TypeError, match="parse_int expected a string"):
        run("none(empty_list) |> parse_int")


def test_then_helpers_fail_clearly_on_wrong_targets(run):
    with pytest.raises(TypeError, match="then_first expected a list, some\\(list\\), or none target"):
        run("then_first(42)")
    with pytest.raises(TypeError, match="then_nth expected a list, some\\(list\\), or none target"):
        run("then_nth(0, 42)")
    with pytest.raises(TypeError, match="then_nth expected an integer index"):
        run('then_nth(some([1, 2]), "0")')
    with pytest.raises(TypeError, match="then_find expected a string, some\\(string\\), or none target"):
        run("then_find(42, \"a\")")


def test_safe_chaining_does_not_change_ordinary_arithmetic_or_option_errors(run):
    with pytest.raises(TypeError):
        run("some(2) + 3")
    with pytest.raises(TypeError):
        run("none(empty_list) + 3")


def test_legacy_slash_access_still_returns_nil_for_missing_keys(run):
    src = '\n'.join([
        'record = { name: "Genia" }',
        'record/missing',
    ])
    assert run(src) is None


def test_string_find_is_canonical_maybe_returning_search(run):
    assert run('unwrap_or(-1, find("abc", "b"))') == 1
    assert run('is_none?(find("abc", "x"))') is True
    assert format_debug(_run('absence_reason(find("abc", "x"))')) == "some(not_found)"


def test_option_values_do_not_gain_boolean_predicate_coercion(run):
    assert run("any?((_) -> some(1), [1])") is False
    assert run("any?((_) -> none, [1])") is False


def test_unwrap_or_requires_option(run):
    with pytest.raises(TypeError, match="unwrap_or expected an option value"):
        run('unwrap_or(0, 42)')
