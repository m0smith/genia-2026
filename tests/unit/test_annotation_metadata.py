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


def test_doc_builtin_returns_doc_string_or_none():
    src = """
    @doc "Adds one"
    inc(x) -> x + 1

    [doc("inc"), unwrap_or("missing", absence_reason(doc("missing_doc")))]
    """
    assert run_source(src, make_global_env([]), filename="doc_builtin.genia") == [
        "Adds one",
        "missing-doc",
    ]


def test_help_displays_selected_annotation_metadata_fields():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = '''
    @doc """
    A useful helper.
    """
    @category "math"
    @since "0.4"
    @deprecated "Use inc2 instead."
    inc(x) -> x + 1
    help("inc")
    '''
    run_source(src, env, filename="help_metadata.genia")
    out = "".join(outputs)
    assert "inc/1" in out
    assert "A useful helper." in out
    assert "Category: math" in out
    assert "Since: 0.4" in out
    assert "Deprecated: Use inc2 instead." in out


def test_help_on_annotated_assignment_displays_named_value_metadata():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = """
    @doc "Configuration value"
    @category "config"
    answer = 42
    help("answer")
    """
    run_source(src, env, filename="help_assignment_metadata.genia")
    out = "".join(outputs)
    assert "answer" in out
    assert "named value" in out
    assert "Configuration value" in out
    assert "Category: config" in out


def test_doc_annotation_requires_string_value():
    src = """
    @doc {text: "bad"}
    inc(x) -> x + 1
    """
    with pytest.raises(TypeError, match="@doc annotation expected a string"):
        run_source(src, make_global_env([]), filename="bad_doc.genia")


def test_meta_annotation_requires_map_value():
    src = """
    @meta "bad"
    x = 10
    """
    with pytest.raises(TypeError, match="@meta annotation expected a map"):
        run_source(src, make_global_env([]), filename="bad_meta.genia")


def test_lightweight_string_annotations_attach_metadata():
    src = """
    @category "math"
    @since "0.4"
    @deprecated "Use square2"
    square(x) -> x * x

    [
      unwrap_or("missing", meta("square") |> get("category")),
      unwrap_or("missing", meta("square") |> get("since")),
      unwrap_or("missing", meta("square") |> get("deprecated"))
    ]
    """
    assert run_source(src, make_global_env([]), filename="lightweight_annos.genia") == [
        "math",
        "0.4",
        "Use square2",
    ]


def test_last_annotation_wins_for_duplicate_lightweight_metadata_keys():
    src = """
    @since "0.3"
    @since "0.4"
    @category "core"
    @category "math"
    inc(x) -> x + 1

    [unwrap_or("missing", meta("inc") |> get("since")), unwrap_or("missing", meta("inc") |> get("category"))]
    """
    assert run_source(src, make_global_env([]), filename="lightweight_override.genia") == [
        "0.4",
        "math",
    ]


def test_doc_builtin_falls_back_to_legacy_function_docstring():
    src = 'inc(x) = "legacy doc" x + 1\ndoc("inc")\n'
    assert run_source(src, make_global_env([]), filename="legacy_doc_lookup.genia") == "legacy doc"


def test_meta_returns_none_for_missing_name():
    """meta() returns none('missing-meta', {name: ...}) for undefined names."""
    src = 'unwrap_or("missing", absence_reason(meta("definitely_not_defined")))'
    assert run_source(src, make_global_env([]), filename="meta_missing.genia") == "missing-meta"


def test_meta_missing_name_carries_name_context():
    """meta() none carries the name in absence context."""
    src = """
    result = meta("no_such_fn")
    unwrap_or("?", absence_context(result) |> get("name"))
    """
    assert run_source(src, make_global_env([]), filename="meta_missing_ctx.genia") == "no_such_fn"


def test_doc_metadata_takes_priority_over_legacy_docstring_in_help():
    """When both @doc and legacy inline docstring exist, help() renders @doc."""
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = """
    @doc "Metadata doc wins."
    inc(x) = "legacy doc" x + 1
    help("inc")
    """
    run_source(src, env, filename="doc_priority.genia")
    out = "".join(outputs)
    assert "Metadata doc wins." in out
    assert "legacy doc" not in out


def test_doc_autoloads_prelude_function():
    """doc() triggers autoload for prelude functions and returns @doc text."""
    result = run_source('doc("inc")', make_global_env([]), filename="doc_autoload.genia")
    assert isinstance(result, str)
    assert len(result) > 0


def test_meta_autoloads_prelude_function():
    """meta() triggers autoload and returns metadata map for prelude functions."""
    src = 'unwrap_or("missing", meta("inc") |> get("doc"))'
    result = run_source(src, make_global_env([]), filename="meta_autoload.genia")
    assert isinstance(result, str)
    assert len(result) > 0
