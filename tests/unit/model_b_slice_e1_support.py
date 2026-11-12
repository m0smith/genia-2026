"""Python-host RED-B fixtures using real groups, records and module loading (#1250).

No lifecycle is simulated. Closed groups come only from the GREEN-A factory;
owner identities are copied from real ordinary declarations before replacement.
"""

from dataclasses import replace

import genia
from genia import callable as callables
from genia import ir
from tests.unit.model_b_d2a_support import IFACE_SOURCE, contributor


def record(scope, name="f", params=("x",)):
    """Create an existing identifier-header record in the supplied real Env."""
    return callables.GeniaFunction(name, list(params), None, None, ir.IrVar(params[-1]), scope)


def close(ordinary):
    """Construct a real closed group and explicitly preserve the declaration owner."""
    assert ordinary.owner is not None
    group = callables.GeniaClosedFunction._from_records(ordinary.name, ordinary.records)
    group.owner = ordinary.owner
    assert group.owner == (group.records[0].closure.module_identity(), group.name)
    return group


def bound_group(*, closed, source="f(x) = x"):
    """Return a real declaration scope/group, optionally replacing its value only."""
    scope = genia.make_global_env([])
    genia.run_source(source, scope)
    ordinary = scope.get("f")
    assert ordinary.owner == (scope.module_identity(), "f")
    group = close(ordinary) if closed else ordinary
    if closed:
        scope.assign("f", group)
    assert scope.get("f") is group
    return scope, group


def module_world(path, *, closed, export="direct"):
    """Load genuine owned exports via a host fixture callback, without closed syntax.

    The callback replaces a real ordinary declaration before module completion.
    The ordinary control uses exactly the same path but returns the original group.
    Alias mode replaces the defining slot; re-export mode uses the real module loader.
    """
    path.mkdir(parents=True, exist_ok=True)
    root = genia.make_global_env([])

    def as_fixture_group(ordinary):
        """Return the genuine ordinary control or a factory-built closed value."""
        assert ordinary.owner is not None
        return close(ordinary) if closed else ordinary

    root.set_host("as_fixture_group", as_fixture_group, visibility="runtime-public")
    source = "f(x) = x\nf = as_fixture_group(f)\na = f\n"
    if export == "alias":
        source += "f = 7\n"
    (path / "base.genia").write_text(source, encoding="utf-8")
    entry = str(path / "entry.genia")
    base = root.load_module("base", entry)
    module = base
    if export == "reexport":
        (path / "relay.genia").write_text("import base\na = base.a\n", encoding="utf-8")
        module = root.load_module("relay", entry)
    group = module.get_export("f" if export == "direct" else "a")
    scope = group.records[0].closure.unit_scope()
    assert group.owner == (scope.module_identity(), "f")
    assert group.records[0].closure.unit_scope() is scope
    assert isinstance(group, callables.GeniaClosedFunction) is closed
    return root, entry, module, group


def prepare_use(root, entry, path, group):
    """Supply a genuine D2a-compiled contribution unit for the use-target test.

    Reuse the existing fixture's explicit-interface compiler to obtain real clause
    records, then seed the module's private ordinary-contribution data with its
    returned exact-target unit, using a new frozen ModuleValue via replace().
    No closed-target extension is needed during setup,
    so a future correct exclusion cannot prevent reaching the use operation.
    """
    (path / "iface.genia").write_text(IFACE_SOURCE, encoding="utf-8")
    unit = contributor(root, entry, path, "ext", group, ["f(x, y) = y"])
    extension = root.load_module("ext", entry)
    assert unit.target is group and unit.target_interface_key == group.owner
    root.assign("ext", replace(extension, _ordinary_contributions=(unit,)))
