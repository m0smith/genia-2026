import zipfile

import pytest

from genia import make_global_env, run_source
from genia.interpreter import GeniaBytes, GeniaZipEntry


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_utf8_round_trip():
    src = """
    utf8_decode(utf8_encode("hello 漢字 🙂"))
    """
    assert _run(src) == "hello 漢字 🙂"


def test_json_pretty_from_parsed_json():
    src = r"""
    json_pretty(json_parse("{\"b\":2,\"a\":1}"))
    """
    assert _run(src) == '{\n  "a": 1,\n  "b": 2\n}'


def test_zip_rewrite_happy_path_with_pipeline_and_order(tmp_path):
    in_zip = tmp_path / "in.zip"
    out_zip = tmp_path / "out.zip"

    with zipfile.ZipFile(in_zip, "w") as zf:
        zf.writestr("a.json", '{"z":1,"a":2}')
        zf.writestr("notes.txt", b"raw\x00bytes")
        zf.writestr("b.json", '{"x":[3,2,1]}')

    env = make_global_env([])
    env.set("in_path", str(in_zip))
    env.set("out_path", str(out_zip))
    src = """
    rewrite_entry(entry) =
      entry ? entry_json(entry) -> update_entry_bytes(entry, compose(utf8_encode, json_pretty, json_parse, utf8_decode)) |
      _ -> entry

    rewrite_zip(in_path, out_path) =
      zip_entries(in_path) |> map(rewrite_entry) |> zip_write(out_path)

    rewrite_zip(in_path, out_path)
    """
    assert run_source(src, env) == str(out_zip)

    with zipfile.ZipFile(out_zip, "r") as zf:
        names = [info.filename for info in zf.infolist() if not info.is_dir()]
        assert names == ["a.json", "notes.txt", "b.json"]
        assert zf.read("a.json").decode("utf-8") == '{\n  "a": 2,\n  "z": 1\n}'
        assert zf.read("notes.txt") == b"raw\x00bytes"
        assert zf.read("b.json").decode("utf-8") == '{\n  "x": [\n    3,\n    2,\n    1\n  ]\n}'


def test_invalid_json_failure_is_clear_and_deterministic(tmp_path):
    in_zip = tmp_path / "bad_json.zip"
    out_zip = tmp_path / "out.zip"
    with zipfile.ZipFile(in_zip, "w") as zf:
        zf.writestr("bad.json", '{"x":')

    env = make_global_env([])
    env.set("in_path", str(in_zip))
    env.set("out_path", str(out_zip))
    src = """
    rewrite_entry(entry) =
      entry ? entry_json(entry) -> update_entry_bytes(entry, compose(utf8_encode, json_pretty, json_parse, utf8_decode)) |
      _ -> entry

    zip_entries(in_path) |> map(rewrite_entry) |> zip_write(out_path)
    """
    with pytest.raises(ValueError, match=r"json_parse invalid JSON"):
        run_source(src, env)


def test_invalid_utf8_failure_is_clear_and_deterministic():
    env = make_global_env([])
    env.set("bad", GeniaBytes(b"\xff\xfe"))
    with pytest.raises(ValueError, match=r"utf8_decode invalid UTF-8"):
        run_source("utf8_decode(bad)", env)


def test_type_errors_for_wrong_argument_types():
    with pytest.raises(TypeError, match="utf8_encode expected a string"):
        _run("utf8_encode(123)")
    with pytest.raises(TypeError, match="zip_entries expected a string"):
        _run("zip_entries(123)")
    with pytest.raises(TypeError, match="entry_name expected a zip entry"):
        _run("entry_name(123)")
    env = make_global_env([])
    env.set("entry", GeniaZipEntry("x.json", GeniaBytes(b"{}")))
    with pytest.raises(TypeError, match="update_entry_bytes expected a function as second argument"):
        run_source("update_entry_bytes(entry, 1)", env)


def test_zip_entries_missing_and_invalid_archive_errors(tmp_path):
    missing = tmp_path / "missing.zip"
    env = make_global_env([])
    env.set("missing", str(missing))
    with pytest.raises(FileNotFoundError, match="zip_entries could not read zip file"):
        run_source("zip_entries(missing)", env)

    bad_zip = tmp_path / "bad.zip"
    bad_zip.write_bytes(b"not-a-zip")
    env.set("bad_zip", str(bad_zip))
    with pytest.raises(ValueError, match="zip_entries invalid zip archive"):
        run_source("zip_entries(bad_zip)", env)
