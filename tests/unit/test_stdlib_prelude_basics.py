from pathlib import Path

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def test_list_function(run):
    assert run("list()") == []
    assert run("list(1)") == [1]
    assert run("list(1, 2, 3)") == [1, 2, 3]


def test_first_and_rest(run):
    assert run("unwrap_or(0, first([1, 2, 3]))") == 1
    assert run("is_none?(first([]))") is True
    assert run("rest([1, 2, 3])") == [2, 3]


def test_option_list_helpers(run):
    assert run("is_none?(first([]))") is True
    assert run("is_some?(first([nil]))") is True
    assert format_debug(run_source("unwrap_or(9, first([nil]))", make_global_env([]))) == 'none("nil")'
    assert run("unwrap_or(0, first([1, 2, 3]))") == 1
    assert run('unwrap_or("?", absence_reason(first([])))') == "empty-list"

    assert run("is_none?(first_opt([]))") is True
    assert run("is_some?(first_opt([nil]))") is True
    assert format_debug(run_source("unwrap_or(9, first_opt([nil]))", make_global_env([]))) == 'none("nil")'
    assert run("unwrap_or(0, first_opt([1, 2, 3]))") == 1
    assert run('unwrap_or("?", absence_reason(first_opt([])))') == "empty-list"

    assert run("is_none?(last([]))") is True
    assert run("is_some?(last([1, nil]))") is True
    assert format_debug(run_source("unwrap_or(9, last([1, nil]))", make_global_env([]))) == 'none("nil")'
    assert run("unwrap_or(0, last([1, 2, 3]))") == 3

    assert run("is_none?(find_opt((x) -> x == 9, []))") is True
    assert run("unwrap_or(0, find_opt((x) -> x % 2 == 0, [1, 2, 4]))") == 2
    src = '\n'.join([
        'is_missing(x) =',
        '  none -> true |',
        '  _ -> false',
        '[is_some?(find_opt(is_missing, [1, nil, 2])), unwrap_or(7, find_opt(is_missing, [1, nil, 2]))]',
    ])
    result = run(src)
    assert result[0] is True
    assert format_debug(result[1]) == 'none("nil")'
    assert run('unwrap_or("?", absence_reason(find_opt((x) -> x == 9, [])))') == "no-match"
    assert run("unwrap_or(0, nth(2, [10, 20, 30]))") == 30
    assert run("is_none?(nth(8, [10, 20]))") is True
    assert run("unwrap_or(0, nth_opt(2, [10, 20, 30]))") == 30
    assert run("is_none?(nth_opt(8, [10, 20]))") is True


def test_book_nth_take_drop_examples_match_current_option_style(run):
    assert run('unwrap_or("?", nth(1, ["a", "b", "c"]))') == "b"
    assert run("take(2, [1, 2, 3, 4])") == [1, 2]
    assert run("drop(2, [1, 2, 3, 4])") == [3, 4]
    assert format_debug(run_source("nth(9, [1, 2])", make_global_env([]))) == 'none("index-out-of-bounds", {index: 9, length: 2})'
    assert run('unwrap_or("missing", nth(9, [1, 2]))') == "missing"


def test_empty_and_nil_predicates(run):
    assert run("empty?([])") is True
    assert run("empty?([1])") is False
    assert run("nil?(nil)") is True
    assert run("nil?(0)") is False
    assert run("nil?([])") is False


def test_append(run):
    assert run("append([], [])") == []
    assert run("append([], [1, 2])") == [1, 2]
    assert run("append([1, 2], [])") == [1, 2]
    assert run("append([1, 2], [3, 4])") == [1, 2, 3, 4]


def test_length(run):
    assert run("length([])") == 0
    assert run("length([1])") == 1
    assert run("length([1, 2, 3])") == 3


def test_reverse(run):
    assert run("reverse([])") == []
    assert run("reverse([1])") == [1]
    assert run("reverse([1, 2, 3])") == [3, 2, 1]


def test_reduce(run):
    # empty list returns initial accumulator
    assert run("reduce((acc, x) -> acc + x, 0, [])") == 0
    assert run("reduce((acc, x) -> acc + x, 99, [])") == 99
    # left-to-right accumulation: 0-1-2-3 = -6 (not right-fold -2)
    assert run("reduce((acc, x) -> acc - x, 0, [1, 2, 3])") == -6
    # lambda reducer
    assert run("reduce((acc, x) -> acc + x, 0, [1, 2, 3, 4])") == 10
    # named function reducer
    assert run("add(a, b) = a + b\nreduce(add, 0, [1, 2, 3, 4])") == 10


def test_map(run):
    # empty list returns []
    assert run("map((x) -> x + 1, [])") == []
    # maps values in order
    assert run("map((x) -> x + 1, [1, 2, 3])") == [2, 3, 4]
    # named function mapper
    assert run("double(x) = x * 2\nmap(double, [1, 2, 3])") == [2, 4, 6]


def test_filter(run):
    # empty list returns []
    assert run("filter((x) -> x % 2 == 0, [])") == []
    # keeps items where predicate returns true
    assert run("filter((x) -> x % 2 == 0, [1, 2, 3, 4, 5])") == [2, 4]
    # drops items where predicate returns false
    assert run("filter((x) -> x > 3, [1, 2, 3, 4, 5])") == [4, 5]
    # named function predicate
    assert run("is_even(x) = x % 2 == 0\nfilter(is_even, [1, 2, 3, 4, 5])") == [2, 4]


def test_range(run):
    assert run("range(5)") == [0, 1, 2, 3, 4]
    assert run("range(2, 5)") == [2, 3, 4, 5]
    assert run("range(2, 8, 2)") == [2, 4, 6, 8]
    assert run("range(5, 1, -2)") == [5, 3, 1]
    assert run("range(5, 1)") == []
    assert run("range(1, 5, -1)") == []
    assert run("range(1, 5, 0)") == []


def test_numeric_helpers(run):
    assert run("inc(4)") == 5
    assert run("dec(4)") == 3
    assert run("mod(7, 3)") == 1
    assert run("abs(-5)") == 5
    assert run("abs(5)") == 5
    assert run("min(2, 9)") == 2
    assert run("min(9, 2)") == 2
    assert run("max(2, 9)") == 9
    assert run("max(9, 2)") == 9


def test_direct_prelude_load_without_autoload():
    env = make_global_env([])
    prelude_path = Path("src/genia/std/prelude/list.genia")
    run_source(prelude_path.read_text(encoding="utf-8"), env, filename=str(prelude_path.resolve()))
    assert run_source("append([1], [2, 3])", env) == [1, 2, 3]
    assert run_source("reverse([1, 2, 3])", env) == [3, 2, 1]
    assert run_source("map((x) -> x + 1, [1, 2, 3])", env) == [2, 3, 4]
    assert run_source("filter((x) -> x % 2 == 1, [1, 2, 3, 4])", env) == [1, 3]
    assert run_source("unwrap_or(0, first([4, 5]))", env) == 4
    assert run_source("unwrap_or(0, first_opt([4, 5]))", env) == 4
    assert run_source("unwrap_or(0, last([4, 5]))", env) == 5
    assert run_source("unwrap_or(0, find_opt((x) -> x == 5, [4, 5, 6]))", env) == 5
    assert run_source("unwrap_or(0, nth(1, [4, 5, 6]))", env) == 5
    assert run_source("unwrap_or(0, nth_opt(1, [4, 5, 6]))", env) == 5
