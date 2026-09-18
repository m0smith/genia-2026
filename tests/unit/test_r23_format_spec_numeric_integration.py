"""Failing tests for issue #913 (E23-2): field-format-spec integration.

Implements docs/design/r23-numeric-representation-interchange-contract.md
section 7 against the merged E23-1 canonical Decimal/Rational/Float64
renderer (issue #911). These tests define the observable behavior of
`format(...)`/`apply_format_spec` for numeric field-format specs:

- alignment/width on canonical rendered text
- zero-padding/grouping where the represented shape supports it
- `.n` half-up precision computed from each kind's exact value
- Rational's `<numerator>/<denominator>` atom never reinterpreted as
  Decimal shape for padding/grouping
- invalid format/numeric-kind combinations raise the existing normalized
  `format-error: ...` diagnostic, never a raw Python traceback
"""

import io

import pytest

from genia import make_global_env, run_source
from genia._format_engine import apply_format_spec


def _env():
    stdout = io.StringIO()
    stderr = io.StringIO()
    return make_global_env(stdout_stream=stdout, stderr_stream=stderr), stdout, stderr


def _run(src: str):
    env, _, _ = _env()
    return run_source(src, env)


# ---------------------------------------------------------------------------
# Alignment/width on canonical rendered text (Decimal/Rational/Float64)
# ---------------------------------------------------------------------------


def test_align_left_decimal_uses_canonical_text():
    assert _run('format("{n:<8}", {n: 3.5})') == "3.5     "


def test_align_right_rational_uses_canonical_text():
    assert _run('format("{n:>8}", {n: 3/4})') == "     3/4"


def test_align_center_float64_uses_canonical_text():
    assert _run('format("{n:^14}", {n: float64(1.5)})') == " float64(1.5) "


def test_align_noop_when_canonical_text_already_wide():
    assert _run('format("{n:<3}", {n: 3/4})') == "3/4"


# ---------------------------------------------------------------------------
# Zero-padding: supported (plain numeral canonical text) vs rejected
# ---------------------------------------------------------------------------


def test_zero_pad_decimal_fixed_notation():
    assert _run('format("{n:06}", {n: 3.5})') == "0003.5"


def test_zero_pad_decimal_negative_keeps_sign_first():
    assert _run('format("{n:06}", {n: -3.5})') == "-003.5"


def test_zero_pad_rational_rejects_with_normalized_diagnostic():
    with pytest.raises((ValueError, TypeError), match="format-error"):
        _run('format("{n:06}", {n: 3/4})')


def test_zero_pad_float64_rejects_with_normalized_diagnostic():
    with pytest.raises((ValueError, TypeError), match="format-error"):
        _run('format("{n:010}", {n: float64(1.5)})')


def test_zero_pad_decimal_scientific_notation_rejects():
    # adjusted_exponent = 22 here, so Decimal's own canonical rendering
    # (E23-1) is scientific notation -- not a plain numeral -- so
    # zero-padding it would mangle the exponent text.
    with pytest.raises((ValueError, TypeError), match="format-error"):
        _run('format("{n:030}", {n: 12345678901234567890123.5})')


# ---------------------------------------------------------------------------
# Grouping: supported (plain numeral canonical text) vs rejected
# ---------------------------------------------------------------------------


def test_grouping_decimal_fixed_notation():
    assert _run('format("{n:,}", {n: 1234.5})') == "1,234.5"


def test_grouping_rational_rejects_with_normalized_diagnostic():
    with pytest.raises((ValueError, TypeError), match="format-error"):
        _run('format("{n:,}", {n: 12345/7})')


def test_grouping_float64_rejects_instead_of_mangling_wrapper_text():
    # Before this slice this call returned the mangled string
    # "flo,at6,4(1,234.5)" -- grouping's digit-counting ran over the whole
    # float64(...) wrapper text introduced by E23-1. It must now raise a
    # normalized diagnostic instead of producing corrupted output.
    with pytest.raises((ValueError, TypeError), match="format-error"):
        _run('format("{n:,}", {n: float64(1234.5)})')


