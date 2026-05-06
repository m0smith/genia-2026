import pytest

from genia import make_global_env, run_source
from genia.values import GeniaFlow, is_none


def _env():
    return make_global_env([])


# ---------------------------------------------------------------------------
# resource_ref constructor
# ---------------------------------------------------------------------------


def test_resource_ref_returns_map_with_uri_and_backend():
    env = _env()
    result = run_source(
        """
        import resource as res
        ref = res/resource_ref("foo.txt")
        [ref/uri, ref/backend]
        """,
        env,
    )
    assert result == ["foo.txt", "fs"]


def test_resource_ref_absolute_path_stored_verbatim():
    env = _env()
    result = run_source(
        """
        import resource as res
        res/resource_ref("/abs/path/to/file.txt")/uri
        """,
        env,
    )
    assert result == "/abs/path/to/file.txt"


def test_resource_ref_unicode_path_stored_verbatim():
    env = _env()
    result = run_source(
        """
        import resource as res
        res/resource_ref("données/fichier.txt")/uri
        """,
        env,
    )
    assert result == "données/fichier.txt"


# ---------------------------------------------------------------------------
# read_text / write_text round-trip
# ---------------------------------------------------------------------------


def test_write_then_read_text_roundtrip(tmp_path):
    out_file = tmp_path / "hello.txt"
    env = _env()
    env.set("out_path", str(out_file))
    result = run_source(
        """
        import resource as res
        ref = res/resource_ref(out_path)
        res/write_text(ref, "hello world")
        res/read_text(ref)
        """,
        env,
    )
    assert result == "hello world"


def test_write_text_returns_ref_on_success(tmp_path):
    out_file = tmp_path / "out.txt"
    env = _env()
    env.set("out_path", str(out_file))
    result = run_source(
        """
        import resource as res
        ref = res/resource_ref(out_path)
        written_ref = res/write_text(ref, "data")
        written_ref/uri
        """,
        env,
    )
    assert result == str(out_file)


def test_write_text_overwrites_existing_content(tmp_path):
    out_file = tmp_path / "overwrite.txt"
    env = _env()
    env.set("out_path", str(out_file))
    result = run_source(
        """
        import resource as res
        ref = res/resource_ref(out_path)
        res/write_text(ref, "first")
        res/write_text(ref, "second")
        res/read_text(ref)
        """,
        env,
    )
    assert result == "second"


