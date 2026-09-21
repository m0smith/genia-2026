"""End-to-end proof that `execution.process` is reachable from Genia source
exactly the way the design anticipated, and grants no ambient authority.

This file started life in the failing-test phase (PR #979) as
`test_execution_process_genia_surface_absent.py`, proving `import
execution` failed with `FileNotFoundError` because nothing existed yet.
Its own docstring at the time said: "Once `execution.process` is
implemented and wired into module resolution, this exact test (unmodified)
should start reporting a DIFFERENT failure shape than today's... adapt its
assertions to the real success path in the implementation phase's own test
updates." This is that adaptation, done in the implementation phase per
that explicit self-documented instruction -- not an opportunistic weakening
of a RED test.

Implementation phase: `import execution` now resolves to
`src/genia/std/prelude/execution.genia`, exactly like `import web`/`import
resource` resolve to their own packaged prelude modules (no second
module-loading mechanism was added -- see `docs/design/execution-process-design.md`
§13/§25).
"""

from __future__ import annotations

from genia.builtins import make_global_env
from genia.interpreter import run_source
from genia.process_capability import create_process_capability
from genia.process_transport import launch_process


def test_importing_execution_module_now_succeeds_and_exposes_process():
    env = make_global_env([])

    result = run_source("import execution\nexecution.process", env)

    # `execution.process` resolves to an ordinary callable value, not an
    # error -- proving the module now exists and exports `process`.
    assert result is not None


def test_execution_process_is_callable_from_ordinary_genia_source():
    """Full stack: Genia source -> prelude `process(...)` -> the private
    `_execution_process` builtin -> `perform_process_execution` -> the
    opaque capability's launcher -> `launch_process`.
    """
    env = make_global_env([])
    capability = create_process_capability(
        bindings={},
        authorized=lambda _symbol: True,
        launcher=lambda target, args, timeout_ms: launch_process(target, args, timeout_ms),
    )
    env.set("fixture_capability", capability)

    result = run_source(
        "import execution\n"
        "execution.process(fixture_capability, {executable: quote(unbound), "
        'args: [], timeout_ms: 1000})',
        env,
    )

    from genia.values import GeniaOptionErr

    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "process-executable-unavailable"


def test_global_environment_has_no_ambient_ready_to_use_capability():
    """No file, command, pipe, import, REPL, test, or server mode may
    provision a usable capability implicitly (contract §3): there is no
    ambient `execution`/`execution_process` value and no global `host`
    object or `host.supports(...)` operation. The only global binding is
    the private raw builtin (`_execution_process`), which still requires
    an explicit, real capability argument and grants no authority by
    itself -- see `test_ambient_builtin_grants_no_authority_without_a_real_capability`.
    """
    env = make_global_env([])

    for name in ("execution", "execution_process", "process_capability", "host"):
        assert name not in env.values


def test_ambient_builtin_grants_no_authority_without_a_real_capability():
    env = make_global_env([])
    import pytest

    with pytest.raises(TypeError):
        run_source(
            'import execution\nexecution.process("not-a-capability", '
            '{executable: quote(x), args: [], timeout_ms: 1000})',
            env,
        )
