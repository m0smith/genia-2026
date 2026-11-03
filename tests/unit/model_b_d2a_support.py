"""Shared fixtures for the Model B D2a RED tests (#1250).

PYTHON REFERENCE HOST ONLY. TEST-ONLY private protocol bound by these tests
(design: docs/design/pre-r29-model-b-d2-linking-design.md sections 2-3, 5, 9.1).
The design names the D2a seams but not their signatures; this file supplies test adapters for the
smallest signatures the RED oracles use. Equivalent private layouts may adapt
the accessors below with independent review; they must not weaken any oracle.

Private seams under test (adapter layouts may change with independent review):
  genia.ordinary_completion.completion_for(module_value, value) -> projection | None
  genia.function_linking.FrozenOrdinaryBase.from_projection(projection)
      attributes: group, interface_key, name, module_id, clauses (tuple of
      GeniaFunction copies), span, projection
  genia.function_linking.plan_link(base, units) -> tuple of units in canonical
      order, or raises (pure; no lock, no user code, no Env access)
  genia.function_linking.link_view(base, units) -> GeniaLinkedOpenFunction
      (checks duplicate selection by declaring_module_id first, then plan_link,
      then builds; never publishes). `base` is a FrozenOrdinaryBase or an
      explicit GeniaOpenFunction.
  genia.callable.GeniaOpenContributionUnit(..., target=G)   (inert field)
  genia.callable.OpenFunctionCrossUnitDuplicateClauseError
  genia.callable.OpenFunctionShapeConflictError
  Env.publish_view(name, view)   Env.ordinary_contributions
  ModuleValue._ordinary_contributions (tuple, empty until D2b)

No skip/xfail/stub model. Contributor units are harvested from REAL modules that
`extend` a private explicit interface `iface.f`; their records keep the
contributor's own closure/span/module id exactly as the evaluator creates them.
"""

from __future__ import annotations

import importlib
from contextlib import contextmanager

import genia
from genia.callable import GeniaOpenContributionUnit

IFACE_KEY = ("iface", "f")
IFACE_SOURCE = "open f(0, 0, 0, 0, 0, 0, 0) = 0\n"


def linking():
    """Import the private D2a module; ImportError is the intended RED until it exists."""
    return importlib.import_module("genia.function_linking")


def completion_for(module_value, value):
    """Call the D2a typed lookup; AttributeError is the intended RED until it exists."""
    return importlib.import_module("genia.ordinary_completion").completion_for(module_value, value)


def world(tmp_path, files=None, root=None):
    """Write fixtures and return (root env, entry label); the loader is the real one."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    for name, source in {"iface": IFACE_SOURCE, **(files or {})}.items():
        (tmp_path / (name + ".genia")).write_text(source, encoding="utf-8")
    return root if root is not None else genia.make_global_env([]), str(tmp_path / "entry.genia")


def base_world(tmp_path, base_source, extra=None, root=None):
    """Load module `base` and return (root, entry, module, group G exported as `f`)."""
    root, entry = world(tmp_path, {"base": base_source, **(extra or {})}, root=root)
    module = root.load_module("base", entry)
    return root, entry, module, module.get_export("f")


def frozen(module, group):
    """Materialize a FrozenOrdinaryBase from the module's D1 projection of `group`."""
    projection = completion_for(module, group)
    assert projection is not None, "D2a: completion_for must find the D1 projection"
    return linking().FrozenOrdinaryBase.from_projection(projection)


def contributor(root, entry, tmp_path, name, group, clauses):
    """Load a real module `name` that `extend`s iface.f; return an ordinary-target unit.

    Line 1 is `import iface`, so clause i is on line i + 2. `clauses` are source
    texts such as 'f(x, ..r) = 1'. The unit carries the contributor's own records.
    """
    source = "import iface\n" + "".join("extend iface." + clause + "\n" for clause in clauses)
    (tmp_path / (name + ".genia")).write_text(source, encoding="utf-8")
    module = root.load_module(name, entry)
    harvested = module.contributions[IFACE_KEY]
    return GeniaOpenContributionUnit(group.owner, name, list(harvested.clauses), target=group)


def explicit_unit(module, key):
    """Return a loaded module's genuine explicit-open contribution unit for `key`."""
    return module.contributions[key]


@contextmanager
def no_runtime_calls():
    """Reject actual lookup/renderer code entry, even through an imported alias."""
    import sys
    from genia.environment import Env
    from genia.builtins import format_display, format_debug

    forbidden = {Env.get.__code__, format_display.__code__, format_debug.__code__}
    previous = sys.getprofile()

    def profile(frame, event, argument):
        """Raise when a forbidden lookup/renderer code object is entered."""
        if event == 'call' and frame.f_code in forbidden:
            raise AssertionError('pure builder entered lookup or renderer')

    try:
        sys.setprofile(profile)
        yield
    finally:
        sys.setprofile(previous)
