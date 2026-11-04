"""Install the public #1285 candidate from exact offline inputs, without images.

Default paths are /opt/genia/{source,build-venv,editable-wheel,venv} and
/opt/runner-tools/installer. --host-test --root explicitly relocates those paths
for unprivileged host evidence, never official-target acceptance. All these
intermediates are retained in the proposed image and included in A/B inventories;
deployment distribution inventory covers venv only. Caller pins this source and
its complete input manifest before invocation with python -I -S -B.
"""

import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

# -I -S excludes this directory; add only the explicitly invoked source location.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import offline_install as frontend


def verify_inputs(manifest, expected_hash):
    """Recheck the caller-pinned complete input tree before any output writes.

    The caller must verify this manifest's expected hash and frontend entrypoint
    before executing Python; self-verification cannot establish its own trust.
    This second check detects missing/extra/replaced inputs in an exclusively
    owned tree. The manifest itself is its only unhashed tree member.
    """
    frontend.no_symlink_components(manifest)
    data = manifest.read_bytes()
    frontend.require(frontend.sha(data) == expected_hash, "input manifest hash mismatch")
    root = manifest.parent
    expected = {}
    for line in data.decode("utf-8").splitlines():
        digest, name = line.split("  ", 1)
        frontend.safe_name(name)
        frontend.require(
            len(digest) == 64
            and all(c in "0123456789abcdef" for c in digest)
            and name not in expected,
            "malformed input manifest",
        )
        expected[name] = digest
    frontend.require(list(expected) == sorted(expected), "unsorted input manifest")
    actual = {}
    for path in root.rglob("*"):
        frontend.require(not path.is_symlink(), "input symlink forbidden")
        if path.is_file() and path != manifest:
            actual[path.relative_to(root).as_posix()] = frontend.sha(path.read_bytes())
    frontend.require(actual == expected, "input tree missing/extra/hash mismatch")


def rows_at(pins, inputs):
    """Select exact local identities and reject missing/extra artifact filenames."""
    runtime = [row for row in pins["runtime_wheels"] if row["target_selected"]]
    backend = pins["backend_wheels"]
    union = {row["filename"]: row for row in [*runtime, *backend]}
    frontend.require(
        len(runtime) == 43 and len(backend) == 7 and len(union) == 47, "unexpected pinned wheel set"
    )
    wanted = set(union) | {pins["installer"]["filename"], pins["uv"]["filename"]}
    frontend.require({p.name for p in inputs.iterdir()} == wanted, "unexpected/missing wheel input")

    def attach(row):
        """Bind an exact artifact identity to its single local manifest filename."""
        return {**row, "path": str(inputs / row["filename"])}

    return [attach(r) for r in runtime], [attach(r) for r in backend], attach(pins["installer"])


def validated_source(archive, lock, pins):
    """Validate immutable approved tar/lock bytes before source destination writes."""
    data, lock_data = archive.read_bytes(), lock.read_bytes()
    frontend.require(
        frontend.sha(data) == pins["source"]["export_archive_sha256"], "source archive hash"
    )
    frontend.require(
        frontend.sha(lock_data) == pins["source"]["lock_sha256"]
        and len(lock_data) == pins["source"]["lock_bytes"],
        "original lock hash/size",
    )
    result, seen = [], set()
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for item in tar:
            name = frontend.safe_name(item.name.rstrip("/"))
            frontend.require(
                name not in seen and (item.isdir() or item.isfile()), "unsafe source tar"
            )
            seen.add(name)
            if item.isfile():
                frontend.require(
                    item.mode in (0o644, 0o755, 0o664, 0o775), "unexpected tracked source mode"
                )
                result.append((name, tar.extractfile(item).read(), item.mode & ~0o022))
    project = next(content for name, content, mode in result if name == "pyproject.toml")
    frontend.require(frontend.sha(project) == pins["source"]["pyproject_sha256"], "pyproject hash")
    frontend.require("uv.lock" not in seen, "source unexpectedly tracks uv.lock")
    result.append(("uv.lock", lock_data, 0o644))
    return result


