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
