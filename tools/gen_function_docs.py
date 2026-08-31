#!/usr/bin/env python3
"""Generate the alphabetical Genia function reference from source @doc/@meta.

Single source of truth: the runtime public surface (autoloaded prelude functions)
plus their @doc / @category / @since / @deprecated metadata. Do not hand-edit the
generated files -- edit @doc/@meta in the prelude and re-run this generator.

Outputs:
  docs/reference/index.md                 alphabetical index (+ by-category view)
  docs/reference/functions/<slug>.md      one page per function
  mkdocs.yml                              regenerates the managed function-nav block
  .tmp/wiki/*.md                          flat GitHub Wiki mirror (for tools/publish_wiki.sh)

Usage:
  python tools/gen_function_docs.py            # write everything
  python tools/gen_function_docs.py --check    # fail if regenerating would change tracked files
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
REF_DIR = REPO / "docs" / "reference"
FUNC_DIR = REF_DIR / "functions"
MKDOCS = REPO / "mkdocs.yml"
WIKI_DIR = REPO / ".tmp" / "wiki"

NAV_BEGIN = "  # >>> BEGIN generated function reference (tools/gen_function_docs.py) >>>"
NAV_END = "  # <<< END generated function reference <<<"

sys.path.insert(0, str(SRC))
from genia.builtins import make_global_env  # noqa: E402
from genia.docstrings import render_markdown_docstring  # noqa: E402
from genia.callable import GeniaFunction, GeniaFunctionGroup  # noqa: E402
from genia.host_builtin_docs import public_host_builtin_docs  # noqa: E402


def slug(name: str) -> str:
    s = name.replace("?", "-p").replace("!", "-bang")
    s = re.sub(r"[^A-Za-z0-9_.-]", "-", s)
    return s


def mstr(md, key):
    try:
        v = md.get(key)
    except Exception:
        return None
    return v if isinstance(v, str) else None


def mlist(md, key):
    try:
        v = md.get(key)
    except Exception:
        return None
    # GeniaList / python list of strings
    try:
        items = list(v)
    except Exception:
        return None
    out = [x for x in items if isinstance(x, str)]
    return out or None


def signatures(group) -> list[str]:
    sigs = []
    if not isinstance(group, GeniaFunctionGroup):
        return sigs
    for arity in group.sorted_arities():
        fn = group.get(arity)
        if not isinstance(fn, GeniaFunction):
            continue
        parts = list(fn.params)
        if fn.rest_param is not None:
            parts.append(".." + fn.rest_param)
        sigs.append(f"{group.name}({', '.join(parts)})")
    if not sigs and isinstance(group, GeniaFunctionGroup):
        sigs.append(group.name)
    return sigs


def arities_label(group) -> str:
    if not isinstance(group, GeniaFunctionGroup):
        return ""
    labels = []
    for arity in group.sorted_arities():
        fn = group.get(arity)
        suffix = "+" if (isinstance(fn, GeniaFunction) and fn.rest_param is not None) else ""
        labels.append(f"{arity}{suffix}")
    return ", ".join(labels)


def collect():
    env = make_global_env([])
    root = env.root()
    # name -> module path (first arity's path), restricted to prelude autoloads
    name_path = collections.OrderedDict()
    for (name, _arity), path in root.autoloads.items():
        if path.startswith("std/prelude/") and name not in name_path:
            name_path[name] = path
    records = []
    for name, path in name_path.items():
        try:
            value = env.get(name)  # triggers autoload
        except Exception:
            value = None
        md = env.get_metadata(name)
        category = mstr(md, "category") or path.split("/")[-1].replace(".genia", "")
        doc_raw = mstr(md, "doc")
        if doc_raw is None and isinstance(value, GeniaFunctionGroup):
            doc_raw = value.docstring
        summary = ""
        if doc_raw:
            for line in doc_raw.strip().splitlines():
                if line.strip():
                    summary = line.strip()
                    break
        records.append({
            "name": name,
            "slug": slug(name),
            "category": category,
            "module": path,
            "since": mstr(md, "since"),
            "deprecated": mstr(md, "deprecated"),
            "stability": mstr(md, "stability"),
            "see_also": mlist(md, "see_also"),
            "signatures": signatures(value),
            "arities": arities_label(value),
            "doc_raw": doc_raw or "",
            "summary": summary,
            "source_kind": "prelude",
        })
    prelude_names = {record["name"] for record in records}
    for entry in public_host_builtin_docs():
        if entry.name in prelude_names:
            raise ValueError(f"duplicate public function documentation name: {entry.name}")
        summary = next(
            (line.strip() for line in entry.doc.strip().splitlines() if line.strip()),
            "",
        )
        records.append({
            "name": entry.name,
            "slug": slug(entry.name),
            "category": entry.category,
            "module": "Python reference host",
            "since": entry.since,
            "deprecated": entry.deprecated,
            "stability": entry.stability,
            "see_also": list(entry.see_also) or None,
            "signatures": list(entry.signatures),
            "arities": "",
            "doc_raw": entry.doc,
            "summary": summary,
            "source_kind": "python-host",
        })
    records.sort(key=lambda r: r["name"].lower())
    return records


def esc_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_index(records) -> str:
    n = len(records)
    cats = sorted({r["category"] for r in records})
    out = []
    out.append("# Function Reference")
    out.append("")
    out.append(f"Alphabetical index of the **{n}** out-of-the-box Genia functions available "
               "from the autoloaded prelude and Python reference host. Every entry is generated "
               "from canonical documentation metadata -- see "
               "[the @doc Style Guide](../style/doc-style.md). Do not edit these pages by hand.")
    out.append("")
    out.append("## All functions (A-Z)")
    out.append("")
    out.append("| Function | Category | Signature | Summary |")
    out.append("| --- | --- | --- | --- |")
    for r in records:
        link = f"[`{r['name']}`](functions/{r['slug']}.md)"
        sig = esc_cell(r["signatures"][0]) if r["signatures"] else r["name"]
        dep = " _(deprecated)_" if r["deprecated"] else ""
        out.append(f"| {link} | {r['category']} | `{sig}` | {esc_cell(r['summary'])}{dep} |")
    out.append("")
    out.append("## By category")
    out.append("")
    by = collections.defaultdict(list)
    for r in records:
        by[r["category"]].append(r)
    for cat in cats:
        out.append(f"### {cat}")
        out.append("")
        for r in sorted(by[cat], key=lambda r: r["name"].lower()):
            out.append(f"- [`{r['name']}`](functions/{r['slug']}.md) - {esc_cell(r['summary'])}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def render_page(r, name_to_slug) -> str:
    out = []
    out.append(f"# `{r['name']}`")
    out.append("")
    badges = [f"**Category:** `{r['category']}`"]
    if r["arities"]:
        badges.append(f"**Arity:** {r['arities']}")
    if r["since"]:
        badges.append(f"**Since:** {r['since']}")
    if r["stability"]:
        badges.append(f"**Stability:** {r['stability']}")
    out.append(" &nbsp;|&nbsp; ".join(badges))
    out.append("")
    if r["deprecated"]:
        out.append("!!! warning \"Deprecated\"")
        out.append(f"    {r['deprecated']}")
        out.append("")
    if r["signatures"]:
        out.append("```genia")
        out.extend(r["signatures"])
        out.append("```")
        out.append("")
    doc = render_markdown_docstring(r["doc_raw"]) if r["doc_raw"] else "_No documentation available._"
    out.append(doc)
    out.append("")
    if r["see_also"]:
        links = []
        for other in r["see_also"]:
            s = name_to_slug.get(other)
            links.append(f"[`{other}`]({s}.md)" if s else f"`{other}`")
        out.append("## See also")
        out.append("")
        out.append(", ".join(links))
        out.append("")
    out.append("---")
    out.append("")
    source = r["module"]
    out.append(f"_Source: `{source}` &middot; category `{r['category']}`. "
               "Generated from canonical metadata by `tools/gen_function_docs.py`._")
    out.append("")
    out.append("[<- Back to the Function Reference](../index.md)")
    return "\n".join(out).rstrip() + "\n"


def render_nav_block(records) -> str:
    by = collections.defaultdict(list)
    for r in records:
        by[r["category"]].append(r)
    lines = [NAV_BEGIN]
    lines.append("  - Function Reference:")
    lines.append("      - Overview: reference/index.md")
    for cat in sorted(by):
        lines.append(f"      - {cat}:")
        for r in sorted(by[cat], key=lambda r: r["name"].lower()):
            lines.append(f"          - \"{r['name']}\": reference/functions/{r['slug']}.md")
    lines.append(NAV_END)
    return "\n".join(lines) + "\n"


def update_mkdocs_nav(records) -> str:
    text = MKDOCS.read_text(encoding="utf-8")
    block = render_nav_block(records)
    if NAV_BEGIN in text and NAV_END in text:
        pre = text[: text.index(NAV_BEGIN)]
        post = text[text.index(NAV_END) + len(NAV_END):]
        post = post.split("\n", 1)[1] if "\n" in post else ""
        return pre + block + post
    # append at end of file (nav is the last top-level key in this project's mkdocs.yml)
    if not text.endswith("\n"):
        text += "\n"
    return text + block


def render_wiki(records) -> dict:
    files = {}
    # Home / index
    home = ["# Genia Function Reference", "",
            f"Alphabetical index of the {len(records)} out-of-the-box prelude functions. "
            "Generated from source `@doc`/`@meta`; do not edit by hand.", "",
            "| Function | Category | Summary |", "| --- | --- | --- |"]
    for r in records:
        home.append(f"| [{r['name']}]({r['slug']}) | {r['category']} | {esc_cell(r['summary'])} |")
    files["Function-Reference.md"] = "\n".join(home) + "\n"
    sidebar = ["### Function Reference", "", "[All functions](Function-Reference)", ""]
    files["_Sidebar.md"] = "\n".join(sidebar) + "\n"
    name_to_slug = {r["name"]: r["slug"] for r in records}
    for r in records:
        page = render_page(r, name_to_slug)
        # wiki links are bare page names, not relative .md paths
        page = page.replace("(../index.md)", "(Function-Reference)")
        page = re.sub(r"\]\(([A-Za-z0-9_.-]+)\.md\)", r"](\1)", page)
        files[f"{r['slug']}.md"] = page
    return files


def _prune(directory: Path, keep: set) -> None:
    """Remove *.md files no longer generated. Best-effort: a read-only or
    delete-locked filesystem (e.g. a mounted dev folder) is tolerated; CI runs
    on a normal filesystem where stale pages are fully cleaned."""
    for existing in directory.glob("*.md"):
        if existing.name not in keep:
            try:
                existing.unlink()
            except OSError as exc:
                print(f"  war: could not remove stale {existing.name}: {exc}", file=sys.stderr)


def write_all(records):
    name_to_slug = {r["name"]: r["slug"] for r in records}
    FUNC_DIR.mkdir(parents=True, exist_ok=True)
    (REF_DIR / "index.md").write_text(render_index(records), encoding="utf-8")
    want = set()
    for r in records:
        fname = f"{r['slug']}.md"
        want.add(fname)
        (FUNC_DIR / fname).write_text(render_page(r, name_to_slug), encoding="utf-8")
    _prune(FUNC_DIR, want)
    MKDOCS.write_text(update_mkdocs_nav(records), encoding="utf-8")
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    wiki = render_wiki(records)
    for fname, content in wiki.items():
        (WIKI_DIR / fname).write_text(content, encoding="utf-8")
    _prune(WIKI_DIR, set(wiki))


def check(records) -> int:
    """Return 1 if regenerating would change any tracked output."""
    name_to_slug = {r["name"]: r["slug"] for r in records}
    changed = []
    def cmp(path: Path, new: str):
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        if old != new:
            changed.append(str(path.relative_to(REPO)))
    cmp(REF_DIR / "index.md", render_index(records))
    want = {f"{r['slug']}.md" for r in records}
    have = {p.name for p in FUNC_DIR.glob("*.md")} if FUNC_DIR.exists() else set()
    for extra in have - want:
        changed.append(f"docs/reference/functions/{extra} (stale)")
    for r in records:
        cmp(FUNC_DIR / f"{r['slug']}.md", render_page(r, name_to_slug))
    cmp(MKDOCS, update_mkdocs_nav(records))
    if changed:
        print("Function reference is STALE. Re-run: python tools/gen_function_docs.py")
        for c in sorted(changed):
            print(f"  - {c}")
        return 1
    print("Function reference is up to date.")
    return 0


def main(argv):
    records = collect()
    if "--check" in argv:
        return check(records)
    write_all(records)
    print(f"Generated reference for {len(records)} functions ->")
    print(f"  {REF_DIR/'index.md'}")
    print(f"  {FUNC_DIR}/<name>.md  ({len(records)} pages)")
    print(f"  {MKDOCS} (nav block)")
    print(f"  {WIKI_DIR}/  (wiki mirror)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
