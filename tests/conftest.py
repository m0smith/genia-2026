from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from genia import make_global_env, run_source


def eval_code(src: str, stdin_data=None):
    env = make_global_env([] if stdin_data is None else stdin_data)
    return run_source(src, env)


@pytest.fixture
def run():
    return eval_code
