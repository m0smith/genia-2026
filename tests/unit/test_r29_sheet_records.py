"""R29 Python reference host internals/security wiring; not cross-host proof.

Portable result oracles live in spec/{eval,error,flow}/r29-*. These tests
pin host object identity, marked exceptions, metadata and protected sinks.
T1 tests require the unimplemented boundary; T2 tests use existing operations.
"""

import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug
from genia.values import GeniaMap, GeniaOptionErr

FLOW = (
    "to_flow(xs) = evolve(0, inc) |> take(length(xs)) |> map((i) -> unwrap_or(nil, nth(i, xs)))\n"
)
HAND = """pairs_to_map(row) = reduce((m, kv) -> map_put(m, unwrap_or(nil, nth(0, kv)), unwrap_or(nil, nth(1, kv))), map_new(), row)
as_records(s) = rows(s) |> map(pairs_to_map)
"""
PROTECTED = """provider = config_provider([{kind: quote(values), values: {K: "R29_PRIVATE_SENTINEL_31"}}]) |> unwrap_or(nil)
token = secret_get(provider, "K", quote(demo)) |> unwrap_or(nil)
s = sheet([["n", [token]]])
"""


def test_t1_materialized_independent_maps_preserve_exact_references():
    env = make_global_env([])
    run_source(
        PROTECTED + 's2 = sheet([[[1, 2], [token, token]], ["o", [some(1), err("bad")]]])', env
    )
    original = env.get("s2")
    result = run_source("sheet_records(s2)", env)
    assert type(result) is list and len(result) == 2
    assert all(isinstance(row, GeniaMap) for row in result)
    assert result[0] is not result[1]
    for index, row in enumerate(result):
        for (key, cell), (name, values) in zip(row.items(), original.columns, strict=True):
            assert key is name
            assert cell is values[index]
    assert env.get("s2") is original
    # All row containers already exist before any separately built Flow is pulled.
    env.set_host("records_fixture", result, visibility="entry-only")
    assert run_source(FLOW + "to_flow(records_fixture) |> take(1) |> collect", env) == result[:1]
    assert len(result) == 2


@pytest.mark.parametrize("source", ["sheet_records(1)", "[1] |> sheet_records"])
def test_t1_misuse_has_original_marked_type_error(source):
    with pytest.raises(TypeError, match="^sheet_records expected a Sheet$") as raised:
        run_source(source, make_global_env([]))
    assert raised.value._genia_preserve_pipeline_error is True


def test_t1_entry_runtime_name_is_reserved_before_initializer():
    env = make_global_env([])
    with pytest.raises(RuntimeError, match="name is reserved by the runtime"):
        run_source("sheet_records =: 5", env)
    assert run_source("sheet_records(sheet([]))", env) == []


def test_t1_module_alias_and_local_shadowing(tmp_path):
    (tmp_path / "record_module.genia").write_text(
        "convert = sheet_records\nlocal(sheet_records) = sheet_records + 1\n"
    )
    result = run_source(
        "import record_module as m\n[m.convert(sheet([])), m.local(4)]",
        make_global_env([]),
        filename=str(tmp_path / "main.genia"),
    )
    assert result == [[], 5]


def test_t1_public_metadata_help_doc_meta(capsys):
    env = make_global_env([])
    entry = env.get("sheet_records")
    metadata = env.get_metadata("sheet_records")
    assert metadata.get("category") and metadata.get("doc")
    assert metadata.get("stability").lower() == "experimental"
    assert run_source('doc("sheet_records")', env) == metadata.get("doc")
    reflected = run_source('meta("sheet_records")', env)
    assert reflected.get("doc") == metadata.get("doc")
    run_source('alias = sheet_records\nhelp("alias")', env)
    assert "sheet_records" in capsys.readouterr().out
    assert env.get("alias") is entry


@pytest.mark.parametrize(
    "convert,stage",
    [("sheet_records", "T1"), ("as_records", "T2")],
    ids=["T1-new-boundary", "T2-existing-hand-conversion"],
)
@pytest.mark.parametrize(
    "surface",
    [
        "display(cv)",
        "debug_repr(cv)",
        "json_encode(cv)",
        "print(cv)",
        "render_csv(collect_sheet(recs))",
    ],
)
def test_protected_transport_diagnostics_and_sinks(convert, stage, surface, capsys):
    env = make_global_env([])
    run_source(
        HAND
        + PROTECTED
        + f'recs = {convert}(s)\ncv = collect_validated(validate_each(recs, (r) -> validate_field("n", (v) -> false, "number", r)))',
        env,
    )
    assert env.get("recs")[0].get("n") is env.get("token")
    if surface.startswith(("print", "render_csv")):
        with pytest.raises(TypeError, match="protected-value") as raised:
            run_source(surface, env)
        text = str(raised.value)
    else:
        result = run_source(surface, env)
        text = result if isinstance(result, str) else format_debug(result)
        if surface.startswith("json_encode"):
            assert isinstance(result, GeniaOptionErr)
            assert "protected-value" in text
        else:
            assert "<protected>" in text
    captured = capsys.readouterr()
    assert "R29_PRIVATE_SENTINEL_31" not in text + captured.out + captured.err
    assert captured.out == "" and captured.err == ""


@pytest.mark.parametrize(
    "convert,stage",
    [("sheet_records", "T1"), ("as_records", "T2")],
    ids=["T1-new-boundary", "T2-existing-hand-conversion"],
)
def test_outcome_data_is_not_lifecycle_failure(convert, stage):
    env = make_global_env([])
    result = run_source(
        HAND
        + FLOW
        + f"""s = sheet([["n", [err("data")]]])
rs = {convert}(s)
work(h) = {{ r = unwrap_or(nil, lifecycle_context(h, quote(element))); r.n }}
bad(h) = 1 / 0
ok = lifecycle_repeat([], to_flow(rs), work) |> collect
failed = lifecycle_repeat([], to_flow(rs), bad) |> collect
[map((r) -> r.status, ok), map((r) -> unwrap_or(nil, r.result), ok), map((r) -> r.status, failed), map((r) -> r.result, failed)]""",
        env,
    )
    assert format_debug(result) == '[[ok], [err("data")], [error], [none("lifecycle-no-result")]]'


@pytest.mark.parametrize(
    "source",
    [
        "map((x) -> x, s)",
        "each((x) -> x, s)",
        "scan((a, b) -> a, 0, s)",
        "reduce((a, b) -> a, 0, s)",
        "lifecycle_repeat([], s, (h) -> 1)",
    ],
)
def test_t2_sheet_remains_non_seq(source):
    with pytest.raises(TypeError, match="Seq|sequence|list|Flow|iterable|source"):
        run_source('s = sheet([["n", [1]]])\n' + source, make_global_env([]))


def test_t2_application_flow_is_bounded_reusable_list_single_use_flow():
    env = make_global_env([])
    result = run_source(
        FLOW
        + """xs = [{n: 1}, {n: 2}, {n: 3}]
c = ref(0)
tick(x) = { ref_update(c, inc); x }
f = to_flow(xs) |> map(tick)
out = f |> take(2) |> collect
[out, ref_get(c), collect(to_flow(xs)), collect(to_flow([]))]""",
        env,
    )
    assert format_debug(result) == "[[{n: 1}, {n: 2}], 2, [{n: 1}, {n: 2}, {n: 3}], []]"
    with pytest.raises(RuntimeError, match="already been consumed"):
        run_source("collect(f)", env)
