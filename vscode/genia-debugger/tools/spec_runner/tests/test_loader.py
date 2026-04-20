import pytest
from tools.spec_runner import loader
import json

# --- Malformed manifest test ---
def test_malformed_manifest(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    # Write malformed JSON
    manifest_path.write_text("{ not: valid json }")
    with pytest.raises(json.JSONDecodeError):
        loader.load_manifest(str(manifest_path))

# --- Missing required fields test ---
def test_missing_required_fields(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    case_path = tmp_path / "case1.json"
    manifest_path.write_text(json.dumps({"cases": [str(case_path)]}))
    # Write a case missing 'category'
    case_path.write_text(json.dumps({"id": "missing-cat", "expect": {}}))
    with pytest.raises(ValueError) as e:
        loader.load_cases(str(manifest_path))
    assert "category" in str(e.value)

# --- Unsupported category test ---
def test_unsupported_category(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    case_path = tmp_path / "case2.json"
    manifest_path.write_text(json.dumps({"cases": [str(case_path)]}))
    # Write a case with unsupported category
    case_path.write_text(json.dumps({"id": "bad-cat", "category": "notreal", "expect": {}}))
    cases = loader.load_cases(str(manifest_path))
    for case in cases:
        with pytest.raises(NotImplementedError):
            loader.dispatch_case(case)
