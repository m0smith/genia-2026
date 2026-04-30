# Comparator for parse spec results
class ParseComparisonFailure:
    def __init__(self, field, expected, actual):
        self.field = field
        self.expected = expected
        self.actual = actual

def compare_parse_spec(spec, actual):
    failures = []
    if spec.expect_ast is not None:
        if actual.kind != "ok":
            failures.append(ParseComparisonFailure("kind", "ok", actual.kind))
        elif actual.ast != spec.expect_ast:
            failures.append(ParseComparisonFailure("ast", spec.expect_ast, actual.ast))
    elif spec.expect_error is not None:
        if actual.kind != "error":
            failures.append(ParseComparisonFailure("kind", "error", actual.kind))
        else:
            if actual.type != spec.expect_error["type"]:
                failures.append(ParseComparisonFailure("type", spec.expect_error["type"], actual.type))
            if spec.expect_error["message"] not in actual.message:
                failures.append(ParseComparisonFailure("message", spec.expect_error["message"], actual.message))
    return failures
