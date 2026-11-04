"""Bounded public host A/B proof for #1285; no images, benchmark or acceptance.

Fresh input inodes/mtimes and independent writes reuse identical absolute paths
sequentially. Retain complete inventories/receipts before removing only the owned
active tree. Rootless mode protection is a labeled host read-only diagnostic,
not a read-only mount, UID10001 test, independent worker or OCI proof.
"""

import argparse
import importlib.machinery
import json
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import offline_install as frontend

WRAPPERS = {
    "coverage": ["--version"],
    "coverage-3.12": ["--version"],
    "coverage3": ["--version"],
    "genia": ["-c", "1 + 1"],
    "ghp-import": ["--help"],
    "idna": ["--help"],
    "markdown_py": ["--help"],
    "mkdocs": ["--version"],
    "mkdocs-get-deps": ["--help"],
    "normalizer": ["--version"],
    "py.test": ["--version"],
    "pybabel": ["--version"],
    "pygmentize": ["-V"],
    "pytest": ["--version"],
    "watchmedo": ["--help"],
}
EXTENSIONS = [
    "charset_normalizer.cd",
    "charset_normalizer.md",
    "coverage.tracer",
    "markupsafe._speedups",
    "yaml._yaml",
    "tree_sitter._binding",
    "tree_sitter_bash._binding",
    "tree_sitter_cpp._binding",
    "tree_sitter_rust._binding",
    "tree_sitter_typescript._binding",
]


def run(argv, cwd, env, commands):
    """Capture finite smoke output and exit status; preserve every failed attempt."""
    guard = Path(__file__).resolve().parents[1] / "frontend_tests/offline_guard.py"
    actual_argv = [sys.executable, "-I", "-S", "-B", str(guard), *[str(x) for x in argv]]
    result = subprocess.run(actual_argv, cwd=cwd, env=env, capture_output=True, timeout=90)
    row = {
        "argv": [str(x) for x in argv],
        "restrictive_offline_guard": True,
        "exit_code": result.returncode,
        "stdout": result.stdout.decode("utf-8", "replace"),
        "stderr": result.stderr.decode("utf-8", "replace"),
    }
    commands.append(row)
    frontend.require(result.returncode == 0, json.dumps(row))
    return result.stdout


def remove_owned_tree(path):
    """Dispose only a marked harness tree after preserving its complete inventory."""
    frontend.require(
        path.name == "active" and (path.parent / "verification-owned").is_file(),
        "not owned verification tree",
    )
    if path.exists():
        for entry in path.rglob("*"):
            if entry.is_dir() and not entry.is_symlink():
                entry.chmod(0o755)
        shutil.rmtree(path)


def probe_readonly(prefix, source, uv, env, commands):
    """Test no-sync/frozen and optional env hardening under declared mode protection.

    Temporarily remove write bits from owned venv files/directories; never change
    bytes. Record attempted-write denial, execute commands, assert exact protected
    inventory equality, and restore original modes explicitly in finally. No
    chmod operation is part of installation or used to manufacture A/B equality.
    """
    original = frontend.inventory(prefix)
    try:
        for name, item in original.items():
            if item["kind"] != "symlink":
                (prefix / name).chmod(item["mode"] & ~0o222)
        protected = frontend.inventory(prefix)
        denied = False
        try:
            (prefix / "write-control").write_bytes(b"forbidden")
        except PermissionError:
            denied = True
        frontend.require(denied, "host readonly diagnostic did not deny creation")
        python_code = "import sys;print(sys.prefix)"
        selected = env | {
            "UV_PROJECT_ENVIRONMENT": str(prefix),
            "UV_PYTHON": str(prefix / "bin/python"),
        }
        output = run(
            [
                uv,
                "--no-config",
                "run",
                "--frozen",
                "--offline",
                "--no-sync",
                "python",
                "-B",
                "-c",
                python_code,
            ],
            source,
            selected,
            commands,
        )
        frontend.require(output.decode().strip() == str(prefix), "uv selected wrong environment")
        hardened = selected | {"UV_NO_SYNC": "1", "UV_FROZEN": "1"}
        # Diagnostic omission only: verifies pinned env switches. Normal project
        # commands still always require the explicit flags above.
        output = run(
            [uv, "--no-config", "run", "--offline", "python", "-B", "-c", python_code],
            source,
            hardened,
            commands,
        )
        frontend.require(
            output.decode().strip() == str(prefix), "uv env hardening selected wrong environment"
        )
        frontend.require(frontend.inventory(prefix) == protected, "uv wrote to protected venv")
        return {
            "mode_protection_only": True,
            "write_creation_denied": True,
            "explicit_no_sync_frozen_pass": True,
            "UV_NO_SYNC_UV_FROZEN_diagnostic_pass": True,
            "changed_venv_paths": [],
            "read_only_mount_or_UID10001_claim": False,
        }
    finally:
        # Restore directory traversal/writability first for reliable owned cleanup.
        for name, item in original.items():
            if item["kind"] != "symlink":
                (prefix / name).chmod(item["mode"])
        frontend.require(
            frontend.inventory(prefix) == original, "mode diagnostic restoration mismatch"
        )


