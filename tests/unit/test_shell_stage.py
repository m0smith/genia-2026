"""Tests for the experimental $(...) shell pipeline stage.

Covers: happy path, stdin materialization, failure cases,
Option propagation, error quality, and regression coverage.
"""

import pytest
from genia import make_global_env, run_source
from genia.interpreter import GeniaOptionNone, GeniaOptionSome


@pytest.fixture
def env():
    return make_global_env()


def run(env, source):
    return run_source(source, env)


# ---------------------------------------------------------------------------
# 1. Happy path — shell stage works in a pipeline
# ---------------------------------------------------------------------------


class TestShellStageHappyPath:
    def test_string_through_cat(self, env):
        assert run(env, '"hello" |> $(cat)') == "hello"

    def test_string_through_tr(self, env):
        assert run(env, '"hello" |> $(tr a-z A-Z)') == "HELLO"

    def test_multi_stage_shell_pipeline(self, env):
        result = run(env, '"hello world" |> $(tr a-z A-Z) |> $(cat)')
        assert result == "HELLO WORLD"

    def test_shell_output_feeds_genia_stage(self, env):
        """Shell stdout becomes the next pipeline value for a Genia stage."""
        src = '''
        upcase(s) = s
        "hello" |> $(cat) |> upcase
        '''
        assert run(env, src) == "hello"

    def test_genia_stage_feeds_shell_stage(self, env):
        """A Genia function result becomes stdin for the next shell stage."""
        src = '''
        upcase(x) = x
        "hello" |> upcase |> $(tr a-z A-Z)
        '''
        assert run(env, src) == "HELLO"

    def test_trailing_newline_stripped(self, env):
        """A single trailing newline in stdout is stripped."""
        # echo produces "hello\n"; only one trailing \n should be stripped
        result = run(env, '"" |> $(echo hello)')
        assert result == "hello"

    def test_only_one_trailing_newline_is_stripped(self, env):
        """Multiple trailing newlines lose only one final newline."""
        result = run(env, '"" |> $(printf \'hello\\n\\n\')')
        assert result == "hello\n"

    def test_multiple_output_lines_preserved(self, env):
        """Non-trailing newlines are preserved in stdout."""
        result = run(env, '"a\\nb" |> $(cat)')
        assert result == "a\nb"


# ---------------------------------------------------------------------------
# 2. Stdin materialization — pipeline value → stdin bytes
# ---------------------------------------------------------------------------


class TestShellStageStdinMaterialization:
    def test_string_stdin(self, env):
        assert run(env, '"hello" |> $(cat)') == "hello"

    def test_integer_stdin(self, env):
        assert run(env, '42 |> $(cat)') == "42"

    def test_float_stdin(self, env):
        assert run(env, '3.14 |> $(cat)') == "3.14"

    def test_bool_true_stdin(self, env):
        assert run(env, 'true |> $(cat)') == "true"

    def test_bool_false_stdin(self, env):
        assert run(env, 'false |> $(cat)') == "false"

    def test_list_stdin_newline_joined(self, env):
        assert run(env, '["a", "b", "c"] |> $(cat)') == "a\nb\nc"

    def test_empty_list_stdin(self, env):
        """Empty list produces empty stdin → empty stdout → none."""
        result = run(env, '[] |> $(cat)')
        assert isinstance(result, GeniaOptionNone)

    def test_flow_stdin_materialized(self, env):
        """Flow values are consumed and newline-joined for stdin."""
        flow_env = make_global_env(stdin_data=["alpha", "beta"])
        result = run(flow_env, 'stdin |> lines |> $(cat)')
        assert result == "alpha\nbeta"

    def test_empty_string_stdin(self, env):
        """Empty string produces empty stdin → empty stdout → none."""
        result = run(env, '"" |> $(cat)')
        assert isinstance(result, GeniaOptionNone)

    def test_unsupported_type_raises_typeerror(self, env):
        """A map/dict passed to shell stage should raise TypeError."""
        with pytest.raises(TypeError, match="cannot convert"):
            run(env, '{"a": 1} |> $(cat)')


# ---------------------------------------------------------------------------
# 3. Empty output
# ---------------------------------------------------------------------------


class TestShellStageEmptyOutput:
    def test_empty_stdout_returns_none(self, env):
        result = run(env, '"x" |> $(tr -d x)')
        assert isinstance(result, GeniaOptionNone)

    def test_empty_output_none_reason(self, env):
        """The none reason for empty output is 'empty-shell-output'."""
        result = run(env, '"x" |> $(tr -d x)')
        assert isinstance(result, GeniaOptionNone)
        assert result.reason == "empty-shell-output"


# ---------------------------------------------------------------------------
# 4. Option propagation
# ---------------------------------------------------------------------------


class TestShellStageOptionPropagation:
    def test_none_propagates_without_execution(self, env, tmp_path):
        """none(...) short-circuits — the shell command is not executed."""
        marker = tmp_path / "shell-stage-short-circuit-marker"
        src = f'none("skip") |> $(touch "{marker}")'
        result = run(env, src)
        assert isinstance(result, GeniaOptionNone)
        assert result.reason == "skip"
        assert not marker.exists()

    def test_none_with_meta_propagates(self, env):
        result = run(env, 'none("reason") |> $(cat)')
        assert isinstance(result, GeniaOptionNone)
        assert result.reason == "reason"

    def test_some_unwraps_and_rewraps(self, env):
        result = run(env, 'some("hello") |> $(cat)')
        assert isinstance(result, GeniaOptionSome)
        assert result.value == "hello"

    def test_some_empty_output_returns_none(self, env):
        """some(x) → shell → empty stdout → none (not re-wrapped in some)."""
        result = run(env, 'some("x") |> $(tr -d x)')
        assert isinstance(result, GeniaOptionNone)

    def test_shell_stage_none_short_circuits_subsequent_stages(self, env):
        """A none from a shell stage short-circuits later pipeline stages."""
        src = '''
        boom(x) = x / 0
        "x" |> $(tr -d x) |> boom
        '''
        result = run(env, src)
        assert isinstance(result, GeniaOptionNone)


