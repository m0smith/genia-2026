"""Guard maintained numeric host-status truth; not executable language conformance.

Shared specs remain behavioral authority. This guard prevents old release-era
absence claims from contradicting the bounded C++ implementation and retaining
its gaps; historical state records deliberately remain outside this check.
"""

import re

import pytest

from docs_truth_utils import read_text


@pytest.mark.parametrize("number", ["9.21", "9.32"])
def test_numeric_state_digest_does_not_deny_existing_cpp_implementation(number):
    """Each maintained numeric digest must distinguish a bounded host from absence."""
    state = read_text("GENIA_STATE.md")
    section = state.split(f"## {number})", 1)[1].split("\n## ", 1)[0]
    flat = " ".join(section.split())
    assert "no C++ implementation" not in flat
    assert "Python reference host only" not in flat
    assert "bounded C++" in flat
    assert "numeric-host-status.md" in section


def test_numeric_host_status_retains_partial_claims_and_resource_gaps():
    """Implementation status must retain limits instead of replacing denial with parity."""
    status = read_text("docs/host-interop/numeric-host-status.md")
    for boundary in ("not full R22/R23 parity", "core_ir_eval", "prelude_autoload",
                     "int64_t", "numeric-resource-limit", "unsupported", "json_compat"):
        assert boundary in status, boundary
    assert re.search(r"Genia checkout: `[0-9a-f]{40}`", status)
    assert re.search(r"C\+\+ checkout: `[0-9a-f]{40}`", status)
    assert "6402e668ae85a1e7efe94b3ac3d51f233b730ca4" in status
