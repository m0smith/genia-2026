"""Python-only F2/P2 metacircular reflection regressions (issue #1067, debt #1238; R10/R34).

Maintainer ruling (PR #1244 comment 6197128489, Option A): raw `doc`/`meta`/`help` obtained by
identifier lookup during metacircular `eval` bind to the metacircular evaluation frame (contract §16.2),
for names supplied through `define`/`extend`. An already scope-bound reflective callable transferred
into the frame keeps its captured scope. `empty_env()` stays rooted at R; entry-only names stay
invisible without explicit transfer; there is no module-to-entry fallback in metacircular evaluation.

Python-host test: it drives `GeniaMetaEnv.lookup`. The earlier integer `doc` probe was non-discriminating
(`missing-doc` under every rule); these controls use a documented function with observable metadata.
"""

import pytest

from genia import make_program_env, run_source

PRELUDE = '''
@doc "documented in entry"
documented(x) = x
docstringed(x) = "docstring in entry" x
undocumented_entry_only = 7
'''


def _entry():
    """Build a program environment holding `PRELUDE`'s documented, docstring and entry-only names."""
    entry = make_program_env([])
    run_source(PRELUDE, entry)
    return entry


def _show(entry, source):
    """Run Genia `source` in `entry` and return the debug `repr` of its result for text assertions."""
    return repr(run_source(source, entry))


def _is_missing(text, kind):
    """True when `text` is the `missing-<kind>` absence (kind is "doc" or "meta")."""
    return f"missing-{kind}" in text


@pytest.mark.parametrize("frame", ["define(empty_env(), quote(f), docstringed)",
                                   "define(extend(empty_env(), nil, []), quote(f), docstringed)"])
def test_raw_doc_in_meta_frame_finds_explicitly_defined_documented_callable(frame):
    """`define` carries the function value (and its docstring), not the entry's `@doc` binding metadata."""
    entry = _entry()
    text = _show(entry, f'eval(quote(doc("f")), {frame})')
    assert text == repr("docstring in entry")


@pytest.mark.parametrize("frame", ["define(empty_env(), quote(f), docstringed)",
                                   "define(extend(empty_env(), nil, []), quote(f), docstringed)"])
def test_raw_meta_in_meta_frame_distinguishes_a_defined_name_from_a_missing_one(frame):
    """A defined name has a (here empty) metadata map; only an unbound name is `missing-meta`."""
    entry = _entry()
    assert _show(entry, f'eval(quote(meta("f")), {frame})') == "<map 0>"
    assert "missing-meta" in _show(entry, f'eval(quote(meta("never_defined")), {frame})')


def test_raw_reflection_still_finds_runtime_names_and_missing_stays_missing():
    entry = _entry()
    assert not _is_missing(_show(entry, 'eval(quote(doc("map")), empty_env())'), "doc")
    assert _is_missing(_show(entry, 'eval(quote(doc("never_defined_anywhere")), empty_env())'), "doc")


def test_help_in_meta_frame_resolves_the_explicitly_defined_name():
    out = []
    entry = make_program_env([], output_handler=out.append)
    run_source(PRELUDE, entry)
    run_source('eval(quote(help("f")), define(empty_env(), quote(f), docstringed))', entry)
    text = "".join(out)
    assert "docstring in entry" in text and "No public helper or runtime name found" not in text


def test_already_bound_reflective_callable_keeps_its_captured_scope():
    """`d` was evaluated in the entry: it reaches entry names and does NOT see the meta-frame-only name."""
    entry = _entry()
    run_source("bound = doc", entry)
    env = "define(define(empty_env(), quote(f), documented), quote(d), bound)"
    assert "documented in entry" in _show(entry, f'eval(quote(d("documented")), {env})')
    assert _is_missing(_show(entry, f'eval(quote(d("f")), {env})'), "doc")


def test_meta_frame_binding_does_not_leak_into_the_entry_or_runtime():
    entry = _entry()
    _show(entry, 'eval(quote(doc("f")), define(empty_env(), quote(f), documented))')
    assert _is_missing(_show(entry, 'doc("f")'), "doc")
    assert "f" not in entry.values and "f" not in entry.runtime_scope().values


def test_entry_only_names_are_invisible_to_meta_frame_reflection_without_transfer():
    entry = _entry()
    assert _is_missing(_show(entry, 'eval(quote(doc("documented")), empty_env())'), "doc")
    assert _is_missing(_show(entry, 'eval(quote(meta("undocumented_entry_only")), empty_env())'), "meta")


def test_module_metacircular_reflection_gets_no_entry_fallback(tmp_path):
    (tmp_path / "meta_mod.genia").write_text(
        'probe() = eval(quote(doc("documented")), empty_env())\n',
        encoding="utf-8",
    )
    entry = _entry()
    run_source("import meta_mod", entry, filename=str(tmp_path / "entry.genia"))
    assert _is_missing(_show(entry, "meta_mod.probe()"), "doc")
    assert not entry.runtime_scope().fallback_events


def test_rebinding_a_reflective_name_in_the_meta_frame_wins_over_the_runtime_builtin():
    """Regression guard (passes before and after the fix): a user value named `doc` is never rebound."""
    entry = _entry()
    text = _show(entry, 'eval(quote(doc("x")), define(empty_env(), quote(doc), (n) -> "mine"))')
    assert "mine" in text