def test_grouping_decimal_scientific_notation_rejects():
    with pytest.raises((ValueError, TypeError), match="format-error"):
        _run('format("{n:,}", {n: 12345678901234567890123.5})')


# ---------------------------------------------------------------------------
# `.n` half-up precision: Decimal (exact coefficient/exponent)
# ---------------------------------------------------------------------------


def test_precision_decimal_half_up_rounds_up():
    assert _run('format("{n:.2}", {n: 1.005})') == "1.01"


def test_precision_decimal_half_up_ties_away_from_zero_negative():
    assert _run('format("{n:.0}", {n: -12.5})') == "-13"


def test_precision_decimal_zero_places_no_decimal_point():
    assert _run('format("{n:.0}", {n: 12.5})') == "13"


def test_precision_decimal_pads_trailing_zeros():
    assert _run('format("{n:.4}", {n: 3.5})') == "3.5000"


# ---------------------------------------------------------------------------
# `.n` half-up precision: Rational (exact ratio, never the num/den atom)
# ---------------------------------------------------------------------------


def test_precision_rational_rounds_exact_ratio_not_atom_text():
    # 1/3 = 0.333... exactly (repeating); .2 must round the true exact
    # ratio to 2 places, not reformat the "1/3" atom text.
    assert _run('format("{n:.2}", {n: 1/3})') == "0.33"


def test_precision_rational_half_up_tie_from_terminating_fraction():
    # 1/8 = 0.125 exactly -- a genuine decimal tie at the 3rd place.
    assert _run('format("{n:.2}", {n: 1/8})') == "0.13"


def test_precision_rational_negative():
    assert _run('format("{n:.2}", {n: -7/4})') == "-1.75"


def test_precision_rational_zero_places():
    assert _run('format("{n:.0}", {n: 5/2})') == "3"


# ---------------------------------------------------------------------------
# `.n` half-up precision: Float64, exact dyadic bit value (not repr text)
# ---------------------------------------------------------------------------


def test_precision_float64_uses_exact_dyadic_value_not_shortest_repr():
    # 2.675's exact binary64 value is
    # 2.67499999999999982236431605997495353221893310546875, which rounds
    # DOWN to 2.67 at 2 places under half-up. Rounding the shortest-
    # round-trip decimal text "2.675" instead (double rounding) would
    # incorrectly give 2.68 -- the exact bug docs/analysis/issue-913-...
    # -preflight.md section "Investigation findings" #2 describes.
    assert _run('format("{n:.2}", {n: float64(2.675)})') == "2.67"


def test_precision_float64_exact_half_representable_value_rounds_up():
    assert _run('format("{n:.2}", {n: float64(0.875)})') == "0.88"


def test_precision_float64_rejects_nan_with_normalized_diagnostic():
    # No Genia source syntax reaches NaN/infinity Float64 values today
    # (E22-5/E22-6 don't expose a source-level constructor), so this
    # exercises apply_format_spec directly at the Python level, exactly
    # as tests/unit/test_r23_canonical_numeric_rendering.py does for
    # format_float64 itself.
    with pytest.raises((ValueError, TypeError), match="format-error"):
        apply_format_spec(float("nan"), ".2")


def test_precision_float64_rejects_infinity_with_normalized_diagnostic():
    with pytest.raises((ValueError, TypeError), match="format-error"):
        apply_format_spec(float("inf"), ".2")


# ---------------------------------------------------------------------------
# Format(...) value parity (existing convention: compiled Format matches
# raw template string behavior)
# ---------------------------------------------------------------------------


def test_precision_rational_format_value_parity():
    raw = _run('format("{n:.2}", {n: 1/3})')
    via_format = _run('format(Format("{n:.2}"), {n: 1/3})')
    assert raw == via_format
