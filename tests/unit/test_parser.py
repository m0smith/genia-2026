from hosts.python.parse_adapter import parse_and_normalize


def test_exact_numeric_parser_dotted_and_exponent_forms() -> None:
    dotted = parse_and_normalize("1.2500")
    exponent = parse_and_normalize("1e3")
    negative = parse_and_normalize("-2.5")

    assert dotted["kind"] == "ok"
    assert dotted["ast"]["value"] == {
        "kind": "decimal",
        "coefficient": "125",
        "exponent": "-2",
    }
    assert exponent["kind"] == "ok"
    assert exponent["ast"]["value"] == {
        "kind": "decimal",
        "coefficient": "1",
        "exponent": "3",
    }
    assert negative["kind"] == "ok"
    assert negative["ast"]["kind"] == "Unary"
    assert negative["ast"]["expr"]["value"] == {
        "kind": "decimal",
        "coefficient": "25",
        "exponent": "-1",
    }


def test_exact_numeric_parser_rejects_invalid_exponent() -> None:
    result = parse_and_normalize("1e")
    assert result["kind"] == "error"
