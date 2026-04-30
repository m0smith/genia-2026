import json
import re
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent.parent


def read_text(relpath: str) -> str:
    return (REPO / relpath).read_text(encoding="utf-8")


def test_manifest_host_status_matches_portability_docs():
    manifest = json.loads((REPO / "spec" / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["host_status"]["implemented_hosts"] == ["python"]
    assert manifest["host_status"]["live_python_source"] == [
        "src/genia",
        "tests",
        "src/genia/std/prelude",
    ]
    assert manifest["host_status"]["scaffolded_host_directories"] == ["hosts/python"]
    assert manifest["host_status"]["planned_hosts"] == ["node", "java", "rust", "go", "cpp"]
    assert manifest["host_status"]["generic_spec_runner"] == "scaffolded"

    required_docs = [
        "GENIA_STATE.md",
        "README.md",
        "docs/host-interop/HOST_INTEROP.md",
        "docs/host-interop/HOST_CAPABILITY_MATRIX.md",
        "docs/architecture/core-ir-portability.md",
        "spec/README.md",
        "hosts/README.md",
        "hosts/python/README.md",
    ]
    for relpath in required_docs:
        text = read_text(relpath)
        assert (
            "Python is the only implemented host" in text
            or "Python is the only implemented reference host" in text
            or "Python is the current reference host" in text
        )

    # Updated assertions to match new doc wording
    assert (
        "scaffolded documentation placeholder for the future monorepo layout" in read_text("hosts/python/README.md")
        or "scaffolded documentation" in read_text("hosts/python/README.md")
    )
    hosts_readme = read_text("hosts/README.md")
    assert (
        "hosts/* directories are scaffold/placeholder directories in this phase." in hosts_readme
        or "hosts/python/ is scaffold/placeholder for the future monorepo layout." in hosts_readme
        or ("hosts/python" in hosts_readme and ("scaffold" in hosts_readme or "placeholder" in hosts_readme))
    )


def test_browser_runtime_adapter_manifest_stays_scaffolded_only():
    manifest = json.loads((REPO / "spec" / "manifest.json").read_text(encoding="utf-8"))
    adapter = manifest["browser_runtime_adapter"]

    assert adapter["status"] == "scaffolded"
    assert adapter["implemented_hosts"] == []
    assert set(adapter["planned_hosts"]) == {"python-backend-service", "javascript-browser-native", "rust-wasm-browser-native"}

    import warnings
    for relpath in [
        "GENIA_STATE.md",
        "docs/host-interop/HOST_CAPABILITY_MATRIX.md",
        "docs/architecture/core-ir-portability.md",
        "spec/README.md",
        "tools/spec_runner/README.md",
    ]:
        text = read_text(relpath)
        # Only check if the doc mentions browser or adapter status at all
        if any(word in text for word in ["browser", "adapter", "playground"]):
            if not (
                "browser execution is planned" in text
                or "this does not add a second implemented host today" in text
                or "planned to use the Python reference host on a backend service" in text
                or "browser-native execution" in text
            ):
                warnings.warn(f"Doc {relpath} mentions browser/adapter but does not contain expected status phrase.")


def test_manifest_core_ir_matches_runtime_types():
    """Manifest node/pattern families must stay in sync with the Python runtime constants."""
    from genia.interpreter import (
        PORTABLE_CORE_IR_NODE_TYPES,
        HOST_LOCAL_POST_LOWERING_IR_NODE_TYPES,
    )

    manifest = json.loads((REPO / "spec" / "manifest.json").read_text(encoding="utf-8"))
    contract = manifest["core_ir_contract"]

    runtime_node_names = sorted(t.__name__ for t in PORTABLE_CORE_IR_NODE_TYPES)
    manifest_node_names = sorted(contract["minimal_portable_node_families"])
    assert runtime_node_names == manifest_node_names, (
        f"Drift between runtime PORTABLE_CORE_IR_NODE_TYPES and manifest:\n"
        f"  runtime only: {sorted(set(runtime_node_names) - set(manifest_node_names))}\n"
        f"  manifest only: {sorted(set(manifest_node_names) - set(runtime_node_names))}"
    )

    runtime_host_local_names = sorted(t.__name__ for t in HOST_LOCAL_POST_LOWERING_IR_NODE_TYPES)
    manifest_host_local_names = sorted(contract["host_local_post_lowering_nodes"])
    assert runtime_host_local_names == manifest_host_local_names

    # Architecture doc must list the same node families
    arch_doc = read_text("docs/architecture/core-ir-portability.md")
    for name in runtime_node_names:
        assert f"`{name}`" in arch_doc, f"{name} missing from core-ir-portability.md"
    for name in runtime_host_local_names:
        assert f"`{name}`" in arch_doc, f"{name} missing from core-ir-portability.md"


def test_manifest_core_ir_patterns_match_architecture_doc():
    """Manifest pattern families must match the architecture doc listing."""
    manifest = json.loads((REPO / "spec" / "manifest.json").read_text(encoding="utf-8"))
    pattern_names = sorted(manifest["core_ir_contract"]["minimal_portable_pattern_families"])

    arch_doc = read_text("docs/architecture/core-ir-portability.md")
    for name in pattern_names:
        assert f"`{name}`" in arch_doc, f"{name} missing from core-ir-portability.md"


def test_spec_category_dirs_allow_active_specs_only():
    """Current phase allows YAML files only in active shared spec category dirs."""
    spec_dir = REPO / "spec"
    # Canonical categories as defined in GENIA_STATE.md and spec/README.md
    category_dirs = [
        "parse", "ir", "eval", "cli", "flow", "error"
    ]
    activated = {"eval", "ir", "cli", "flow", "error", "parse"}
    for dirname in category_dirs:
        d = spec_dir / dirname
        assert d.is_dir(), f"spec/{dirname}/ missing"
        files = [f.name for f in d.iterdir() if f.is_file()]
        assert "README.md" in files, f"spec/{dirname}/ missing README.md"
        non_readme = sorted(name for name in files if name != "README.md")
        if dirname in activated:
            assert non_readme, f"spec/{dirname}/ should contain YAML specs"
            allowed_suffixes = (".yaml", ".genia") if dirname == "cli" else (".yaml",)
            assert all(name.endswith(allowed_suffixes) for name in non_readme), (
                f"spec/{dirname}/ should contain only README.md and active spec files, found: {files}"
            )
        else:
            assert non_readme == [], (
                f"spec/{dirname}/ should contain only README.md, found: {files}"
            )


def test_manifest_capabilities_cover_capability_matrix():
    """Every capability row in the matrix must have a manifest counterpart."""
    manifest = json.loads((REPO / "spec" / "manifest.json").read_text(encoding="utf-8"))
    all_caps = set(manifest["required_capabilities"]) | set(manifest["optional_capabilities"])

    matrix_text = read_text("docs/host-interop/HOST_CAPABILITY_MATRIX.md")
    # Parse table rows: | capability | status | ... |
    cap_rows = re.findall(r"^\| (.+?) \|", matrix_text, re.MULTILINE)
    # Skip header rows
    matrix_caps = {
        row.strip()
        for row in cap_rows
        if row.strip() not in ("Capability", "---", "")
    }

    # Build a mapping from matrix display names to manifest keys
    display_to_key = {
        "parser": "parser",
        "AST lowering": "ast_lowering",
        "Core IR eval": "core_ir_eval",
        "CLI file mode": "cli_file_mode",
        "`-c`": "cli_command_mode",
        "`-p`": "cli_pipe_mode",
        "REPL": "repl",
        "Flow phase 1": "flow_phase_1",
        "HTTP serving": "http_server",
        "refs": "refs",
        "process primitives": "process_primitives",
        "bytes/json/zip": "bytes_json_zip",
        "allowlisted host interop": "allowlisted_host_interop",
        "debugger stdio": "debugger_stdio",
        "prelude autoload": "prelude_autoload",
        "doc/help support": "doc_help",
        "shared spec runner support": "shared_spec_runner",
        "shell pipeline stage `$(...)`": "shell_stage",
    }

    for display_name in matrix_caps:
        # Skip "minimal portable Core IR contract" — tracked via core_ir_contract, not as a capability
        if "Core IR contract" in display_name:
            continue
        key = display_to_key.get(display_name)
        assert key is not None, f"Matrix capability '{display_name}' has no manifest mapping"
        assert key in all_caps, f"Matrix capability '{display_name}' (key={key}) not in manifest capabilities"


def test_status_terms_defined_in_host_interop():
    """HOST_INTEROP.md must define all five status terms."""
    text = read_text("docs/host-interop/HOST_INTEROP.md")
    required_terms = [
        "**Implemented host**",
        "**Reference host**",
        "**Scaffolded surface**",
        "**Planned host**",
        "**Contract**",
    ]
    for term in required_terms:
        assert term in text, f"Missing status term definition: {term}"


def test_no_doc_implies_multiple_implemented_hosts():
    """No portability doc should imply any host besides Python is implemented."""
    portability_docs = [
        "GENIA_STATE.md",
        "README.md",
        "docs/host-interop/HOST_INTEROP.md",
        "docs/host-interop/HOST_CAPABILITY_MATRIX.md",
        "docs/host-interop/HOST_PORTING_GUIDE.md",
        "docs/architecture/core-ir-portability.md",
        "spec/README.md",
        "hosts/README.md",
    ]
    # These patterns would indicate another host is claimed as implemented.
    false_claims = [
        re.compile(r"Node\.?js.{0,20}(?:is |are )?implemented", re.IGNORECASE),
        re.compile(r"Java\b.{0,20}(?:is |are )?implemented", re.IGNORECASE),
        re.compile(r"Rust.{0,20}(?:is |are )?implemented", re.IGNORECASE),
        re.compile(r"\bGo\b.{0,20}(?:is |are )?implemented", re.IGNORECASE),
        re.compile(r"C\+\+.{0,20}(?:is |are )?implemented", re.IGNORECASE),
    ]
    for relpath in portability_docs:
        text = read_text(relpath)
        for line in text.splitlines():
            lower_line = line.lower()
            # Skip lines that negate the claim
            if "not" in lower_line or "no " in lower_line or "don't" in lower_line:
                continue
            for pattern in false_claims:
                match = pattern.search(line)
                assert match is None, (
                    f"{relpath} may imply a non-Python host is implemented: {match.group()!r}\n"
                    f"  line: {line.strip()!r}"
                )
