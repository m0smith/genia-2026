from pathlib import Path

from genia import make_global_env, run_source


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
    source_path = Path("examples/tic-tac-toe.genia")
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
    source_path = Path("examples/tic-tac-toe.genia")
    source = source_path.read_text(encoding="utf-8")
    outputs: list[str] = []
    moves = iter(["oops", "0", "3", "1", "4", "2"])

    monkeypatch.setattr("builtins.input", lambda prompt="": next(moves))
    env = make_global_env([], output_handler=outputs.append)

    run_source(source + "\nmain()", env, filename=str(source_path.resolve()))
    transcript = "".join(outputs)

    assert transcript.count("That square is not available. Try again.\n") == 1
    assert outputs[-1] == "X wins!\n"


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
