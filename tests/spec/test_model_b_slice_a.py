"""Portable Slice A observations live in shared R16 IR/error cases, not AST snapshots."""
from pathlib import Path
import pytest
from tools.spec_runner.loader import load_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.comparator import compare_spec

ROOT = Path(__file__).resolve().parents[2]
CASES = sorted((ROOT / 'spec/ir').glob('model-b-a-*.yaml')) + sorted((ROOT / 'spec/parse').glob('model-b-a-*.yaml'))

@pytest.mark.parametrize('path', CASES, ids=lambda p: p.stem)
def test_shared_slice_a(path):
    """Exercise the existing shared runner's comparison and error vocabulary."""
    spec = load_spec(path)
    assert not compare_spec(spec, execute_spec(spec))
