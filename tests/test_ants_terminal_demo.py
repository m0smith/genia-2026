import io
from pathlib import Path

from genia import make_global_env, run_source


SOURCE_PATH = Path("examples/ants_terminal.genia")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
FILENAME = str(SOURCE_PATH.resolve())


def run_terminal_demo(src_suffix: str, *, stdout=None):
    env = make_global_env(stdout_stream=stdout or io.StringIO())
    return run_source(SOURCE + "\n" + src_suffix, env, filename=FILENAME)


def test_terminal_demo_collect_positions_is_seeded_and_reproducible():
    result = run_terminal_demo("collect_positions(7, 3, 3)")
    assert result == run_terminal_demo("collect_positions(7, 3, 3)")


def test_terminal_draw_frame_uses_terminal_helpers_and_rendered_world():
    stdout = io.StringIO()

    run_terminal_demo(
        """
        world = new_terminal_world(7, 3)
        draw_frame(world, 4, 20)
        """,
        stdout=stdout,
    )

    assert stdout.getvalue() == (
        "\x1b[2J\x1b[H\x1b[1;1H[ants, 3, grid, 20, x, 20, tick, 0, delivered, 0, steps_left, 4, use --ants N --seed S]\n"
        "....................\n"
        ".*................*.\n"
        "....................\n"
        "....................\n"
        "....................\n"
        "....................\n"
        "....................\n"
        "....................\n"
        "....................\n"
        ".........aaa........\n"
        ".........NNN........\n"
        ".........NNN........\n"
        "....................\n"
        "....................\n"
        "....................\n"
        "....................\n"
        "....................\n"
        "....................\n"
        ".*................*.\n"
        "...................."
    )


def test_terminal_demo_uses_imported_ants_logic():
    result = run_terminal_demo(
        """
        world = new_terminal_world(7, 3)
        [length(ants/world_ants(world)), ants/world_delivered(world), ants/world_tick(ants/step(world))]
        """
    )

    assert result == [3, 0, 1]
