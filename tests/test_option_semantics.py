from genia import make_global_env, run_source
from genia.interpreter import GeniaOptionNone
from genia.utf8 import format_debug


def _run(src: str, stdin=None):
    env = make_global_env([] if stdin is None else stdin)
    return run_source(src, env)


# ---------------------------------------------------------------------------
# None propagation: basic pipeline short-circuit
# ---------------------------------------------------------------------------

def test_none_short_circuits_pipeline_and_preserves_reason():
    src = """
    bump(x) = x + 1
    none("empty-list") |> bump
    """
    assert format_debug(_run(src)) == 'none("empty-list")'


def test_none_argument_short_circuits_ordinary_calls_unless_pattern_matched():
    src = """
    f(x) = x + 1
    g(x) =
      none("missing-key", info) -> info/key |
      _ -> "ok"

    [f(none("missing-key", {key: "name"})), g(none("missing-key", {key: "name"}))]
    """
    result = _run(src)
    assert format_debug(result[0]) == 'none("missing-key", {key: "name"})'
    assert result[1] == "name"


def test_none_type_errors_use_structured_absence():
    assert format_debug(_run('some(2) + 3')) == 'none("type-error", {source: "+", left: "some", right: "int"})'


def test_run_source_normalizes_empty_program_result_to_none_value():
    result = _run("")
    assert isinstance(result, GeniaOptionNone)
    assert format_debug(result) == 'none("nil")'


# ---------------------------------------------------------------------------
# Structured none metadata flows through pipeline
# ---------------------------------------------------------------------------

def test_structured_none_metadata_passes_through_multi_stage_pipeline():
    # reason and context map must survive every skipped stage
    src = """
    add1(x) = x + 1
    times2(x) = x * 2
    upper_str(x) = upper(x)

    none("missing-key", { key: "profile" }) |> add1 |> times2 |> upper_str
    """
    result = _run(src)
    assert format_debug(result) == 'none("missing-key", {key: "profile"})'


def test_structured_none_context_survives_deep_pipeline_chain():
    src = """
    step1(x) = x + 100
    step2(x) = x * 2

    none("index-out-of-bounds", { index: 9, length: 3 }) |> step1 |> step2
    """
    result = _run(src)
    assert format_debug(result) == 'none("index-out-of-bounds", {index: 9, length: 3})'


# ---------------------------------------------------------------------------
# map_some / flat_map_some in pipeline context
# ---------------------------------------------------------------------------

def test_map_some_in_pipeline_applies_function_to_inner_value():
    # parse_int returns some(n) or none(...); map_some applies the doubler and keeps the some wrapper
    src = '"42" |> parse_int |> map_some((n) -> n * 2)'
    result = _run(src)
    assert format_debug(result) == 'some(84)'


def test_map_some_in_pipeline_preserves_none_from_failed_stage():
    src = '"oops" |> parse_int |> map_some((n) -> n * 2)'
    result = _run(src)
    # metadata dict field order is not defined — check reason and none-ness only
    assert format_debug(result).startswith('none("parse-error"')
    assert isinstance(result, GeniaOptionNone)


def test_flat_map_some_chains_option_returning_function():
    src = """
        positive(n) =
            (n) ? n > 0 -> some(n) |
            (_) -> none("negative", { value: n })

    [
      unwrap_or(-1, "5" |> parse_int |> flat_map_some(positive)),
      is_none?("-3" |> parse_int |> flat_map_some(positive))
    ]
    """
    result = _run(src)
    assert result == [5, True]


def test_flat_map_some_preserves_none_metadata_from_failed_parse():
    src = '"bad" |> parse_int |> flat_map_some((n) -> some(n + 1))'
    result = _run(src)
    assert format_debug(result).startswith('none("parse-error"')


def test_pipeline_auto_lifts_some_for_non_option_stages():
    src = 'unwrap_or(-1, some("42") |> parse_int |> map_some((n) -> n + 1))'
    assert _run(src) == 43


def test_pipeline_keeps_option_visible_when_stage_explicitly_matches_some():
    src = """
    describe(opt) =
      some(x) -> x + 1 |
      none(_) -> -1

    some(4) |> describe
    """
    assert _run(src) == 5


# ---------------------------------------------------------------------------
# Mixed valid and invalid data in flow pipelines
# ---------------------------------------------------------------------------

def test_flow_pipeline_with_mixed_valid_invalid_data_no_crash():
    src = """
    ["10", "oops", "20", "bad", "30"] |> lines |> keep_some(parse_int) |> collect
    """
    assert _run(src) == [10, 20, 30]


def test_flow_pipeline_preserves_counts_of_valid_and_dropped_items():
    src = """
    dead = ref([])
    keep(x) = ref_update(dead, (xs) -> append(xs, [x]))

    result = ["1", "two", "3", "four", "5"] |> lines |> keep_some_else(parse_int, keep) |> collect
    [result, ref_get(dead)]
    """
    assert _run(src) == [[1, 3, 5], ["two", "four"]]


def test_pipeline_with_all_invalid_data_produces_empty_list():
    src = """
    ["a", "b", "c"] |> lines |> keep_some(parse_int) |> collect
    """
    assert _run(src) == []


def test_pipeline_with_all_valid_data_produces_complete_list():
    src = """
    ["1", "2", "3"] |> lines |> keep_some(parse_int) |> collect
    """
    assert _run(src) == [1, 2, 3]


# ---------------------------------------------------------------------------
# Recovery helpers at the end of Option-aware pipelines
# ---------------------------------------------------------------------------

def test_unwrap_or_recovers_from_none_at_pipeline_end():
    src = """
    record = {}
    unwrap_or("unknown", record |> get("profile") |> then_get("name"))
    """
    assert _run(src) == "unknown"


def test_unwrap_or_returns_inner_value_on_success():
    src = """
    record = { profile: { name: "Genia" } }
    unwrap_or("unknown", record |> get("profile") |> then_get("name"))
    """
    assert _run(src) == "Genia"


def test_or_else_with_thunk_is_lazy():
    # thunk is only called on none; counter must stay 0 on success
    src = """
    calls = ref(0)
    lazy() = {
      ref_update(calls, (n) -> n + 1)
      "fallback"
    }
    result = or_else_with(some("good"), lazy)
    [result, ref_get(calls)]
    """
    assert _run(src) == ["good", 0]


def test_or_else_with_thunk_is_called_on_none():
    src = """
    calls = ref(0)
    lazy() = {
      ref_update(calls, (n) -> n + 1)
      "fallback"
    }
    result = or_else_with(none("empty-list"), lazy)
    [result, ref_get(calls)]
    """
    assert _run(src) == ["fallback", 1]


# ---------------------------------------------------------------------------
# Canonical chaining pattern with then_* helpers
# ---------------------------------------------------------------------------

def test_canonical_nested_map_access_chain():
    src = """
    record = { user: { address: { zip: "80302" } } }
    unwrap_or("unknown", record |> get("user") |> then_get("address") |> then_get("zip"))
    """
    assert _run(src) == "80302"


def test_none_short_circuits_chain_early_with_first_missing_key():
    src = """
    record = { user: {} }
    record |> get("user") |> then_get("address") |> then_get("zip")
    """
    result = _run(src)
    assert format_debug(result) == 'none("missing-key", {key: "address"})'


def test_absence_reason_and_context_accessible_after_pipeline():
    src = """
    items = []
    items |> first
    """
    result = _run(src)
    assert format_debug(result) == 'none("empty-list")'
    assert format_debug(_run('absence_reason(first([]))')) == 'some("empty-list")'

