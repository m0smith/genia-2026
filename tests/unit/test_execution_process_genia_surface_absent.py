"""FAILING-TEST PHASE — end-to-end proof that `execution.process` has no
Genia-visible surface yet.

This is the single RED test that is independent of whatever internal
module names (`genia.process_capability`/`process_transport`/
`process_execution`) the implementation phase eventually chooses (those
names are this design's own proposal, not contract-mandated -- see
`docs/design/execution-process-design.md` §13). It drives the real
`run_source`/`make_global_env` path exactly as ordinary Genia programs do,
and proves the capability is unreachable from Genia source today.

Once `execution.process` is implemented and wired into module resolution,
this exact test (unmodified) should start reporting a DIFFERENT failure
shape than today's -- at minimum it will no longer raise
`FileNotFoundError: Module not found: execution`. Do not delete this test
when implementing; adapt its assertions to the real success path in the
implementation phase's own test updates.
"""

from __future__ import annotations

import pytest

from genia.builtins import make_global_env
from genia.interpreter import run_source


def test_importing_execution_module_fails_because_it_does_not_exist_yet():
    env = make_global_env([])

    with pytest.raises(FileNotFoundError, match="execution"):
        run_source("import execution\n1", env)


def test_global_environment_has_no_ambient_execution_process_binding():
    """No file, command, pipe, import, REPL, test, or server mode may
    provision this capability implicitly (contract §3) -- and today there
    is no binding for it at all, ambient or otherwise.
    """
    env = make_global_env([])

    for name in ("execution", "execution_process", "process_capability"):
        assert name not in env.values
