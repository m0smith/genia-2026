"""Tests for the actor/coordinator ants simulation demo.

Covers:
1. Coordinator owns world truth
2. Actor-mode ant can request sense data and submit intent
3. Food pickup/delivery works in actor mode
4. Actor-mode world is reproducible under explicit tick order
5. Key invariants: total food accounting, delivered food monotonic
"""

from pathlib import Path

from genia import make_global_env, run_source


SOURCE_PATH = Path("examples/ants_actor.genia")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
FILENAME = str(SOURCE_PATH.resolve())


def run_actor(src_suffix: str):
    return run_source(SOURCE + "\n" + src_suffix, make_global_env(), filename=FILENAME)


# --- Coordinator owns world truth ---


def test_coordinator_snapshot_returns_world():
    """Coordinator replies to snapshot with the current world."""
    result = run_actor(
        """
        world = ants/new_world(7, 2, 5, 5)
        coord = actor(world, coordinator_handler)
        snap = actor_call(coord, ["snapshot"])
        w = snapshot_world(snap)
        actor_call(coord, ["stop"])
        ants/world_tick(w)
        """
    )
    assert result == 0


def test_coordinator_tick_increments_tick_counter():
    """Coordinator tick message increments the world tick count."""
    result = run_actor(
        """
        world = ants/new_world(7, 2, 5, 5)
        coord = actor(world, coordinator_handler)
        actor_call(coord, ["tick"])
        actor_call(coord, ["tick"])
        snap = actor_call(coord, ["snapshot"])
        w = snapshot_world(snap)
        actor_call(coord, ["stop"])
        ants/world_tick(w)
        """
    )
    assert result == 2


# --- Ant sense/move cycle ---


def test_ant_sense_returns_weighted_candidates():
    """Sense reply contains weighted candidate moves for the ant."""
    result = run_actor(
        """
        world = ants/new_world(7, 2, 5, 5)
        coord = actor(world, coordinator_handler)
        reply = actor_call(coord, ["sense", 0])
        check(r) = (["sense_reply", _, _, weighted]) -> length(weighted) > 0
        result = check(reply)
        actor_call(coord, ["stop"])
        result
        """
    )
    assert result is True


def test_ant_move_intent_updates_world():
    """Move intent via coordinator applies the move and returns a tag."""
    result = run_actor(
        """
        world = ants/new_world(7, 2, 5, 5)
        coord = actor(world, coordinator_handler)
        sense = actor_call(coord, ["sense", 0])
        get_weighted(r) = (["sense_reply", _, _, w]) -> w
        weighted = get_weighted(sense)
        first_entry = fst(weighted)
        chosen_move = snd(first_entry)
        move_result = actor_call(coord, ["move_intent", 0, chosen_move])
        snap = actor_call(coord, ["snapshot"])
        w = snapshot_world(snap)
        count = length(ants/world_ants(w))
        actor_call(coord, ["stop"])
        count
        """
    )
    assert result == 2


# --- Full simulation ---


def test_run_actor_sim_returns_world():
    """run_actor_sim returns a world map after the given number of ticks."""
    result = run_actor(
        """
        world = ants/new_world(7, 2, 5, 5)
        w = run_actor_sim(world, 3)
        ants/world_tick(w)
        """
    )
    assert result == 3


def test_actor_sim_same_seed_is_reproducible():
    """Same seed produces the same world summary after the same tick count."""
    result1 = run_actor("world_summary(run_actor_sim(ants/new_world(7, 3, 5, 5), 5))")
    result2 = run_actor("world_summary(run_actor_sim(ants/new_world(7, 3, 5, 5), 5))")
    assert result1 == result2


def test_actor_sim_different_seed_differs():
    """Different seeds produce different outcomes."""
    result1 = run_actor("world_summary(run_actor_sim(ants/new_world(7, 3, 5, 5), 5))")
    result2 = run_actor("world_summary(run_actor_sim(ants/new_world(42, 3, 5, 5), 5))")
    assert result1 != result2


def test_collect_actor_summaries_length():
    """collect_actor_summaries returns one entry per tick plus a final snapshot."""
    result = run_actor("length(collect_actor_summaries(7, 2, 4))")
    # 4 ticks + 1 final = 5 summaries
    assert result == 5


def test_collect_actor_summaries_tick_increases():
    """Tick counter in summaries increases monotonically."""
    result = run_actor(
        """
        summaries = collect_actor_summaries(7, 2, 3)
        map(fst, summaries)
        """
    )
    # [0, 1, 2, final_tick=3]
    assert result == [0, 1, 2, 3]


# --- Invariants ---


def test_food_accounting_preserved():
    """Total food + delivered equals the initial total."""
    result = run_actor(
        """
        world0 = ants/new_world(7, 3, 5, 5)
        initial_food = ants/total_food(world0)
        world_f = run_actor_sim(world0, 6)
        final_food = ants/total_food(world_f)
        delivered = ants/world_delivered(world_f)
        carried = length(filter((a) -> ants/ant_carrying?(a), ants/world_ants(world_f)))
        initial_food == final_food + delivered + carried
        """
    )
    assert result is True


def test_delivered_food_monotonic():
    """Delivered food never decreases across ticks."""
    result = run_actor(
        """
        summaries = collect_actor_summaries(7, 3, 6)
        map(snd, summaries)
        """
    )
    # delivered_list should be monotonically non-decreasing
    for i in range(len(result) - 1):
        assert result[i] <= result[i + 1], f"delivered decreased at index {i}: {result[i]} > {result[i+1]}"


def test_ant_count_unchanged():
    """Number of ants stays the same after simulation."""
    result = run_actor(
        """
        world = ants/new_world(7, 4, 5, 5)
        w = run_actor_sim(world, 5)
        length(ants/world_ants(w))
        """
    )
    assert result == 4
