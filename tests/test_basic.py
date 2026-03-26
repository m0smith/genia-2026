def test_basic(run):
    assert run("1+2") == 3


def test_input_builtin_returns_user_text(run, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "typed value")
    assert run('input("Prompt: ")') == "typed value"


def test_input_builtin_passes_prompt(run, monkeypatch):
    prompts: list[str] = []

    def fake_input(prompt=""):
        prompts.append(prompt)
        return "ok"

    monkeypatch.setattr("builtins.input", fake_input)
    assert run('input("Enter value: ")') == "ok"
    assert prompts == ["Enter value: "]


def test_stdin_builtin_is_callable_and_returns_lines():
    from genia import make_global_env, run_source

    env = make_global_env(stdin_data=["a", "b"])
    assert run_source("stdin()", env) == ["a", "b"]


def test_stdin_builtin_is_lazy():
    calls = 0

    def provider():
        nonlocal calls
        calls += 1
        return ["x", "y"]

    from genia import make_global_env, run_source

    env = make_global_env(stdin_provider=provider)
    assert calls == 0
    assert run_source("1 + 1", env) == 2
    assert calls == 0
    assert run_source("stdin()", env) == ["x", "y"]
    assert calls == 1
    assert run_source("stdin()", env) == ["x", "y"]
    assert calls == 1
