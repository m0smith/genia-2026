import pytest

from pathlib import Path

from genia import make_global_env, run_source


TIC_TAC_TOE_PATH = Path("examples/tic-tac-toe.genia")


def run_tic_tac_toe_expression(expression: str):
    source = TIC_TAC_TOE_PATH.read_text(encoding="utf-8")
    env = make_global_env([], output_handler=lambda _text: None)
    return run_source(source + f"\n{expression}", env, filename=str(TIC_TAC_TOE_PATH.resolve()))


def test_sum_5th_example_refine_works():
    source = Path("examples/sum-5th.genia").read_text(encoding="utf-8")
    env = make_global_env(
        stdin_data=[
            "a b c d 5 x\n",
            "1 2 3 4 6 y\n",
            "short\n",
        ]
    )
    # Should sum 5 + 6 = 11 using refine/step_emit
    assert run_source(source, env, filename=str(Path("examples/sum-5th.genia").resolve())) == 11


def test_sum_5th_example_uses_autoloaded_fields_and_structured_absence():
    source = Path("examples/sum-5th.genia").read_text(encoding="utf-8")
    env = make_global_env(
        stdin_data=[
            "a b c d 5 x\n",
            "1 2 3 4 6 y\n",
            "short\n",
        ]
    )

    assert run_source(source, env, filename=str(Path("examples/sum-5th.genia").resolve())) == 11


def test_tic_tac_toe_example_runs_to_x_win(monkeypatch):
    source_path = TIC_TAC_TOE_PATH
    source = source_path.read_text(encoding="utf-8")
    outputs: list[str] = []
    prompts: list[str] = []
    moves = iter(["0", "3", "1", "4", "2"])

    def fake_input(prompt=""):
        prompts.append(prompt)
        return next(moves)

    monkeypatch.setattr("builtins.input", fake_input)
    env = make_global_env([], output_handler=outputs.append)

    result = run_source(source + "\nmain()", env, filename=str(source_path.resolve()))
    transcript = "".join(outputs)

    assert result == "X wins!"
    assert prompts[0] == "Player X, enter a move from 0 to 8:"
    assert "Tic-Tac-Toe\n" in transcript
    assert "0 1 2\n" in transcript
    assert outputs[-1] == "X wins!\n"


def test_tic_tac_toe_example_retries_invalid_move(monkeypatch):
    source_path = TIC_TAC_TOE_PATH
    source = source_path.read_text(encoding="utf-8")
    outputs: list[str] = []
    moves = iter(["oops", "0", "3", "1", "4", "2"])

    monkeypatch.setattr("builtins.input", lambda prompt="": next(moves))
    env = make_global_env([], output_handler=outputs.append)

    run_source(source + "\nmain()", env, filename=str(source_path.resolve()))
    transcript = "".join(outputs)

    assert transcript.count("That square is not available. Try again.\n") == 1
    assert outputs[-1] == "X wins!\n"


def test_tic_tac_toe_example_uses_format_for_rows():
    source = TIC_TAC_TOE_PATH.read_text(encoding="utf-8")

    assert "Format(" in source
    assert "format(" in source
    assert "showSquare(a) + \" \" + showSquare(b)" not in source
    assert run_tic_tac_toe_expression('formatRow("X", "_", "O")') == "X _ O"


def test_tic_tac_toe_winning_lines_are_explicit_data():
    assert run_tic_tac_toe_expression("winningLines()") == [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [2, 4, 6],
    ]


def test_tic_tac_toe_winner_contract_covers_empty_rows_columns_and_diagonals():
    assert run_tic_tac_toe_expression("winner(newBoard())") == "_"
    assert run_tic_tac_toe_expression('winner(["X", "X", "X", "_", "_", "_", "_", "_", "_"])') == "X"
    assert run_tic_tac_toe_expression('winner(["_", "O", "_", "_", "O", "_", "_", "O", "_"])') == "O"
    assert run_tic_tac_toe_expression('winner(["_", "_", "O", "_", "O", "_", "O", "_", "_"])') == "O"


def test_tic_tac_toe_example_runs_to_o_win(monkeypatch):
    source = TIC_TAC_TOE_PATH.read_text(encoding="utf-8")
    outputs: list[str] = []
    moves = iter(["0", "3", "1", "4", "8", "5"])

    monkeypatch.setattr("builtins.input", lambda prompt="": next(moves))
    env = make_global_env([], output_handler=outputs.append)

    result = run_source(source + "\nmain()", env, filename=str(TIC_TAC_TOE_PATH.resolve()))

    assert result == "O wins!"
    assert outputs[-1] == "O wins!\n"


def test_tic_tac_toe_example_runs_to_draw(monkeypatch):
    source = TIC_TAC_TOE_PATH.read_text(encoding="utf-8")
    outputs: list[str] = []
    moves = iter(["0", "1", "2", "4", "3", "5", "7", "6", "8"])

    monkeypatch.setattr("builtins.input", lambda prompt="": next(moves))
    env = make_global_env([], output_handler=outputs.append)

    result = run_source(source + "\nmain()", env, filename=str(TIC_TAC_TOE_PATH.resolve()))

    assert result == "Draw!"
    assert outputs[-1] == "Draw!\n"


def test_tic_tac_toe_example_occupied_square_retries_same_player(monkeypatch):
    source = TIC_TAC_TOE_PATH.read_text(encoding="utf-8")
    outputs: list[str] = []
    prompts: list[str] = []
    moves = iter(["0", "0", "3", "1", "4", "2"])

    def fake_input(prompt=""):
        prompts.append(prompt)
        return next(moves)

    monkeypatch.setattr("builtins.input", fake_input)
    env = make_global_env([], output_handler=outputs.append)

    run_source(source + "\nmain()", env, filename=str(TIC_TAC_TOE_PATH.resolve()))

    assert "That square is not available. Try again.\n" in outputs
    assert prompts[:3] == [
        "Player X, enter a move from 0 to 8:",
        "Player O, enter a move from 0 to 8:",
        "Player O, enter a move from 0 to 8:",
    ]
    assert outputs[-1] == "X wins!\n"


@pytest.mark.slow
def test_ants_terminal_demo_parses_configurable_ant_count():
    source_path = Path("examples/ants_terminal.genia")
    source = source_path.read_text(encoding="utf-8")

    env = make_global_env()
    assert run_source(source + '\nant_count(["--ants", "3"])', env, filename=str(source_path.resolve())) == 3

    env = make_global_env()
    assert run_source(source + '\nant_count(["-a", "2"])', env, filename=str(source_path.resolve())) == 2

    env = make_global_env()
    assert run_source(source + '\nant_count(["--ants", "nope"])', env, filename=str(source_path.resolve())) == 6

    env = make_global_env()
    assert run_source(source + "\ngrid_size(3)", env, filename=str(source_path.resolve())) == 20

    env = make_global_env()
    assert run_source(source + "\ngrid_size(25)", env, filename=str(source_path.resolve())) == 25


@pytest.mark.slow
def test_ants_terminal_demo_parses_seed_option():
    source_path = Path("examples/ants_terminal.genia")
    source = source_path.read_text(encoding="utf-8")

    env = make_global_env()
    assert run_source(source + '\nseed_arg(["--seed", "7"])', env, filename=str(source_path.resolve())) == 7

    env = make_global_env()
    assert run_source(source + '\nseed_arg(["-s", "5"])', env, filename=str(source_path.resolve())) == 5

    env = make_global_env()
    assert run_source(source + '\nseed_arg(["--seed", "oops"])', env, filename=str(source_path.resolve())) == 0
