from pathlib import Path

from genia import make_global_env, run_source


SOURCE_PATH = Path("examples/ants.genia")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
FILENAME = str(SOURCE_PATH.resolve())


def run_ants(src_suffix: str):
    return run_source(SOURCE + "\n" + src_suffix, make_global_env(), filename=FILENAME)


def test_ants_wrap_behavior():
    assert run_ants("[wrap(-1, 8), wrap(8, 8), wrap(3, 8)]") == [7, 0, 3]


def test_ants_same_seed_is_reproducible():
    result = run_ants("collect_signatures(7, 3)")
    assert result == run_ants("collect_signatures(7, 3)")


def test_ants_pure_world_step_preserves_food_accounting():
    result = run_ants(
        """
        world0 = new_world(7, 3, 7, 7)
        initial_food = total_food(world0)
        world1 = step(step(step(step(world0))))
        carried = length(filter((ant_value) -> ant_carrying?(ant_value), world_ants(world1)))
        [world_tick(world1), initial_food, total_food(world1) + world_delivered(world1) + carried]
        """
    )

    assert result == [4, 24, 24]


def test_ants_pick_up_food_and_reduce_cell_quantity():
    result = run_ants(
        """
        world = empty_world(7, 1, 5, 5)
        ant0 = ant([2, 2], [1, 0], false)
        world1 = set_ants(set_food(world, [3, 2], 2), [ant0])
        move = move_ant(world1, ant0, [[2, 1], [2, 3], [1, 2]])
        world_after(step_result) = ([world2, _, _]) -> world2
        ant_after(step_result) = ([_, ant2, _]) -> ant2
        world2 = world_after(move)
        ant2 = ant_after(move)
        [ant_pos(ant2), ant_carrying?(ant2), food_at(world2, [3, 2]), world_delivered(world2)]
        """
    )

    assert result == [[3, 2], True, 1, 0]


def test_ants_return_to_nest_and_deliver_food():
    result = run_ants(
        """
        world = empty_world(7, 1, 5, 5)
        ant0 = ant([3, 2], [-1, 0], true)
        world1 = set_ants(world, [ant0])
        world2 = step(world1)
        ant2 = first_ant(world2)
        [ant_pos(ant2), ant_carrying?(ant2), world_delivered(world2)]
        """
    )

    assert result == [[2, 2], False, 1]


def test_ants_deposit_pheromone_while_returning():
    result = run_ants(
        """
        world = empty_world(7, 1, 7, 5)
        ant0 = ant([5, 2], [-1, 0], true)
        world1 = set_ants(world, [ant0])
        world2 = step(world1)
        [ant_pos(first_ant(world2)), pheromone_at(world2, [4, 2]), world_delivered(world2)]
        """
    )

    assert result == [[4, 2], 6, 0]


def test_ants_pheromone_evaporates_toward_zero():
    result = run_ants(
        """
        world = set_pheromone(empty_world(7, 1, 5, 5), [1, 1], 4)
        world1 = evaporate(world)
        world2 = evaporate(world1)
        [pheromone_at(world1, [1, 1]), pheromone_at(world2, [1, 1])]
        """
    )

    assert result == [3, 2]


def test_ants_active_pheromone_tracking_removes_zeroed_trails():
    result = run_ants(
        """
        world = set_pheromone(empty_world(7, 1, 5, 5), [1, 1], 1)
        world1 = evaporate(world)
        [
          pheromone_at(world1, [1, 1]),
          pheromone_entries(world1),
          total_pheromone(world1),
          active_trail_count(world1),
          world_pheromone_positions(world1)
        ]
        """
    )

    assert result == [0, [], 0, 0, []]


def test_ants_pheromone_stats_track_active_cells_without_grid_scan():
    result = run_ants(
        """
        world0 = empty_world(7, 1, 20, 20)
        world1 = set_pheromone(world0, [18, 18], 4)
        world2 = set_pheromone(world1, [1, 1], 2)
        world3 = evaporate(world2)
        [
          pheromone_entries(world2),
          total_pheromone(world2),
          active_trail_count(world2),
          pheromone_entries(world3),
          total_pheromone(world3),
          active_trail_count(world3),
          length(world_pheromone_positions(world3))
        ]
        """
    )

    assert result == [
        [[[1, 1], 2], [[18, 18], 4]],
        6,
        2,
        [[[1, 1], 1], [[18, 18], 3]],
        4,
        2,
        2,
    ]


def test_ants_food_totals_and_entries_track_updates():
    result = run_ants(
        """
        world0 = empty_world(7, 1, 10, 10)
        world1 = set_food(world0, [8, 8], 3)
        world2 = set_food(world1, [1, 1], 2)
        world3 = take_food(take_food(world2, [1, 1]), [1, 1])
        [
          food_entries(world2),
          total_food(world2),
          food_entries(world3),
          total_food(world3),
          world_food_positions(world3)
        ]
        """
    )

    assert result == [
        [[[1, 1], 2], [[8, 8], 3]],
        5,
        [[[8, 8], 3]],
        3,
        [[8, 8]],
    ]


def test_ants_weighted_movement_prefers_food_and_forward_motion():
    result = run_ants(
        """
        world = empty_world(7, 1, 5, 5)
        ant0 = ant([2, 2], [1, 0], false)
        world1 = set_ants(set_food(world, [3, 2], 2), [ant0])
        weighted_move_view(world1, ant0, [])
        """
    )

    weights = {kind: weight for kind, _, weight in result}

    assert weights["forward"] > weights["left"]
    assert weights["forward"] > weights["right"]
    assert weights["forward"] > weights["back"]
    assert weights["forward"] > weights["stay"]
