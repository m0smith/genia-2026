from tools.spec_runner import normalize

# --- Deeply nested normalization ---
def test_deeply_nested_normalization():
    value = {"Map": [["k1", [1, 2, {"Some": {"Map": [["k2", None]]}}]]]}  # deeply nested
    norm = normalize.normalize_value(value)
    # Should preserve structure and normalize None to null
    assert norm == {"Map": [["k1", [1, 2, {"Some": {"Map": [["k2", None]]}}]]]}  # JSON-compatible

# --- Error object normalization with/without optional fields ---
def test_error_object_optional_fields():
    # With location
    err = {"kind": "ParseError", "category": "syntax", "message": "bad", "location": {"line": 1, "column": 2}}
    norm = normalize.normalize_error(err)
    assert norm["kind"] == "ParseError"
    assert norm["category"] == "syntax"
    assert norm["message"] == "bad"
    assert "location" in norm and norm["location"] == {"line": 1, "column": 2}
    # Without location
    err2 = {"kind": "RuntimeError", "category": "runtime", "message": "fail"}
    norm2 = normalize.normalize_error(err2)
    assert norm2["kind"] == "RuntimeError"
    assert norm2["category"] == "runtime"
    assert norm2["message"] == "fail"
    assert "location" not in norm2
