"""Run D1's shared public-preservation cases through existing R16 machinery.

These green controls are portable evidence for their stated requirements; they
do not expose private Python projections or certify D2 linking.
"""

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import load_spec


CASES = sorted((Path(__file__).resolve().parents[2] / 'spec').glob('*/model-b-d1-*.yaml'))


@pytest.mark.parametrize('path', CASES, ids=lambda path: path.stem)
def test_shared_public_preservation(path):
    """Compare exact source/module observations with the shared YAML oracle."""
    spec = load_spec(path)
    assert compare_spec(spec, execute_spec(spec)) == []
