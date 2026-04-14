import io
from pathlib import Path

from genia import make_global_env, run_source


SOURCE_PATH = Path("examples/ants_terminal.genia")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
FILENAME = str(SOURCE_PATH.resolve())


def run_terminal_demo(src_suffix: str, *, stdout=None):
    env = make_global_env(stdout_stream=stdout or io.StringIO())
    return run_source(SOURCE + "\n" + src_suffix, env, filename=FILENAME)


def test_terminal_ants_block_on_occupied_target():
    result = run_terminal_demo(
        """
        world = place_ant(place_ant(map_new(), [1, 1]), [2, 1])
        result = step_target(world, [1, 1], [2, 1])

        world_after(step) = ([world2, _, _]) -> world2
        pos_after(step) = ([_, ant_pos2, _]) -> ant_pos2
        event_after(step) = ([_, _, event]) -> event

        [
          pos_after(result),
          event_after(result),
          cell_get(world_after(result), [1, 1]),
          cell_get(world_after(result), [2, 1])
        ]
        """
    )

    assert result == [[1, 1], "blocked", "ant", "ant"]


def test_terminal_ants_consume_food_and_update_world_state():
    result = run_terminal_demo(
        """
        world = place_ant(seed_world(), [1, 0])
        result = step_target(world, [1, 0], [0, 0])

        world_after(step) = ([world2, _, _]) -> world2
        pos_after(step) = ([_, ant_pos2, _]) -> ant_pos2
        event_after(step) = ([_, _, event]) -> event

        [
          pos_after(result),
          event_after(result),
          cell_get(world_after(result), [1, 0]),
          cell_get(world_after(result), [0, 0])
        ]
        """
    )

    assert result == [[0, 0], "ate_food", "empty", "ant"]


def test_terminal_step_ants_keeps_world_and_positions_in_sync():
    result = run_terminal_demo(
        """
        random_dir = () -> [1, 0]

        world = place_ant(place_ant(map_new(), [1, 1]), [2, 1])
        result = step_ants(world, [[1, 1], [2, 1]], 5)

        world_after(step) = ([world2, _]) -> world2
        ants_after(step) = ([_, ants2]) -> ants2

        [
          ants_after(result),
          cell_get(world_after(result), [1, 1]),
          cell_get(world_after(result), [2, 1]),
          cell_get(world_after(result), [3, 1])
        ]
        """
    )

    assert result == [[[1, 1], [3, 1]], "ant", "empty", "ant"]


def test_terminal_draw_frame_uses_terminal_helpers_and_world_rendering():
    stdout = io.StringIO()

    run_terminal_demo(
        """
        world = place_ant(cell_put(seed_world(), [0, 0], empty_cell()), [0, 0])
        draw_frame(world, [[0, 0]], 7, 4)
        """,
        stdout=stdout,
    )

    assert stdout.getvalue() == (
        "\x1b[2J\x1b[H\x1b[1;1H[ants, 1, grid, 4, x, 4, steps_left, 7, use --ants N or -a N]\n"
        "A...\n"
        "....\n"
        "....\n"
        "...."
    )


def test_terminal_ants_collect_positions_is_seeded_and_reproducible():
    result = run_terminal_demo("collect_positions(7, 3, 4)")

    assert result == [
        [[18, 17], [16, 11], [14, 9]],
        [[19, 17], [16, 10], [14, 10]],
        [[18, 17], [17, 10], [14, 9]],
        [[18, 18], [16, 10], [15, 9]],
        [[18, 17], [16, 11], [14, 9]],
    ]
