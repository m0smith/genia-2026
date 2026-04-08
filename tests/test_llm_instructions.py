from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_llm_instruction_sync_validator() -> None:
    root = Path(__file__).resolve().parents[1]
    validator = root / "tools" / "validate_llm_instructions.py"

    assert validator.exists(), f"Missing validator script: {validator}"

    result = subprocess.run(
        [sys.executable, str(validator)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "LLM instruction validation failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )