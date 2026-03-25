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