def test_read_text_empty_file_returns_empty_string(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")
    env = _env()
    env.set("file_path", str(empty_file))
    result = run_source(
        """
        import resource as res
        res/read_text(res/resource_ref(file_path))
        """,
        env,
    )
    assert result == ""


def test_read_text_missing_file_returns_not_found(tmp_path):
    missing = tmp_path / "missing.txt"
    env = _env()
    env.set("missing_path", str(missing))
    result = run_source(
        """
        import resource as res
        res/read_text(res/resource_ref(missing_path))
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "resource-not-found"


def test_write_text_to_nonexistent_directory_returns_write_error(tmp_path):
    out_file = tmp_path / "no_dir" / "file.txt"
    env = _env()
    env.set("out_path", str(out_file))
    result = run_source(
        """
        import resource as res
        res/write_text(res/resource_ref(out_path), "data")
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "resource-write-error"


# ---------------------------------------------------------------------------
# Malformed ref and unsupported backend
# ---------------------------------------------------------------------------


def test_read_text_malformed_ref_plain_string_returns_malformed_ref():
    env = _env()
    result = run_source(
        """
        import resource as res
        res/read_text("just-a-string")
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "resource-malformed-ref"


def test_read_text_malformed_ref_missing_backend_key_returns_malformed_ref():
    env = _env()
    result = run_source(
        """
        import resource as res
        res/read_text({uri: "foo.txt"})
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "resource-malformed-ref"


def test_read_text_missing_uri_key_returns_malformed_ref():
    env = _env()
    result = run_source(
        """
        import resource as res
        res/read_text({backend: "fs"})
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "resource-malformed-ref"


def test_read_text_unsupported_backend_returns_resource_unsupported():
    env = _env()
    result = run_source(
        """
        import resource as res
        res/read_text({uri: "foo.txt", backend: "s3"})
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "resource-unsupported"


# ---------------------------------------------------------------------------
# read_bytes / write_bytes round-trip
# ---------------------------------------------------------------------------


def test_write_then_read_bytes_roundtrip(tmp_path):
    out_file = tmp_path / "data.bin"
    env = _env()
    env.set("out_path", str(out_file))
    result = run_source(
        """
        import resource as res
        ref = res/resource_ref(out_path)
        data = utf8_encode("binary content")
        res/write_bytes(ref, data)
        utf8_decode(res/read_bytes(ref))
        """,
        env,
    )
    assert result == "binary content"


def test_read_bytes_missing_file_returns_not_found(tmp_path):
    missing = tmp_path / "missing.bin"
    env = _env()
    env.set("missing_path", str(missing))
    result = run_source(
        """
        import resource as res
        res/read_bytes(res/resource_ref(missing_path))
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "resource-not-found"


def test_write_bytes_returns_ref_on_success(tmp_path):
    out_file = tmp_path / "data.bin"
    env = _env()
    env.set("out_path", str(out_file))
    result = run_source(
        """
        import resource as res
        ref = res/resource_ref(out_path)
        written_ref = res/write_bytes(ref, utf8_encode("x"))
        written_ref/uri
        """,
        env,
    )
    assert result == str(out_file)


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_nonexistent_file_returns_nil(tmp_path):
    missing = tmp_path / "never_existed.txt"
    env = _env()
    env.set("file_path", str(missing))
    result = run_source(
        """
        import resource as res
        res/delete(res/resource_ref(file_path))
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "nil"


def test_delete_returns_nil_none_on_success(tmp_path):
    out_file = tmp_path / "to_delete.txt"
    env = _env()
    env.set("file_path", str(out_file))
    result = run_source(
        """
        import resource as res
        ref = res/resource_ref(file_path)
        res/write_text(ref, "data")
        res/delete(ref)
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "nil"


def test_delete_then_read_returns_not_found(tmp_path):
    out_file = tmp_path / "to_delete.txt"
    env = _env()
    env.set("file_path", str(out_file))
    result = run_source(
        """
        import resource as res
        ref = res/resource_ref(file_path)
        res/write_text(ref, "bye")
        res/delete(ref)
        res/read_text(ref)
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "resource-not-found"


# ---------------------------------------------------------------------------
# copy
# ---------------------------------------------------------------------------


def test_copy_source_content_to_dest(tmp_path):
    src_file = tmp_path / "src.txt"
    dst_file = tmp_path / "dst.txt"
    env = _env()
    env.set("src_path", str(src_file))
    env.set("dst_path", str(dst_file))
    result = run_source(
        """
        import resource as res
        from_ref = res/resource_ref(src_path)
        to_ref = res/resource_ref(dst_path)
        res/write_text(from_ref, "copied content")
        res/copy(from_ref, to_ref)
        res/read_text(to_ref)
        """,
        env,
    )
    assert result == "copied content"


def test_copy_returns_to_ref_on_success(tmp_path):
    src_file = tmp_path / "src.txt"
    dst_file = tmp_path / "dst.txt"
    env = _env()
    env.set("src_path", str(src_file))
    env.set("dst_path", str(dst_file))
    result = run_source(
        """
        import resource as res
        from_ref = res/resource_ref(src_path)
        to_ref = res/resource_ref(dst_path)
        res/write_text(from_ref, "x")
        copied_ref = res/copy(from_ref, to_ref)
        copied_ref/uri
        """,
        env,
    )
    assert result == str(dst_file)


def test_copy_missing_source_returns_not_found(tmp_path):
    src_file = tmp_path / "missing_src.txt"
    dst_file = tmp_path / "dst.txt"
    env = _env()
    env.set("src_path", str(src_file))
    env.set("dst_path", str(dst_file))
    result = run_source(
        """
        import resource as res
        res/copy(res/resource_ref(src_path), res/resource_ref(dst_path))
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "resource-not-found"


def test_copy_overwrites_existing_dest(tmp_path):
    src_file = tmp_path / "src.txt"
    dst_file = tmp_path / "dst.txt"
    env = _env()
    env.set("src_path", str(src_file))
    env.set("dst_path", str(dst_file))
    result = run_source(
        """
        import resource as res
        from_ref = res/resource_ref(src_path)
        to_ref = res/resource_ref(dst_path)
        res/write_text(to_ref, "old content")
        res/write_text(from_ref, "new content")
        res/copy(from_ref, to_ref)
        res/read_text(to_ref)
        """,
        env,
    )
    assert result == "new content"


# ---------------------------------------------------------------------------
# resource_meta
# ---------------------------------------------------------------------------


def test_resource_meta_existing_file_has_exists_true(tmp_path):
    out_file = tmp_path / "meta.txt"
    env = _env()
    env.set("file_path", str(out_file))
    result = run_source(
        """
        import resource as res
        ref = res/resource_ref(file_path)
        res/write_text(ref, "hello meta")
        meta = res/resource_meta(ref)
        meta/exists
        """,
        env,
    )
    assert result is True


def test_resource_meta_existing_file_size_matches_content(tmp_path):
    content = "hello meta"
    out_file = tmp_path / "meta.txt"
    env = _env()
    env.set("file_path", str(out_file))
    result = run_source(
        """
        import resource as res
        ref = res/resource_ref(file_path)
        res/write_text(ref, "hello meta")
        res/resource_meta(ref)/size
        """,
        env,
    )
    assert result == len(content.encode("utf-8"))


def test_resource_meta_existing_file_backend_is_fs(tmp_path):
    out_file = tmp_path / "meta.txt"
    env = _env()
    env.set("file_path", str(out_file))
    result = run_source(
        """
        import resource as res
        ref = res/resource_ref(file_path)
        res/write_text(ref, "x")
        res/resource_meta(ref)/backend
        """,
        env,
    )
    assert result == "fs"


def test_resource_meta_missing_file_exists_is_false(tmp_path):
    missing = tmp_path / "missing.txt"
    env = _env()
    env.set("file_path", str(missing))
    result = run_source(
        """
        import resource as res
        ref = res/resource_ref(file_path)
        res/resource_meta(ref)/exists
        """,
        env,
    )
    assert result is False


def test_resource_meta_missing_file_has_no_size_key(tmp_path):
    missing = tmp_path / "missing.txt"
    env = _env()
    env.set("file_path", str(missing))
    result = run_source(
        """
        import resource as res
        ref = res/resource_ref(file_path)
        meta = res/resource_meta(ref)
        map_has?(meta, "size")
        """,
        env,
    )
    assert result is False


# ---------------------------------------------------------------------------
# discover
# ---------------------------------------------------------------------------


def test_discover_returns_a_flow(tmp_path):
    (tmp_path / "a.txt").write_text("A")
    env = _env()
    env.set("root_path", str(tmp_path))
    result = run_source(
        """
        import resource as res
        res/discover(res/resource_ref(root_path))
        """,
        env,
    )
    assert isinstance(result, GeniaFlow)


def test_discover_flow_items_have_uri_and_backend_keys(tmp_path):
    (tmp_path / "a.txt").write_text("A")
    (tmp_path / "b.txt").write_text("B")
    env = _env()
    env.set("root_path", str(tmp_path))
    result = run_source(
        """
        import resource as res
        root = res/resource_ref(root_path)
        res/discover(root)
          |> map((ref) -> [ref/uri, ref/backend])
          |> collect
        """,
        env,
    )
    pairs_sorted = sorted(result, key=lambda x: x[0])
    assert pairs_sorted == [
        [str(tmp_path / "a.txt"), "fs"],
        [str(tmp_path / "b.txt"), "fs"],
    ]


def test_discover_does_not_emit_directories(tmp_path):
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "c.txt").write_text("C")
    env = _env()
    env.set("root_path", str(tmp_path))
    result = run_source(
        """
        import resource as res
        res/discover(res/resource_ref(root_path))
          |> map((ref) -> ref/uri)
          |> collect
        """,
        env,
    )
    # Only the file, not the directory
    assert len(result) == 1
    assert result[0] == str(sub / "c.txt")


def test_discover_empty_directory_collects_to_empty_list(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    env = _env()
    env.set("root_path", str(empty_dir))
    result = run_source(
        """
        import resource as res
        res/discover(res/resource_ref(root_path)) |> collect
        """,
        env,
    )
    assert result == []


def test_discover_flow_is_single_use(tmp_path):
    (tmp_path / "a.txt").write_text("A")
    env = _env()
    env.set("root_path", str(tmp_path))
    with pytest.raises(RuntimeError, match="already been consumed"):
        run_source(
            """
            import resource as res
            flow = res/discover(res/resource_ref(root_path))
            collect(flow)
            collect(flow)
            """,
            env,
        )


def test_discover_nonexistent_root_returns_not_found(tmp_path):
    missing_dir = tmp_path / "does_not_exist"
    env = _env()
    env.set("root_path", str(missing_dir))
    result = run_source(
        """
        import resource as res
        res/discover(res/resource_ref(root_path))
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "resource-not-found"


def test_discover_malformed_ref_returns_malformed_ref():
    env = _env()
    result = run_source(
        """
        import resource as res
        res/discover("not-a-ref")
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "resource-malformed-ref"


def test_discover_pipeline_read_all_text(tmp_path):
    (tmp_path / "x.txt").write_text("hello")
    (tmp_path / "y.txt").write_text("world")
    env = _env()
    env.set("root_path", str(tmp_path))
    result = run_source(
        """
        import resource as res
        res/discover(res/resource_ref(root_path))
          |> map(res/read_text)
          |> collect
        """,
        env,
    )
    assert sorted(result) == ["hello", "world"]


# ---------------------------------------------------------------------------
# resource_capabilities
# ---------------------------------------------------------------------------


def test_resource_capabilities_supports_discover_is_true():
    env = _env()
    result = run_source(
        """
        import resource as res
        res/resource_capabilities()/supports_discover
        """,
        env,
    )
    assert result is True


def test_resource_capabilities_all_supports_flags_are_true():
    env = _env()
    result = run_source(
        """
        import resource as res
        caps = res/resource_capabilities()
        [
          caps/supports_discover,
          caps/supports_delete,
          caps/supports_copy,
          caps/supports_meta,
          caps/supports_bytes
        ]
        """,
        env,
    )
    assert result == [True, True, True, True, True]


def test_resource_capabilities_backends_contains_fs():
    env = _env()
    result = run_source(
        """
        import resource as res
        caps = res/resource_capabilities()
        any?((b) -> b == "fs", caps/backends)
        """,
        env,
    )
    assert result is True


# ---------------------------------------------------------------------------
# None propagation
# ---------------------------------------------------------------------------


def test_none_propagation_short_circuits_read_text():
    env = _env()
    result = run_source(
        """
        import resource as res
        res/read_text(none("upstream-failure"))
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "upstream-failure"


def test_none_propagation_short_circuits_write_text(tmp_path):
    env = _env()
    result = run_source(
        """
        import resource as res
        res/write_text(none("upstream-failure"), "data")
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "upstream-failure"


def test_none_propagation_short_circuits_discover():
    env = _env()
    result = run_source(
        """
        import resource as res
        res/discover(none("upstream-failure"))
        """,
        env,
    )
    assert is_none(result)
    assert result.reason == "upstream-failure"


# ---------------------------------------------------------------------------
# Regression: existing file/zip helpers unaffected
# ---------------------------------------------------------------------------


def test_existing_read_file_still_works(tmp_path):
    f = tmp_path / "existing.txt"
    f.write_text("legacy", encoding="utf-8")
    env = _env()
    env.set("fpath", str(f))
    result = run_source("read_file(fpath)", env)
    assert result == "legacy"


def test_existing_write_file_still_works(tmp_path):
    f = tmp_path / "out.txt"
    env = _env()
    env.set("fpath", str(f))
    run_source('write_file(fpath, "legacy")', env)
    assert f.read_text(encoding="utf-8") == "legacy"