def command(argv, cwd, env, receipts):
    """Run a bounded local command and preserve failures in the caller's receipt.

    Build/import/check outputs are small by contract; this is not the future
    runner's 16MiB stream supervisor. No benchmark command is accepted here.
    """
    result = subprocess.run(
        [str(x) for x in argv], cwd=cwd, env=env, capture_output=True, timeout=90
    )
    row = {
        "argv": [str(x) for x in argv],
        "exit_code": result.returncode,
        "stdout": result.stdout.decode("utf-8", "replace"),
        "stderr": result.stderr.decode("utf-8", "replace"),
    }
    receipts.append(row)
    frontend.require(result.returncode == 0, "command failed: " + json.dumps(row))
    return result.stdout


def build(args):
    """Prevalidate originals, bootstrap/build in isolation, then install complete44.

    No destination writes precede original-input validation. Editable wheel
    generation necessarily writes the builder/source/intermediate first; the
    complete runtime+editable plan validates before ANY deployment venv write.
    All source bytes/modes are checked unchanged after hook/build/install.
    """
    frontend.umask_022()
    frontend.require(
        sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
        "invoke orchestration with python -I -S -B",
    )
    frontend.require(sys.version_info[:2] == (3, 12), "CPython3.12 required")
    if not args.host_test:
        frontend.require(
            args.root == Path("/opt")
            and args.python == Path("/usr/local/bin/python3.12")
            and sys.version_info[:3] == (3, 12, 15),
            "official fixed target required",
        )
    else:
        frontend.require(
            args.root.is_relative_to(Path("/workspace/work")),
            "host-test root must be a dedicated /workspace/work child",
        )
    pins = json.loads(args.pins.read_text())
    runtime, backend, tool = rows_at(pins, args.inputs)
    root = args.root
    source, builder, editable, deployment = [
        root / "genia" / name for name in ("source", "build-venv", "editable-wheel", "venv")
    ]
    tools = root / "runner-tools/installer"
    for path in (source, builder, editable, deployment, tools):
        frontend.no_symlink_components(path)
        frontend.require(not path.exists(), "output exists: " + str(path))
    frontend.require(
        frontend.sha(args.uv.read_bytes()) == pins["uv"]["binary_sha256"], "uv binary pin"
    )
    # Stdlib-validates all49 original inputs, not just backend ones. Runtime
    # mapped collisions/modes are checked even before the builder/scaffold starts.
    runtime_plan = frontend.prepare(runtime, deployment)
    builder_plan = frontend.prepare(backend, builder)
    frontend.validate_wheel(tool)
    frontend.validate_wheel({**pins["uv"], "path": str(args.inputs / pins["uv"]["filename"])})
    source_files = validated_source(args.source_archive, args.lock, pins)
    expected = json.loads(Path(__file__).with_name("expected-modes.json").read_text())
    frontend.require(
        runtime_plan.files == expected["runtime_files"]
        and builder_plan.files == expected["builder_files"],
        "expected mode manifest mismatch",
    )
    # No output parent is created until the full original preflight passes.
    (root / "genia").mkdir(parents=True, exist_ok=True)
    (root / "runner-tools").mkdir(parents=True, exist_ok=True)
    frontend.bootstrap(tool, tools)
    env = frontend.clean_environment()
    env["UV_CACHE_DIR"] = str(args.cache)
    frontend.install(builder_plan, tools, args.uv, args.python)
    frontend.umask_022()
    source.mkdir()
    for name, data, mode in source_files:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
        # Source permissions are the approved Git modes, not wheel normalization.
        if mode == 0o755:
            target.chmod(mode)
    before_source = frontend.inventory(source)
    frontend.umask_022()
    editable.mkdir()
    receipts = []
    code = (
        "import json,sys,hatchling.build; "
        "requirements=hatchling.build.get_requires_for_build_editable({}); "
        'assert requirements == ["editables~=0.3"],requirements; '
        'print(json.dumps({"requires":requirements,"wheel":hatchling.build.build_editable(sys.argv[1])}))'
    )
    output = command(
        [builder / "bin/python", "-I", "-B", "-c", code, editable], source, env, receipts
    )
    build_result = json.loads(output)
    frontend.require(
        build_result["requires"] == ["editables~=0.3"], "editable requirements changed"
    )
    wheel_path = editable / frontend.safe_name(build_result["wheel"])
    frontend.require(
        wheel_path.parent == editable and len(list(editable.iterdir())) == 1,
        "unexpected builder output",
    )
    generated = {
        "name": "genia",
        "version": pins["source"]["root_version"],
        "filename": wheel_path.name,
        "path": str(wheel_path),
        "sha256": frontend.sha(wheel_path.read_bytes()),
        "bytes": wheel_path.stat().st_size,
    }
    generated_valid = frontend.validate_wheel(generated)
    frontend.require(
        not any(name.startswith("genia/") for name, _ in generated_valid.members),
        "editable copied Genia into site-packages",
    )
    with frontend.zipfile.ZipFile(io.BytesIO(generated_valid.data)) as archive:
        pths = [archive.read(n) for n in archive.namelist() if n.endswith(".pth")]
    frontend.require(pths == [str(source / "src").encode()], "unexpected editable source routing")
    final_plan = frontend.prepare([*runtime, generated], deployment, editable_source=source)
    frontend.require(
        final_plan.files
        == {**expected["runtime_files"], **expected["editable_and_generated_files"]},
        "editable/final expected mode manifest mismatch",
    )
    receipts.extend(frontend.install(final_plan, tools, args.uv, args.python))
    for prefix in (builder, deployment):
        command(
            [
                args.uv,
                "--no-config",
                "pip",
                "check",
                "--python",
                prefix / "bin/python",
                "--offline",
            ],
            source,
            env,
            receipts,
        )
    frontend.require(frontend.inventory(source) == before_source, "source/lock changed")
    for path in (source, builder, editable, deployment, tools):
        frontend.require(not list(path.rglob("*.pyc")), "unexpected bytecode")
    return {
        "host_test": args.host_test,
        "host_python": sys.version,
        "runtime_prefix": str(deployment),
        "source_archive_sha256": pins["source"]["export_archive_sha256"],
        "editable_wheel": generated,
        "commands": receipts,
        "wheel_order": [w.row["filename"] for w in final_plan.wheels],
        "installed_RECORD_rows": frontend.verify_records(deployment),
        "retained_roots": [str(p) for p in (source, builder, editable, deployment, tools)],
        "official_target_or_OCI_acceptance": False,
    }