def smoke(active, uv, env, expected, commands):
    """Check exact44, all wrappers, native imports, editable behavior and RECORDs."""
    prefix, source = active / "genia/venv", active / "genia/source"
    python = prefix / "bin/python"
    before_source = frontend.inventory(source)
    code = (
        "import json,importlib.metadata,site,genia;print(json.dumps({"
        '"distributions":sorted(d.metadata["Name"].lower().replace("_","-")+"=="+d.version '
        'for d in importlib.metadata.distributions()),"source":genia.__file__,"user_site":site.ENABLE_USER_SITE}))'
    )
    result = json.loads(run([python, "-I", "-B", "-c", code], active, env, commands))
    frontend.require(result["distributions"] == sorted(expected), "final44 inventory mismatch")
    frontend.require(
        Path(result["source"]).is_relative_to(source / "src") and not result["user_site"],
        "editable import routing",
    )
    for wrapper, args in WRAPPERS.items():
        run([prefix / "bin" / wrapper, *args], active, env, commands)
    run([prefix / "bin/ruff", "--version"], active, env, commands)
    code = (
        "import importlib,json;modules=" + repr(EXTENSIONS) + ";"
        "print(json.dumps({n:importlib.import_module(n).__file__ for n in modules}))"
    )
    native = json.loads(run([python, "-I", "-B", "-c", code], active, env, commands))
    for path in native.values():
        frontend.require(
            Path(path).is_relative_to(prefix / frontend.SITE)
            and any(path.endswith(ext) for ext in importlib.machinery.EXTENSION_SUFFIXES),
            "compiled fallback/escape",
        )
    run(
        [
            python,
            "-I",
            "-B",
            "-c",
            "from watchdog.observers.inotify_c import Inotify;print(Inotify.__module__)",
        ],
        active,
        env,
        commands,
    )
    for operation in (
        ["list", "--format", "json"],
        ["freeze"],
        ["show", "genia"],
        ["tree"],
        ["check"],
    ):
        run(
            [uv, "--no-config", "pip", *operation, "--python", python, "--offline"],
            source,
            env,
            commands,
        )
    module = source / "src/genia/frontend_live_probe.py"
    init = source / "src/genia/__init__.py"
    initial = init.read_bytes()
    try:
        init.write_bytes(initial + b"\nfrontend_live_probe_value = 1285\n")
        module.write_text("value = 1285\n")
        output = run(
            [
                python,
                "-I",
                "-B",
                "-c",
                "import genia,genia.frontend_live_probe as p;print(genia.frontend_live_probe_value,p.value)",
            ],
            active,
            env,
            commands,
        )
        frontend.require(output == b"1285 1285\n", "source not live")
    finally:
        init.write_bytes(initial)
        if module.exists():
            module.unlink()
    readonly = probe_readonly(prefix, source, uv, env, commands)
    frontend.require(
        frontend.inventory(source) == before_source, "source/lock/environment writes detected"
    )
    frontend.require(not list(active.rglob("*.pyc")), "unwanted bytecode")
    direct = prefix / frontend.SITE / "genia-0.1.14.dist-info/direct_url.json"
    frontend.require(not direct.read_bytes().endswith(b"\n"), "direct_url trailing newline")
    return {
        "final_distributions": result["distributions"],
        "wrappers": list(WRAPPERS),
        "native_modules": native,
        "watchdog_platform_python_backend": True,
        "live_edit_and_new_module": True,
        "readonly_uv": readonly,
        "source_unchanged": True,
        "RECORD_rows": frontend.verify_records(prefix),
        "direct_url_bytes": direct.read_text(),
    }


