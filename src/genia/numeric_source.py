"""R21 numeric source classification and lexical/base-10 normalization.

Implements docs/design/r21-numeric-source-portable-representation-contract.md
sections 2 and 3 only: classifying numeric source text as Integer or Decimal,
and normalizing Decimal source into a canonical (coefficient, exponent) pair
without ever constructing a host binary float.

This module performs no evaluator/runtime materialization (R22) and builds
no tagged Core IR payload (that wiring is E21-2's responsibility, consuming
this module's output).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# integer := DIGIT+
# decimal-dotted := DIGIT+ "." DIGIT+
# exponent := ("e" | "E") ("+" | "-")? DIGIT+
# decimal-exp := DIGIT+ exponent
# decimal-dot-exp := DIGIT+ "." DIGIT+ exponent
_NUMERIC_LITERAL_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$")


@dataclass(frozen=True)
class NumericSource:
    """Classification result for one numeric source literal.

    kind is "integer" or "decimal".
    digits is set only for kind == "integer": canonical unsigned base-10
    text with no leading zeros except "0".
    coefficient/exponent are set only for kind == "decimal": canonical
    base-10 text such that value == coefficient * 10**exponent.
    """

    kind: str
    digits: str | None = None
    coefficient: str | None = None
    exponent: str | None = None


def _canonical_integer_digits(text: str) -> str:
    stripped = text.lstrip("0")
    return stripped if stripped else "0"


def _canonicalize_decimal(int_part: str, frac_part: str, exp_part: str | None) -> tuple[str, str]:
    """Return (coefficient, exponent) per contract section 4.2.

    value = coefficient * 10**exponent
    zero -> ("0", "0")
    otherwise trailing base-10 zeros are removed from the magnitude and the
    exponent is increased by the count removed. Lexical scale is not
    retained. Uses only string slicing and integer arithmetic on exponent
    offsets -- never float().
    """
    digits = (int_part + frac_part).lstrip("0")
    if digits == "":
        return "0", "0"

    scale = len(frac_part)
    exponent = -scale
    if exp_part is not None:
        exponent += int(exp_part)

    stripped = digits.rstrip("0")
    if stripped == "":
        return "0", "0"
    removed = len(digits) - len(stripped)
    exponent += removed
    return stripped, str(exponent)


def numeric_literal_payload(number_node) -> dict:
    """Build the R21 E21-2 tagged portable IrLiteral payload for a Number AST node.

    Consumes the E21-1 classification fields already populated on the node
    (source_kind/digits/coefficient/exponent) -- no re-parsing, no float().
    """
    if number_node.source_kind == "integer":
        return {"kind": "integer", "digits": number_node.digits}
    return {
        "kind": "decimal",
        "coefficient": number_node.coefficient,
        "exponent": number_node.exponent,
    }


def numeric_literal_runtime_value(payload: dict) -> int | float:
    """Reconstruct the evaluator-facing int/float from a tagged IrLiteral payload.

    This is a pure compatibility shim required by E21-2's own payload-shape
    change to IrLiteral -- it reproduces exactly the same value the
    evaluator already computed before this ticket (int(digits) for
    Integer; float(coefficient + "e" + exponent) for Decimal, which
    denotes the same mathematical value as the original source spelling
    and therefore rounds to the same binary64 result). It introduces no
    new runtime numeric kind, arithmetic rule, or conversion semantic.
    """
    if payload["kind"] == "integer":
        return int(payload["digits"])
    return float(f"{payload['coefficient']}e{payload['exponent']}")


def classify_numeric_literal(text: str) -> NumericSource:
    """Classify numeric source text as Integer or Decimal.

    Raises SyntaxError deterministically for malformed exponent forms
    (an 'e'/'E' marker with no valid digit-only, optionally signed,
    exponent following it). Leading-dot (.5) and trailing-dot (5.) forms
    are rejected upstream by the lexer/tokenizer -- this function only
    ever receives already-tokenized numeric text.
    """
    match = _NUMERIC_LITERAL_RE.match(text)
    if match is None:
        raise SyntaxError(f"Malformed numeric literal: {text!r}")

    int_part, frac_part, exp_part = match.groups()

    if frac_part is None and exp_part is None:
        return NumericSource(kind="integer", digits=_canonical_integer_digits(int_part))

    coefficient, exponent = _canonicalize_decimal(int_part, frac_part or "", exp_part)
    return NumericSource(kind="decimal", coefficient=coefficient, exponent=exponent)
