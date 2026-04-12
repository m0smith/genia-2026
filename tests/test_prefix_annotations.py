import pytest

from genia.interpreter import AnnotatedNode, Annotation, Assign, FuncDef, MapLiteral, Parser, String, Var, lex


def parse_program(src: str):
    return Parser(lex(src), source=src, filename="annotations.genia").parse_program()


def test_parser_captures_single_prefix_annotation_on_function_definition():
    ast = parse_program('@doc "Adds one"\ninc(x) -> x + 1\n')

    node = ast[0]
    assert isinstance(node, AnnotatedNode)
    assert isinstance(node.target, FuncDef)
    assert len(node.annotations) == 1

    annotation = node.annotations[0]
    assert isinstance(annotation, Annotation)
    assert annotation.name == "doc"
    assert isinstance(annotation.value, String)
    assert annotation.value.value == "Adds one"


def test_parser_captures_multiple_stacked_prefix_annotations():
    src = '@doc """Adds one.\\n"""\n@category "math"\ninc(x) -> x + 1\n'
    ast = parse_program(src)

    node = ast[0]
    assert isinstance(node, AnnotatedNode)
    assert isinstance(node.target, FuncDef)
    assert [annotation.name for annotation in node.annotations] == ["doc", "category"]
    assert isinstance(node.annotations[0].value, String)
    assert node.annotations[0].value.value == "Adds one.\n"
    assert isinstance(node.annotations[1].value, String)
    assert node.annotations[1].value.value == "math"


def test_parser_captures_multiline_doc_annotation():
    src = '@doc """\nAdds one.\n"""\ninc(x) -> x + 1\n'
    ast = parse_program(src)

    node = ast[0]
    assert isinstance(node, AnnotatedNode)
    assert isinstance(node.annotations[0].value, String)
    assert node.annotations[0].value.value == "\nAdds one.\n"


def test_parser_captures_annotation_on_top_level_assignment():
    ast = parse_program('@meta {category: "math"}\nx = 10\n')

    node = ast[0]
    assert isinstance(node, AnnotatedNode)
    assert isinstance(node.target, Assign)
    assert node.target.name == "x"
    assert len(node.annotations) == 1
    assert isinstance(node.annotations[0].value, MapLiteral)
    key, value = node.annotations[0].value.items[0]
    assert isinstance(key, Var)
    assert key.name == "category"
    assert isinstance(value, String)
    assert value.value == "math"


def test_parser_rejects_annotation_without_bindable_target():
    with pytest.raises(
        SyntaxError,
        match="Annotation must be followed by a top-level function definition or assignment",
    ):
        parse_program('@doc "Adds one"\n1 + 2\n')
