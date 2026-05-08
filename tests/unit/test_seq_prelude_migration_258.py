"""Failing tests for issue #258 seq prelude migration.

The contract keeps public sequence behavior on the prelude surface while
Python-host kernels remain internal substrate only. These tests intentionally
fail before implementation because the underscore sequence kernels are still
resolvable from user code.
"""

import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def run(src: str):
    env = make_global_env([])
    return run_source(src, env)


class TestInternalSeqKernelsNotPublic:
    """Internal sequence kernels must not be user-callable public helpers."""

    def test_prelude_shaped_filename_does_not_grant_collect_access(self):
        env = make_global_env([])
        with pytest.raises(Exception, match="(?i)_collect|undefined|not defined|NameError"):
            run_source("_collect([1, 2])", env, filename="std/prelude/user.genia")

    def test_prelude_shaped_filename_does_not_grant_run_access(self):
        env = make_global_env([])
        with pytest.raises(Exception, match="(?i)_run|undefined|not defined|NameError"):
            run_source("_run([1, 2])", env, filename="std/prelude/user.genia")

    def test_seq_transform_internal_kernel_not_registered(self):
        src = """
        step(state, item) = { emit: [item], state: state }
        _seq_transform(nil, step, [1, 2])
        """
        with pytest.raises(Exception, match="(?i)_seq_transform|undefined|not defined|NameError"):
            run(src)

    def test_evolve_internal_kernel_not_registered(self):
        src = "_evolve(0, (n) -> n + 1) |> take(2) |> collect"
        with pytest.raises(Exception, match="(?i)_evolve|undefined|not defined|NameError"):
            run(src)

    def test_scan_internal_kernel_not_registered(self):
        src = """
        evolve(0, (n) -> n + 1)
          |> _scan((state, item) -> [state + item, state + item], 0)
          |> take(2)
          |> collect
        """
        with pytest.raises(Exception, match="(?i)_scan|undefined|not defined|NameError"):
            run(src)

    def test_each_internal_kernel_not_registered(self):
        with pytest.raises(Exception, match="(?i)_each|undefined|not defined|NameError"):
            run("_each((x) -> nil, [1, 2])")

    def test_collect_internal_kernel_not_registered(self):
        with pytest.raises(Exception, match="(?i)_collect|undefined|not defined|NameError"):
            run("_collect([1, 2])")

    def test_run_internal_kernel_not_registered(self):
        with pytest.raises(Exception, match="(?i)_run|undefined|not defined|NameError"):
            run("_run([1, 2])")


class TestPublicSeqHelpersRemainUsable:
    """Public prelude-backed helpers stay available while internals move away."""

    def test_public_list_helpers_still_work(self):
        src = """
        [
          map((x) -> x + 1, [1, 2, 3]),
          filter((x) -> x > 1, [1, 2, 3]),
          take(2, [1, 2, 3]),
          drop(1, [1, 2, 3])
        ]
        """
        assert run(src) == [[2, 3, 4], [2, 3], [1, 2], [2, 3]]

    def test_public_flow_helpers_still_work(self):
        src = """
        evolve(0, (n) -> n + 1)
          |> scan((state, item) -> [state + item, state + item], 0)
          |> take(4)
          |> collect
        """
        assert run(src) == [0, 1, 3, 6]

    def test_public_seq_terminal_helpers_still_work(self):
        src = """
        seen = ref([])
        result = each((x) -> ref_set(seen, [..ref_get(seen), x]), [1, 2]) |> collect
        [result, collect([3, 4]), run([5, 6]), ref_get(seen)]
        """
        result = run(src)
        assert result[0] == [1, 2]
        assert result[1] == [3, 4]
        assert format_debug(result[2]) == 'none("nil")'
        assert result[3] == [1, 2]
