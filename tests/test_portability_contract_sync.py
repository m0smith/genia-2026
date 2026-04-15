import json
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent


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
        "docs/book/15-reference-host-and-portability.md",
        "spec/README.md",
        "hosts/README.md",
        "hosts/python/README.md",
    ]
    for relpath in required_docs:
        text = read_text(relpath)
        assert "Python is the only implemented host" in text

    assert "hosts/python/` is a scaffolded future-layout directory" in read_text(
        "docs/host-interop/HOST_INTEROP.md"
    )
    assert "the live Python implementation remains in `src/genia/`" in read_text(
        "docs/host-interop/HOST_CAPABILITY_MATRIX.md"
    )
    assert "hosts/python/` is a future-layout documentation scaffold" in read_text("spec/README.md")


def test_browser_runtime_adapter_manifest_stays_scaffolded_only():
    manifest = json.loads((REPO / "spec" / "manifest.json").read_text(encoding="utf-8"))
    adapter = manifest["browser_runtime_adapter"]

    assert adapter["status"] == "scaffolded"
    assert adapter["implemented_hosts"] == []
    assert adapter["planned_hosts"] == [
        "python-backend-service",
        "javascript-browser-native",
        "rust-wasm-browser-native",
    ]

    for relpath in [
        "GENIA_STATE.md",
        "docs/host-interop/HOST_CAPABILITY_MATRIX.md",
        "docs/book/15-reference-host-and-portability.md",
        "spec/README.md",
        "tools/spec_runner/README.md",
    ]:
        text = read_text(relpath)
        assert "no implemented browser runtime adapter hosts" in text
