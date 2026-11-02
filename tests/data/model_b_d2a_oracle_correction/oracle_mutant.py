"""Ephemeral mutation probe; production sources are never edited."""
import os

def pytest_configure(config):
    """Install the mutated none-awareness predicate selected by ORACLE_MUTATION."""
    from genia import callable as c
    original = c._callable_explicitly_handles_none
    mutation = os.environ['ORACLE_MUTATION']

    def mutated(fn, arity, callee_node=None):
        """Mutate only linked-view awareness: all-false, all-true, or arity-2 leak."""
        if isinstance(fn, c.GeniaLinkedOpenFunction):
            if mutation == 'false':
                return False
            if mutation == 'true':
                return True
            if mutation == 'leak':
                return original(fn, 2, callee_node)
        return original(fn, arity, callee_node)
    c._callable_explicitly_handles_none = mutated
