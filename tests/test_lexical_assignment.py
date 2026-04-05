import pytest


def test_block_local_rebinding(run):
    src = """
    {
      x = 1
      x = 2
      x
    }
    """
    assert run(src) == 2


def test_function_parameter_rebinding(run):
    src = """
    f(x) = {
      x = x + 1
      x
    }

    f(10)
    """
    assert run(src) == 11


def test_closure_rebinding_preserves_local_state(run):
    src = """
    make_counter() = {
      n = 0
      () -> {
        n = n + 1
        n
      }
    }

    c = make_counter()
    [c(), c(), c()]
    """
    assert run(src) == [1, 2, 3]


def test_independent_closures_keep_independent_bindings(run):
    src = """
    make_counter() = {
      n = 0
      () -> {
        n = n + 1
        n
      }
    }

    a = make_counter()
    b = make_counter()
    [a(), a(), b(), a(), b()]
    """
    assert run(src) == [1, 2, 1, 3, 2]


def test_nested_scope_assignment_updates_nearest_existing_binding(run):
    src = """
    {
      x = 1
      y = {
        x = 2
        x
      }
      [x, y]
    }
    """
    assert run(src) == [2, 2]


def test_nested_scope_assignment_defines_local_when_name_missing(run):
    src = """
    {
      y = {
        x = 2
        x
      }
      y
    }
    """
    assert run(src) == 2


def test_invalid_assignment_target_is_rejected(run):
    src = """
    {
      (1 + 2) = 3
      0
    }
    """
    with pytest.raises(SyntaxError, match="Assignment target must be a simple name"):
        run(src)
