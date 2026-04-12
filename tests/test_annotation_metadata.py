import pytest

from genia import make_global_env, run_source


def test_doc_annotation_attaches_metadata_to_function_binding():
    src = """
    @doc "Adds one"
    inc(x) -> x + 1

    unwrap_or("missing", meta("inc") |> get("doc"))
    """
    assert run_source(src, make_global_env([]), filename="doc_meta.genia") == "Adds one"


def test_meta_annotation_merges_map_metadata():
    src = """
    @meta {category: "math"}
    @meta {stable: true}
    square(x) -> x * x

    [
      unwrap_or("missing", meta("square") |> get("category")),
      unwrap_or(false, meta("square") |> get("stable"))
    ]
    """
    assert run_source(src, make_global_env([]), filename="meta_merge.genia") == ["math", True]


def test_multiple_annotations_merge_on_binding():
    src = """
    @doc "Adds one"
    @meta {category: "math"}
    inc(x) -> x + 1

    [
      unwrap_or("missing", meta("inc") |> get("doc")),
      unwrap_or("missing", meta("inc") |> get("category"))
    ]
    """
    assert run_source(src, make_global_env([]), filename="multi_meta.genia") == ["Adds one", "math"]


def test_later_annotation_keys_override_earlier_keys():
    src = """
    @doc "First"
    @doc "Second"
    @meta {stable: true}
    @meta {stable: false}
    inc(x) -> x + 1

    [
      unwrap_or("missing", meta("inc") |> get("doc")),
      unwrap_or(true, meta("inc") |> get("stable"))
    ]
    """
    assert run_source(src, make_global_env([]), filename="override_meta.genia") == ["Second", False]


def test_rebinding_preserves_existing_metadata_and_new_annotations_override():
    src = """
    @meta {category: "math", stable: true}
    x = 1
    x = 2
    @meta {stable: false, version: 2}
    x = 3

    [
      unwrap_or("missing", meta("x") |> get("category")),
      unwrap_or(true, meta("x") |> get("stable")),
      unwrap_or(0, meta("x") |> get("version"))
    ]
    """
    assert run_source(src, make_global_env([]), filename="rebind_meta.genia") == ["math", False, 2]


def test_help_uses_doc_annotation_when_no_legacy_docstring_exists():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = """
    @doc "Adds one"
    inc(x) -> x + 1
    help("inc")
    """
    run_source(src, env, filename="help_doc_annotation.genia")
    out = "".join(outputs)
    assert "inc/1" in out
    assert "Adds one" in out


def test_doc_annotation_requires_string_value():
    src = """
    @doc {text: "bad"}
    inc(x) -> x + 1
    """
    with pytest.raises(TypeError, match="@doc expected a string"):
        run_source(src, make_global_env([]), filename="bad_doc.genia")


def test_meta_annotation_requires_map_value():
    src = """
    @meta "bad"
    x = 10
    """
    with pytest.raises(TypeError, match="@meta expected a map"):
        run_source(src, make_global_env([]), filename="bad_meta.genia")
