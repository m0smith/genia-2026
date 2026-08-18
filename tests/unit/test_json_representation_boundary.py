from genia.builtins import make_global_env
from genia.values import GeniaBytes, GeniaOptionErr, GeniaOptionSome


def test_json_decode_rejects_invalid_utf8_bytes_with_portable_reason():
    result = make_global_env([]).get("_json_decode")(GeniaBytes(b"\xff"))

    assert isinstance(result, GeniaOptionErr)
    assert str(result.reason) == "invalid_json_utf8"
    assert str(result.context.get("operation")) == "decode"


def test_json_decode_accepts_utf8_bytes_and_attaches_one_json_facet():
    result = make_global_env([]).get("_json_decode")(GeniaBytes("{\"é\":1}".encode()))

    assert isinstance(result, GeniaOptionSome)
    assert result.value.facet == "json"
    assert result.value.value.get("é") == 1


def test_json_decode_and_encode_reject_container_depth_over_128():
    env = make_global_env([])
    too_deep_text = "[" * 129 + "0" + "]" * 129
    decoded = env.get("_json_decode")(too_deep_text)

    nested = 0
    for _ in range(129):
        nested = [nested]
    encoded = env.get("_json_encode")(nested)

    assert isinstance(decoded, GeniaOptionErr)
    assert str(decoded.reason) == "json_nesting_too_deep"
    assert isinstance(encoded, GeniaOptionErr)
    assert str(encoded.reason) == "json_nesting_too_deep"
