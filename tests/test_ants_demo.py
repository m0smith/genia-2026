ANTS_CORE = """
width() = 8
height() = 5

empty_cell() = "empty"
food_cell() = "food"
ant_cell() = "ant"

wrap(n, size) =
  (n, size) ? n < 0 -> size - 1 |
  (n, size) ? n >= size -> 0 |
  (n, _) -> n

pos_add(pos, delta) =
  ([x, y], [dx, dy]) -> [
    wrap(x + dx, width()),
    wrap(y + dy, height())
  ]

cell_get(world, pos) =
  (world, pos) ? map_has?(world, pos) -> map_get(world, pos) |
  (_, _) -> empty_cell()

cell_put(world, pos, value) = map_put(world, pos, value)

move_ant(world, from, to) =
  cell_put(cell_put(world, from, empty_cell()), to, ant_cell())

step_target(world, ant_pos, target) =
  step_cell(world, ant_pos, target, cell_get(world, target))

step_cell(world, ant_pos, target, target_cell) =
  (world, ant_pos, target, "ant") -> [world, ant_pos, "blocked"] |
  (world, ant_pos, target, "food") -> [move_ant(world, ant_pos, target), target, "ate_food"] |
  (world, ant_pos, target, _) -> [move_ant(world, ant_pos, target), target, "moved"]
"""


def test_ants_wrap_behavior(run):
    src = ANTS_CORE + "\n[wrap(-1, 8), wrap(8, 8), wrap(3, 8)]"
    assert run(src) == [7, 0, 3]


def test_ants_position_update_with_wrapping(run):
    src = ANTS_CORE + "\n[pos_add([7, 4], [1, 1]), pos_add([0, 0], [-1, -1])]"
    assert run(src) == [[0, 0], [7, 4]]


def test_ants_move_ant_returns_updated_world(run):
    src = (
        ANTS_CORE
        + '\n'
        + 'w0 = map_put(map_new(), [1, 1], "ant")\n'
        + 'w1 = move_ant(w0, [1, 1], [2, 1])\n'
        + '[cell_get(w0, [1, 1]), cell_get(w1, [1, 1]), cell_get(w1, [2, 1])]'
    )
    assert run(src) == ["ant", "empty", "ant"]


def test_ants_missing_cell_defaults_to_empty(run):
    src = ANTS_CORE + '\ncell_get(map_new(), [99, 99])'
    assert run(src) == "empty"


def test_ants_step_target_result_shape_and_event(run):
    src = (
        ANTS_CORE
        + '\n'
        + 'w0 = map_put(map_new(), [2, 2], "ant")\n'
        + 'step_target(w0, [2, 2], [3, 2])'
    )
    result = run(src)
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[1] == [3, 2]
    assert result[2] == "moved"


def test_ants_example_collect_events_is_seeded_and_reproducible():
    from pathlib import Path

    from genia import make_global_env, run_source

    source_path = Path("examples/ants.genia")
    source = source_path.read_text(encoding="utf-8")
    env = make_global_env()

    result = run_source(source + "\ncollect_events(7, 6)", env, filename=str(source_path.resolve()))

    assert result == [
        [[2, 3], "moved"],
        [[1, 3], "moved"],
        [[2, 3], "moved"],
        [[2, 2], "moved"],
        [[2, 3], "moved"],
        [[1, 3], "moved"],
    ]
