from pathlib import Path

from genia import make_global_env, run_source


def test_list_function(run):
    assert run("list()") == []
    assert run("list(1)") == [1]
    assert run("list(1, 2, 3)") == [1, 2, 3]


def test_first_and_rest(run):
    assert run("first([1, 2, 3])") == 1
    assert run("rest([1, 2, 3])") == [2, 3]


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


def test_map(run):
    assert run("map((x) -> x + 1, [])") == []
    assert run("map((x) -> x + 1, [1, 2, 3])") == [2, 3, 4]


def test_filter(run):
    assert run("filter((x) -> x % 2 == 0, [])") == []
    assert run("filter((x) -> x % 2 == 0, [1, 2, 3, 4, 5])") == [2, 4]


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
    prelude_path = Path("std/prelude/list.genia")
    run_source(prelude_path.read_text(encoding="utf-8"), env, filename=str(prelude_path.resolve()))
    assert run_source("append([1], [2, 3])", env) == [1, 2, 3]
    assert run_source("reverse([1, 2, 3])", env) == [3, 2, 1]
    assert run_source("map((x) -> x + 1, [1, 2, 3])", env) == [2, 3, 4]
    assert run_source("filter((x) -> x % 2 == 1, [1, 2, 3, 4])", env) == [1, 3]
