import io
from pathlib import Path

import pytest

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


@pytest.mark.slow
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
        "\x1b[2J\x1b[H\x1b[1;1HGenia ants terminal UI\n"
        "[mode, pure, seed, 0, evolve, 0, steps_left, 4]\n"
        "[ants, 3, carrying, 0, delivered, 0, food_left, 24]\n"
        "[pheromone_total, 0, active_trails, 0, delay_ms, 80]\n"
        "legend: H carrying ant | a ant | N nest | * food | # + : pheromone high/med/low | . empty\n"
        "controls: CLI only (--seed --ants --steps --delay --size --mode pure|actor); no pause/step keys\n"
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


def test_terminal_config_parses_seed_steps_delay_size_and_mode():
    result = run_terminal_demo(
        """
        config = terminal_config(["--ants", "4", "--seed", "7", "--steps", "9", "--delay", "0", "--size", "21", "--mode", "actor"])
        [config_ant_count(config), config_seed(config), config_steps(config), config_delay(config), config_size(config), config_mode(config)]
        """
    )

    assert result == [4, 7, 9, 0, 21, "actor"]


def test_terminal_render_helpers_show_pheromone_heat_and_priority():
    result = run_terminal_demo(
        """
        world = new_terminal_world(7, 1, 20)
        trail = ants/set_pheromone(world, [0, 0], ants/pheromone_deposit() * 2)
        food = ants/set_food(trail, [1, 0], 2)
        nest = ants/world_nest(food)
        ant0 = ants/ant([2, 0], [1, 0], true)
        with_ant = ants/set_ants(food, [ant0])
        [
          pheromone_heat(1),
          pheromone_heat(ants/pheromone_deposit()),
          pheromone_heat(ants/pheromone_deposit() * 2),
          terminal_cell_char(with_ant, [0, 0]),
          terminal_cell_char(with_ant, [1, 0]),
          terminal_cell_char(with_ant, [2, 0]),
          terminal_cell_char(with_ant, nest)
        ]
        """
    )

    assert result == [":", "+", "#", "#", "*", "H", "N"]


def test_actor_mode_session_advances_and_stops():
    result = run_terminal_demo(
        """
        config = terminal_config(["--mode", "actor", "--ants", "2", "--seed", "7", "--steps", "1", "--delay", "0"])
        world = new_terminal_world(config_seed(config), config_ant_count(config), config_size(config))
        session = start_session(config_mode(config), world)
        session2 = session_step(config_mode(config), session)
        w = session_world(config_mode(config), session2)
        session_stop(config_mode(config), session2)
        [config_mode(config), ants/world_tick(w), length(ants/world_ants(w))]
        """
    )

    assert result == ["actor", 1, 2]
