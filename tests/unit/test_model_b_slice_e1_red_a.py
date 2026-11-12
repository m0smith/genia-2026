"""E1 RED-A: missing private production construction interface (issue #1250).

PYTHON REFERENCE HOST ONLY. Authorized by issue comment 6811532577, grounded
in Slice E design sections 3.1-3.2: a closed group subclasses the existing
ordinary group and is assembled only through a private whole-group builder.

Minimal test-bound seam:
    genia.callable.GeniaClosedFunction._from_records(name, records) -> closed group
`records` is a non-empty list of existing GeniaFunction records. This private
factory must return the named closed group containing those clauses; it need
not retain the input record identities. No public constructor is introduced.
Equivalent private layouts may adapt this seam with independent review.

A missing production class/factory is the intentional RED-A observation.
This test does not establish failures of sealing, lifecycle guards, rendering,
reflection or capture exclusion. Those behavioral oracles require separately
authorized RED-B against a real construction seam. No state transitions,
annotation execution, lineage, reservations or source activation are tested.
"""

from genia import callable as callables
from genia import ir
from genia.environment import Env


def test_red_a_private_closed_construction_interface():
    """Resolve the real closed type and build one clause without evaluating source."""
    scope = Env()
    record = callables.GeniaFunction("f", ["x"], None, None, ir.IrVar("x"), scope)

    closed_type = callables.GeniaClosedFunction
    group = closed_type._from_records("f", [record])

    assert isinstance(group, closed_type)
    assert isinstance(group, callables.GeniaFunctionGroup)
    assert group.name == "f"
    assert len(group.records) == 1