def verify(args):
    """Create two independent host installations at fixed paths and compare all roots."""
    frontend.umask_022()
    work = args.work
    frontend.require(not work.exists(), "verification requires a fresh work directory")
    work.mkdir(parents=True)
    (work / "verification-owned").touch()
    active, stage = work / "active", work / "stage"
    expected = json.loads(args.pins.with_name("expected-inventory.json").read_text())["phases"][
        "final_both_candidates"
    ]
    manifest, results = (
        {},
        {
            "scope": "HOST ONLY, no target3.12.15/UID10001/OCI proof",
            "host": sys.version,
            "uid": os.getuid(),
            "cases": {},
            "commands": [],
        },
    )
    input_manifest = args.pins.with_name("input-sha256.txt")
    input_bytes = input_manifest.read_bytes()
    input_hash = frontend.sha(input_bytes)
    try:
        for label, timestamp in [("A", 1000000000), ("B", 1600000000)]:
            stage.mkdir()
            stats = {}
            for line in input_bytes.decode().splitlines():
                expected_hash, name = line.split("  ", 1)
                if name.startswith("wheels/"):
                    origin = args.inputs / Path(name).name
                elif name in ("source.tar", "uv.lock", "uv"):
                    origin = {
                        "source.tar": args.source_archive,
                        "uv.lock": args.lock,
                        "uv": args.uv,
                    }[name]
                else:
                    origin = args.pins.parent / name
                frontend.require(
                    frontend.sha(origin.read_bytes()) == expected_hash, "caller input hash mismatch"
                )
                target = stage / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(origin.read_bytes())
                if name == "uv":
                    target.chmod(0o755)
                os.utime(target, (timestamp, timestamp))
                stats[name] = {
                    "ctime_ns": target.stat().st_ctime_ns,
                    "mtime_ns": target.stat().st_mtime_ns,
                }
            (stage / "input-sha256.txt").write_bytes(input_bytes)
            os.utime(stage / "input-sha256.txt", (timestamp, timestamp))
            env = frontend.clean_environment() | {"UV_CACHE_DIR": str(work / f"cache-{label}")}
            receipt = work / f"build-{label}.json"
            run(
                [
                    args.python,
                    "-I",
                    "-S",
                    "-B",
                    stage / "frontend/build_frontend.py",
                    "--pins",
                    stage / "pins.json",
                    "--inputs",
                    stage / "wheels",
                    "--source-archive",
                    stage / "source.tar",
                    "--lock",
                    stage / "uv.lock",
                    "--uv",
                    stage / "uv",
                    "--receipt",
                    receipt,
                    "--cache",
                    work / f"cache-{label}",
                    "--input-manifest",
                    stage / "input-sha256.txt",
                    "--input-manifest-sha256",
                    input_hash,
                    "--host-test",
                    "--root",
                    active,
                    "--python",
                    args.python,
                ],
                work,
                env,
                results["commands"],
            )
            result = json.loads(receipt.read_text())
            checks = smoke(active, stage / "uv", env, expected, results["commands"])
            manifest[label] = {
                **{"installed/" + n: v for n, v in frontend.inventory(active).items()},
                **{"runner-input/" + n: v for n, v in frontend.inventory(stage).items()},
            }
            results["cases"][label] = {
                "inputs": stats,
                "build": result,
                "smokes": checks,
                "paths": len(manifest[label]),
                "socket_connect_denial_inherited": True,
                "packet_trace_or_general_sandbox_claim": False,
            }
            (work / "results.json").write_text(json.dumps(results, indent=2) + "\n")
            if label == "A":
                remove_owned_tree(active)
                shutil.rmtree(stage)
        for name, a in results["cases"]["A"]["inputs"].items():
            b = results["cases"]["B"]["inputs"][name]
            frontend.require(
                a["ctime_ns"] != b["ctime_ns"] and a["mtime_ns"] != b["mtime_ns"],
                "timestamp variation not established",
            )
        changes = [
            name
            for name in sorted(set(manifest["A"]) | set(manifest["B"]))
            if manifest["A"].get(name) != manifest["B"].get(name)
        ]
        results["comparison"] = {
            "changed_paths": changes,
            "strict_equal": not changes,
            "includes": "all files/directories/symlinks, bytes/hash/size/mode/uid/gid/link targets in source/builder/editable/deployment/tools and complete retained runner-input tree; timestamps excluded",
            "independent_workers_or_OCI": False,
        }
        frontend.require(not changes, "A/B output differs")
        raw = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
        compressed = lzma.compress(raw)
        (work / "manifests.json.xz").write_bytes(compressed)
        results["manifest_artifact"] = {
            "file": "manifests.json.xz",
            "sha256": frontend.sha(compressed),
            "decoded_sha256": frontend.sha(raw),
            "bytes": len(compressed),
        }
        return results
    finally:
        (work / "results.json").write_text(json.dumps(results, indent=2) + "\n")


def main():
    """Run host-only verification; failures remain in the new work directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("work", "pins", "inputs", "source-archive", "lock", "uv", "python"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = verify(args)
    print(json.dumps(result["comparison"], indent=2))


if __name__ == "__main__":
    main()