def main():
    """Parse explicit offline inputs and write a receipt outside the output roots."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "pins",
        "inputs",
        "source-archive",
        "lock",
        "uv",
        "receipt",
        "cache",
        "input-manifest",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--input-manifest-sha256", required=True)
    parser.add_argument("--root", type=Path, default=Path("/opt"))
    parser.add_argument("--python", type=Path, default=Path("/usr/local/bin/python3.12"))
    parser.add_argument("--host-test", action="store_true")
    args = parser.parse_args()
    frontend.no_symlink_components(args.receipt)
    frontend.require(not args.receipt.exists(), "receipt already exists; retain prior evidence")
    try:
        verify_inputs(args.input_manifest, args.input_manifest_sha256)
        for field, relative in [
            ("pins", "pins.json"),
            ("inputs", "wheels"),
            ("source_archive", "source.tar"),
            ("lock", "uv.lock"),
            ("uv", "uv"),
        ]:
            frontend.require(
                getattr(args, field) == args.input_manifest.parent / relative,
                "input selector outside verified manifest tree",
            )
        frontend.require(
            not args.receipt.is_relative_to(args.input_manifest.parent)
            and not args.cache.is_relative_to(args.input_manifest.parent),
            "receipts/caches must be outside immutable inputs",
        )
        result = build(args)
    except Exception as error:
        args.receipt.write_text(
            json.dumps(
                {"status": "FAIL", "type": type(error).__name__, "message": str(error)}, indent=2
            )
            + "\n"
        )
        raise
    args.receipt.write_text(json.dumps({"status": "PASS", **result}, indent=2) + "\n")


if __name__ == "__main__":
    main()
