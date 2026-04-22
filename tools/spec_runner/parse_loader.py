# Loader for parse spec fixtures
import yaml
from pathlib import Path

class ParseSpec:
    def __init__(self, path, data):
        self.path = path
        self.id = data["id"]
        self.source = data["source"]
        self.expect_ast = data.get("expect_ast")
        self.expect_error = data.get("expect_error")


def load_parse_spec(path: Path) -> ParseSpec:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if "id" not in data or "source" not in data:
        raise ValueError(f"Missing required fields in {path}")
    if ("expect_ast" in data) == ("expect_error" in data):
        raise ValueError(f"Must have exactly one of expect_ast or expect_error in {path}")
    return ParseSpec(path, data)