# ---------------------------------------------------------------------------
# 5. Failure cases
# ---------------------------------------------------------------------------


class TestShellStageFailures:
    def test_nonzero_exit_raises_runtime_error(self, env):
        with pytest.raises(RuntimeError, match="command failed"):
            run(env, '"x" |> $(false)')

    def test_nonzero_exit_includes_exit_code(self, env):
        with pytest.raises(RuntimeError, match="exit 1"):
            run(env, '"x" |> $(exit 1)')

    def test_nonzero_exit_includes_command(self, env):
        with pytest.raises(RuntimeError, match="exit 42"):
            run(env, '"x" |> $(exit 42)')

    def test_command_not_found_raises(self, env):
        with pytest.raises(RuntimeError):
            run(env, '"x" |> $(this_command_does_not_exist_xyz_99)')

    def test_shell_stage_outside_pipeline_raises_syntax_error(self, env):
        with pytest.raises(SyntaxError, match="only valid as a pipeline stage"):
            run(env, "$(echo hi)")

    def test_shell_stage_standalone_in_let_raises(self, env):
        with pytest.raises(SyntaxError, match="only valid as a pipeline stage"):
            run(env, 'x = $(echo hi)')


# ---------------------------------------------------------------------------
# 6. Lexer / syntax edge cases
# ---------------------------------------------------------------------------


class TestShellStageLexer:
    def test_balanced_parens_in_command(self, env):
        result = run(env, '"test" |> $(echo "(hello)")')
        assert "(hello)" in result

    def test_empty_command_rejected(self, env):
        with pytest.raises(SyntaxError, match="empty command"):
            run(env, '"x" |> $()')

    def test_whitespace_only_command_rejected(self, env):
        with pytest.raises(SyntaxError, match="empty command"):
            run(env, '"x" |> $(   )')

    def test_unterminated_rejected(self, env):
        with pytest.raises(SyntaxError, match="Unterminated"):
            run(env, '"x" |> $(echo hi')

    def test_nested_shell_stage_rejected(self, env):
        with pytest.raises(SyntaxError, match="nested"):
            run(env, '"x" |> $(echo $(inner))')

    def test_command_with_spaces_preserved(self, env):
        result = run(env, '"" |> $(echo "a  b")')
        assert "a  b" in result


# ---------------------------------------------------------------------------
# 7. Error quality
# ---------------------------------------------------------------------------


class TestShellStageErrorQuality:
    def test_runtime_error_type_on_nonzero(self, env):
        """Non-zero exit produces RuntimeError, not a generic Exception."""
        with pytest.raises(RuntimeError):
            run(env, '"x" |> $(false)')

    def test_syntax_error_type_outside_pipeline(self, env):
        """Usage outside pipeline produces SyntaxError."""
        with pytest.raises(SyntaxError):
            run(env, "$(echo hi)")

    def test_type_error_on_unconvertible_input(self, env):
        """Unconvertible stdin type produces TypeError."""
        with pytest.raises(TypeError):
            run(env, '{"a": 1} |> $(cat)')

    def test_nonzero_exit_message_format(self, env):
        """Error message follows the contract format."""
        with pytest.raises(
            RuntimeError,
            match=r"shell stage: command failed \(exit \d+\):",
        ):
            run(env, '"x" |> $(false)')


# ---------------------------------------------------------------------------
# 8. Regression coverage — ordinary pipelines unaffected
# ---------------------------------------------------------------------------


class TestShellStageRegressionCoverage:
    def test_ordinary_pipeline_still_works(self, env):
        src = """
        inc(x) = x + 1
        double(x) = x * 2
        3 |> inc |> double
        """
        assert run(env, src) == 8

    def test_pipeline_none_shortcircuit_unchanged(self, env):
        src = '''
        inc(x) = x + 1
        none("gone") |> inc
        '''
        result = run(env, src)
        assert isinstance(result, GeniaOptionNone)
        assert result.reason == "gone"

    def test_pipeline_some_lifting_unchanged(self, env):
        src = """
        inc(x) = x + 1
        some(4) |> inc
        """
        result = run(env, src)
        assert isinstance(result, GeniaOptionSome)
        assert result.value == 5

    def test_flow_pipeline_still_works(self):
        flow_env = make_global_env(stdin_data=["hello", "world"])
        result = run(flow_env, 'stdin |> lines |> collect')
        assert result == ["hello", "world"]

    def test_mixed_shell_and_genia_pipeline(self, env):
        """Shell and Genia stages coexist in one pipeline."""
        src = '''
        add1(x) = x + 1
        unwrap_or(0, "5" |> $(cat) |> parse_int) |> add1
        '''
        assert run(env, src) == 6

    def test_dollar_identifier_not_broken(self, env):
        """$ as part of identifiers is unaffected when not followed by (."""
        # $foo is a valid identifier start in Genia
        src = """
        $x = 42
        $x + 1
        """
        assert run(env, src) == 43
