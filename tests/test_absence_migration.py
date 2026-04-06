from genia import make_global_env, run_source
from genia.utf8 import format_debug


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_canonical_access_surface_returns_structured_absence(run):
    assert run('unwrap_or("?", get("name", {name: "Genia"}))') == "Genia"
    assert format_debug(_run('absence_reason(get("missing", {name: "Genia"}))')) == "some(missing_key)"
    assert run("unwrap_or(0, first([10, 20]))") == 10
    assert format_debug(_run("absence_reason(first([]))")) == "some(empty_list)"
    assert run("unwrap_or(0, last([10, 20]))") == 20
    assert run("unwrap_or(0, nth(1, [10, 20]))") == 20
    assert format_debug(_run("absence_reason(nth(8, [10, 20]))")) == "some(index_out_of_bounds)"
    assert run('unwrap_or(-1, find("abc", "b"))') == 1
    assert format_debug(_run('absence_reason(find("abc", "x"))')) == "some(not_found)"


def test_compatibility_aliases_match_canonical_behavior(run):
    assert run('get?("name", {name: "Genia"}) == get("name", {name: "Genia"})') is True
    assert format_debug(_run('get?("missing", {name: "Genia"})')) == format_debug(_run('get("missing", {name: "Genia"})'))
    assert run("first_opt([10, 20]) == first([10, 20])") is True
    assert format_debug(_run("first_opt([])")) == format_debug(_run("first([])"))
    assert run("nth_opt(1, [10, 20]) == nth(1, [10, 20])") is True
    assert format_debug(_run("nth_opt(8, [10, 20])")) == format_debug(_run("nth(8, [10, 20])"))


def test_find_opt_is_canonical_predicate_search_helper(run):
    assert run("unwrap_or(0, find_opt((x) -> x == 2, [1, 2, 3]))") == 2
    assert format_debug(_run("absence_reason(find_opt((x) -> x == 9, [1, 2, 3]))")) == "some(no_match)"


def test_docs_deprecated_and_legacy_nil_paths_remain_stable(run):
    assert run('map_get({name: "Genia"}, "name")') == "Genia"
    assert run('map_get({name: "Genia"}, "missing")') is None
    assert run('{name: "Genia"}("name")') == "Genia"
    assert run('{name: "Genia"}("missing")') is None
    assert run('"name"({name: "Genia"})') == "Genia"
    assert run('"missing"({name: "Genia"})') is None
    assert run('{name: "Genia"}/name') == "Genia"
    assert run('{name: "Genia"}/missing') is None


def test_cli_option_remains_legacy_retained_nil_surface(run):
    src = '\n'.join([
        'opts = unwrap_or({}, first(cli_parse(["--indent=4"])))',
        '[cli_option(opts, "indent"), cli_option(opts, "missing"), cli_option_or(opts, "missing", "2")]',
    ])
    assert run(src) == ["4", None, "2"]


def test_migration_does_not_regress_patterns_or_helper_driven_pipeline_flow(run):
    src = '\n'.join([
        'pick(opt) =',
        '  some(v) -> v |',
        '  none(missing_key, info) -> info/key |',
        '  none(_) -> "missing"',
        'record = { user: { name: "Genia" } }',
        '[pick(record |> get("user") |> then_get("name")), pick({} |> get("user") |> then_get("name"))]',
    ])
    assert run(src) == ["Genia", "user"]
