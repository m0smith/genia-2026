import zipfile

from genia import make_global_env, run_source
from genia.interpreter import GeniaFlow


def test_zip_read_returns_lazy_flow_and_collects_entries(tmp_path):
    in_zip = tmp_path / "in.zip"
    with zipfile.ZipFile(in_zip, "w") as zf:
        zf.writestr("a.txt", "A")
        zf.writestr("b.txt", "B")

    env = make_global_env([])
    env.set("in_path", str(in_zip))
    flow_value = run_source("zip_read(in_path)", env)
    assert isinstance(flow_value, GeniaFlow)

    env = make_global_env([])
    env.set("in_path", str(in_zip))
    result = run_source(
      'zip_read(in_path) |> map((entry) -> unwrap_or("?", first(entry))) |> collect',
        env,
    )
    assert result == ["a.txt", "b.txt"]


def test_zip_read_transform_json_and_zip_write_pipeline(tmp_path):
    in_zip = tmp_path / "in.zip"
    out_zip = tmp_path / "out.zip"

    with zipfile.ZipFile(in_zip, "w") as zf:
        zf.writestr("a.json", '{"z":1,"a":2}')
        zf.writestr("note.txt", "hello")

    env = make_global_env([])
    env.set("in_path", str(in_zip))
    env.set("out_path", str(out_zip))

    src = """
    rewrite(item) =
      ([name, data]) ? ends_with(name, ".json") -> [name, json_parse(utf8_decode(data)) |> json_stringify |> utf8_encode] |
      ([name, data]) -> [name, data]

    zip_read(in_path)
      |> map(rewrite)
      |> zip_write(out_path)
    """

    assert run_source(src, env) == str(out_zip)

    with zipfile.ZipFile(out_zip, "r") as zf:
        assert zf.read("a.json").decode("utf-8") == '{\n  "a": 2,\n  "z": 1\n}'
        assert zf.read("note.txt").decode("utf-8") == "hello"


def test_zip_write_writes_new_zip_from_flow(tmp_path):
    out_zip = tmp_path / "created.zip"

    env = make_global_env([])
    env.set("out_path", str(out_zip))

    src = """
    make_item(line) = [concat(line, ".txt"), upper(line)]

    ["a", "b"]
      |> lines
      |> map(make_item)
      |> zip_write(out_path)
    """

    assert run_source(src, env) == str(out_zip)

    with zipfile.ZipFile(out_zip, "r") as zf:
        assert zf.read("a.txt").decode("utf-8") == "A"
        assert zf.read("b.txt").decode("utf-8") == "B"


def test_file_read_write_and_zip_error_paths_return_none_with_metadata(tmp_path):
    missing = tmp_path / "missing.txt"
    missing_zip = tmp_path / "missing.zip"

    env = make_global_env([])
    env.set("missing", str(missing))
    env.set("missing_zip", str(missing_zip))

    src = """
    read_missing = read_file(missing)
    zip_missing = zip_read(missing_zip)

    [
      none?(read_missing),
      unwrap_or("?", absence_reason(read_missing)),
      none?(zip_missing),
      unwrap_or("?", absence_reason(zip_missing))
    ]
    """

    assert run_source(src, env) == [True, "file-not-found", True, "file-not-found"]

    out_file = tmp_path / "x.txt"
    env = make_global_env([])
    env.set("out_file", str(out_file))
    assert run_source('write_file(out_file, "hello")', env) == str(out_file)
    assert run_source('read_file(out_file)', env) == "hello"
