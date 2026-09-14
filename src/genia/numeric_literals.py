from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NumericLiteral:
    kind: str
    digits: str | None = None
    coefficient: str | None = None
    exponent: str | None = None

    def portable_payload(self) -> dict[str, str]:
        if self.kind == "integer":
            if self.digits is None:
                raise ValueError("integer numeric literal is missing digits")
            return {"kind": "integer", "digits": self.digits}
        if self.kind == "decimal":
            if self.coefficient is None or self.exponent is None:
                raise ValueError("decimal numeric literal is incomplete")
            return {
                "kind": "decimal",
                "coefficient": self.coefficient,
                "exponent": self.exponent,
            }
        raise ValueError(f"unsupported numeric literal kind {self.kind!r}")


def parse_numeric_literal(text: str) -> NumericLiteral:
    lower = text.lower()
    has_exp = "e" in lower
    if has_exp:
        significand, exp_text = lower.split("e", 1)
        source_exp = int(exp_text)
    else:
        significand = text
        source_exp = 0

    if "." not in significand and not has_exp:
        digits = significand.lstrip("0") or "0"
        return NumericLiteral("integer", digits=digits)

    if "." in significand:
        whole, frac = significand.split(".", 1)
    else:
        whole, frac = significand, ""
    coeff_digits = (whole + frac).lstrip("0") or "0"
    exponent = source_exp - len(frac)
    if coeff_digits == "0":
        return NumericLiteral("decimal", coefficient="0", exponent="0")
    while coeff_digits.endswith("0"):
        coeff_digits = coeff_digits[:-1]
        exponent += 1
    return NumericLiteral(
        "decimal",
        coefficient=coeff_digits,
        exponent=str(exponent),
    )


def is_portable_numeric_payload(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    kind = value.get("kind")
    if kind == "integer":
        return set(value) == {"kind", "digits"} and isinstance(value.get("digits"), str)
    if kind == "decimal":
        return (
            set(value) == {"kind", "coefficient", "exponent"}
            and isinstance(value.get("coefficient"), str)
            and isinstance(value.get("exponent"), str)
        )
    return False


def materialize_literal_value(value: Any) -> Any:
    """Materialize a ``Number``/``IrLiteral`` payload for evaluation (issue #840).

    ``Number``/``IrLiteral`` nodes carry every literal kind (strings,
    booleans, symbols, ...), not only numeric ones, so this is the single
    call-site adapter ``genia.evaluator``/``genia.pattern_match`` use: a
    tagged numeric payload (or :class:`NumericLiteral` AST descriptor) is
    built into a real runtime exact value via
    :func:`genia.numeric_values.materialize_exact_numeric` (Integer stays
    plain ``int``; a decimal payload becomes a real, canonical
    ``Decimal`` — never a host ``float``, retiring the former
    ``materialize_legacy_numeric`` bridge); every other literal value passes
    through unchanged, exactly as the retired bridge did.
    """
    if isinstance(value, NumericLiteral) or is_portable_numeric_payload(value):
        from .numeric_values import materialize_exact_numeric

        return materialize_exact_numeric(value)
    return value
