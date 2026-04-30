# Minimal parse executor for shared spec runner
from hosts.python import parse_and_normalize

class ParseResult:
    def __init__(self, kind, ast=None, type=None, message=None):
        self.kind = kind
        self.ast = ast
        self.type = type
        self.message = message

    def as_dict(self):
        if self.kind == "ok":
            return {"kind": "ok", "ast": self.ast}
        else:
            return {"kind": "error", "type": self.type, "message": self.message}


def execute_parse_spec(source):
    result = parse_and_normalize(source)
    if result["kind"] == "ok":
        return ParseResult(kind="ok", ast=result["ast"])
    else:
        return ParseResult(kind="error", type=result["type"], message=result["message"])
