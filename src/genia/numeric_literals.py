from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
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


def materialize_legacy_numeric(value: Any) -> Any:
    """Temporary N-1 compatibility bridge behind portable Core IR.

    N-1 changes source classification and portable representation only. The
    following runtime slice replaces this bridge with exact runtime values.
    """
    if isinstance(value, NumericLiteral):
        value = value.portable_payload()
    if not is_portable_numeric_payload(value):
        return value
    if value["kind"] == "integer":
        return int(value["digits"])
    coefficient = int(value["coefficient"])
    exponent = int(value["exponent"])
    exact_decimal = Decimal(coefficient).scaleb(exponent)
    return float(exact_decimal)
