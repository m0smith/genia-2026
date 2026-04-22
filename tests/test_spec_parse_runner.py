import pytest
from hosts.python import parse_and_normalize

# Black-box: test parse adapter normalization
@pytest.mark.parametrize("source,expected", [
    ("42", {"kind": "ok", "ast": {"kind": "Literal", "value": 42}}),
    ("x = 1", {"kind": "ok", "ast": {"kind": "Assign", "name": "x", "value": {"kind": "Literal", "value": 1}}}),
    ("inc(x) -> x + 1", {"kind": "ok", "ast": {"kind": "FuncDef", "name": "inc", "params": ["x"], "body": {"kind": "Binary", "op": "+", "left": {"kind": "Var", "name": "x"}, "right": {"kind": "Literal", "value": 1}}}}),
])
def test_parse_adapter_valid(source, expected):
    result = parse_and_normalize(source)
    assert result == expected

@pytest.mark.parametrize("source,etype,msgpart", [
    ("(1 + 2", "SyntaxError", "Expected RPAREN"),
    ("x = (y -> y)", "SyntaxError", "Expected RPAREN"),
])
def test_parse_adapter_invalid(source, etype, msgpart):
    result = parse_and_normalize(source)
    assert result["kind"] == "error"
    assert result["type"] == etype
    assert msgpart in result["message"]
