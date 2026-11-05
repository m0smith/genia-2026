"""Offline wheel frontend for #1285; host-verified candidate, not runner acceptance.

prepare() reads and validates the entire input set into immutable byte snapshots
without destination writes. install() consumes that plan once in an exclusively
owned, absent prefix. No resolver, download, third-party builder or transaction
rollback is provided. Native member order and installer-generated metadata remain
untouched. CLI orchestration and the pinned input manifest are separate sources.
"""

import base64
import configparser
import csv
from dataclasses import dataclass
from email.parser import BytesParser
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import sysconfig
import zipfile

INSTALLER_SHA256 = "05d1933f0a5ba7d8d6296bb6d5018e7c94fa473ceb10cf198a92ccea19c27b53"
UV_SHA256 = "8a70db72685b7138121bfcda71fa1a00cb709ed9f1fdc4ecf1dd871e8e167e52"
SITE = "lib/python3.12/site-packages"
SCAFFOLD_RESERVED = {
    "bin/python",
    "bin/python3",
    "bin/python3.12",
    "bin/activate",
    "bin/activate.csh",
    "bin/activate.fish",
    "bin/activate.nu",
    "bin/activate.ps1",
    "bin/activate.bat",
    "bin/deactivate.bat",
    "bin/activate_this.py",
    "bin/activate.xsh",
    "bin/pydoc.bat",
    "lib64",
    "pyvenv.cfg",
    ".gitignore",
    "CACHEDIR.TAG",
}
MAX_ARCHIVE = 128 * 1024 * 1024
MAX_BATCH = 512 * 1024 * 1024


def require(condition, message):
    """Raise ValueError for a violated invariant, including under python -O."""
    if not condition:
        raise ValueError(message)


def sha(data):
    """Return the exact-byte lowercase SHA256 used by the approved manifests."""
    return hashlib.sha256(data).hexdigest()


def umask_022():
    """Reject an inherited umask other than 022 without changing the caller policy.

    This single-threaded frontend briefly reads/restores the process umask. CLI
    callers must establish 022; silently correcting a caller override would hide
    the negative control. Call again immediately before every write phase.
    """
    mask = os.umask(0o022)
    os.umask(mask)
    require(mask == 0o022, "umask must be 022")


def safe_name(name, directory=False):
    """Accept canonical relative POSIX members only; return their slashless path."""
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name, "unsafe path")
    require(not any(ord(c) < 32 or ord(c) == 127 for c in name), "control in path")
    value = name[:-1] if directory else name
    require(
        not value.startswith("/") and all(p not in ("", ".", "..") for p in value.split("/")),
        "noncanonical path",
    )
    return value


def no_symlink_components(path):
    """Reject symlink ancestors and lexical aliases before reading or creating paths."""
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "absolute canonical path required")
    for parent in [path, *path.parents]:
        require(not parent.is_symlink(), "symlink path component")
    require(path.resolve() == path, "path resolution changed")


def canonical(name):
    """Canonicalize a distribution name without importing packaging before trust."""
    return re.sub(r"[-_.]+", "-", name).lower()


def headers(data, required):
    """Read metadata with exactly one of each required header, rejecting ambiguity."""
    result = BytesParser().parsebytes(data)
    for key in required:
        require(len(result.get_all(key, [])) == 1, "missing/duplicate " + key)
    return result


@dataclass(frozen=True)
class Wheel:
    """A hash/RECORD-validated archive snapshot and its validated native member list."""

    row: dict
    data: bytes
    dist_info: str
    data_dir: str
    members: tuple
    root_scheme: str
    scripts: tuple


@dataclass(frozen=True)
class Plan:
    """Complete batch plan; caller must exclusively own the absent prefix until done."""

    prefix: Path
    scheme: dict
    wheels: tuple
    files: dict
    metadata: dict


def validate_wheel(row):
    """Return a stdlib-validated snapshot; malformed archive formats raise ValueError."""
    try:
        return _validate_wheel(row)
    except (
        zipfile.BadZipFile,
        csv.Error,
        configparser.Error,
        KeyError,
        NotImplementedError,
    ) as error:
        raise ValueError("malformed wheel: " + str(error)) from error


def _validate_wheel(row):
    """Stdlib-first archive validation, with bidirectional RECORD content coverage.

    Input row must pin name/version/filename/bytes/SHA256 and an absolute path.
    Genuine 0755 zero-size directory members may be omitted from RECORD; they are
    non-payload and produce no output. No archive-controlled code is imported.
    Reads are bounded to 128 MiB per archive and 512 MiB expanded payload.
    """
    path = Path(row["path"])
    no_symlink_components(path)
    require(path.name == row["filename"], "filename does not match pin")
    require(path.stat().st_size == row["bytes"] <= MAX_ARCHIVE, "archive size mismatch/limit")
    data = path.read_bytes()
    require(len(data) == row["bytes"] and sha(data) == row["sha256"], "archive hash mismatch")
    parts = row["filename"][:-4].split("-")
    require(row["filename"].endswith(".whl") and len(parts) in (5, 6), "invalid wheel filename")
    distribution, version = parts[:2]
    require(
        bool(re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9_.]*[A-Za-z0-9])?", distribution))
        and bool(re.fullmatch(r"[A-Za-z0-9_!.+]+", version)),
        "malformed wheel identity",
    )
    require(
        canonical(distribution) == canonical(row["name"]) and version == row["version"],
        "filename identity mismatch",
    )
    if len(parts) == 6:
        require(bool(re.fullmatch(r"\d[\w]*", parts[2])), "invalid wheel build tag")
    filename_tags = {
        f"{py}-{abi}-{platform}"
        for py in parts[-3].split(".")
        for abi in parts[-2].split(".")
        for platform in parts[-1].split(".")
    }
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        items = archive.infolist()
        require(
            len(items) <= 100000 and sum(i.file_size for i in items) <= MAX_BATCH,
            "expanded archive limit",
        )
        seen, payload, dirs = set(), {}, set()
        for item in items:
            require(
                item.orig_filename == item.filename and not (item.flag_bits & 1),
                "ambiguous/encrypted ZIP entry",
            )
            directory = item.filename.endswith("/")
            name = safe_name(item.filename, directory)
            require(name not in seen, "duplicate member or directory/file alias")
            seen.add(name)
            mode = item.external_attr >> 16
            kind = stat.S_IFMT(mode)
            if directory:
                require(
                    kind == stat.S_IFDIR and stat.S_IMODE(mode) == 0o755 and item.file_size == 0,
                    "malformed ZIP directory",
                )
                require(archive.read(item) == b"", "nonempty ZIP directory")
                dirs.add(name)
            else:
                require(kind in (0, stat.S_IFREG) and not mode & 0o7000, "unsafe member type/mode")
                require(kind == stat.S_IFREG or not mode & 0o111, "untyped executable member")
                require(not name.endswith((".pyc", ".pyo")), "bytecode payload forbidden")
                payload[name] = archive.read(item)  # also checks CRC/local-header consistency
        for name in seen:
            require(
                not any(str(p) in payload for p in PurePosixPath(name).parents if str(p) != "."),
                "file is also a parent",
            )
        infos = {n.split("/")[0] for n in seen if n.split("/")[0].endswith(".dist-info")}
        require(len(infos) == 1, "exactly one dist-info required")
        dist_info = infos.pop()
        require(dist_info == f"{distribution}-{version}.dist-info", "dist-info identity mismatch")
        record_name = dist_info + "/RECORD"
        require(record_name in payload, "missing RECORD")
        records = {}
        for record in csv.reader(
            io.StringIO(payload[record_name].decode("utf-8"), newline=""), strict=True
        ):
            require(len(record) == 3, "malformed RECORD row")
            name, digest, size = record
            safe_name(name)
            require(name not in records, "duplicate RECORD row")
            records[name] = (digest, size)
        require(set(records) == set(payload), "RECORD/payload coverage mismatch")
        for name, content in payload.items():
            digest, size = records[name]
            if name == record_name:
                require((digest, size) == ("", ""), "RECORD self-row must be empty")
            else:
                expected = (
                    base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip("=")
                )
                require(
                    digest == "sha256=" + expected and size == str(len(content)),
                    "RECORD content mismatch",
                )
        metadata = headers(payload[dist_info + "/METADATA"], ["Name", "Version"])
        require(
            canonical(metadata["Name"]) == canonical(row["name"])
            and metadata["Version"] == version,
            "METADATA identity mismatch",
        )
        wheel = headers(payload[dist_info + "/WHEEL"], ["Wheel-Version", "Root-Is-Purelib"])
        require(
            wheel["Wheel-Version"] == "1.0" and wheel["Root-Is-Purelib"] in ("true", "false"),
            "unsupported WHEEL format",
        )
        tags = set(wheel.get_all("Tag", []))
        require(tags == filename_tags, "WHEEL/filename tag mismatch")
        require(any(compatible_tag(t) for t in tags), "incompatible target tag")
        data_dir = f"{distribution}-{version}.data"
        for name in payload:
            top = name.split("/")[0]
            require(not top.startswith(dist_info) or top == dist_info, "dist-info prefix alias")
            if top.endswith(".data") or top.startswith(data_dir):
                require(top == data_dir, "unexpected .data directory")
            if name.startswith(dist_info + "/"):
                require(
                    name.split("/")[-1]
                    not in {
                        "INSTALLER",
                        "REQUESTED",
                        "direct_url.json",
                        "uv_cache.json",
                        "uv_build.json",
                        "RECORD.jws",
                        "RECORD.p7s",
                    },
                    "unexpected generated metadata/signature",
                )
        scripts = entrypoints(payload.get(dist_info + "/entry_points.txt", b""))
        members = tuple(
            (
                i.filename,
                bool(stat.S_ISREG(i.external_attr >> 16) and (i.external_attr >> 16) & 0o111),
            )
            for i in items
            if not i.is_dir()
        )
    return Wheel(
        dict(row),
        data,
        dist_info,
        data_dir,
        members,
        "purelib" if wheel["Root-Is-Purelib"] == "true" else "platlib",
        scripts,
    )


def compatible_tag(tag):
    """Accept only the declared CPython3.12/Linux-amd64 wheel families, no resolver."""
    py, abi, platform = tag.split("-")
    python_ok = (py in ("py3", "py312") and abi == "none") or (
        py == "cp312" and abi in ("cp312", "none")
    )
    python_ok |= abi == "abi3" and bool(re.fullmatch(r"cp3(?:[2-9]|1[0-2])", py))
    platform_ok = platform == "any" or platform in {
        "manylinux1_x86_64",
        "manylinux2010_x86_64",
        "manylinux2014_x86_64",
    }
    match = re.fullmatch(r"manylinux_2_(\d+)_x86_64", platform)
    platform_ok |= bool(match and int(match[1]) <= 41)
    return python_ok and platform_ok


def entrypoints(data):
    """Validate generated-script names/targets without importing wheel modules."""
    parser = configparser.ConfigParser(interpolation=None, delimiters="=")
    parser.optionxform = str
    parser.read_string(data.decode("utf-8"))
    result = []
    for section in ("console_scripts", "gui_scripts"):
        if not parser.has_section(section):
            continue
        for name, value in parser.items(section):
            require(
                bool(re.fullmatch(r"[\w.-]+", name)) and name not in (".", ".."),
                "unsafe entrypoint name",
            )
            require(
                bool(re.fullmatch(r"[\w.]+\s*:\s*[\w.]+(?:\s*\[[\w., -]+\])?", value)),
                "unsupported entrypoint target",
            )
            target = value.split("[", 1)[0]
            require(
                all(
                    part.strip().isidentifier()
                    for side in target.split(":")
                    for part in side.strip().split(".")
                ),
                "malformed entrypoint identifier",
            )
            result.append(name)
    return tuple(result)


def prefix_scheme(prefix):
    """Resolve and assert explicit upstream posix_prefix paths for one fixed venv."""
    prefix = Path(prefix)
    variables = dict.fromkeys(
        ("base", "platbase", "installed_base", "installed_platbase"), str(prefix)
    )
    scheme = sysconfig.get_paths(scheme="posix_prefix", vars=variables)
    require(
        scheme["purelib"] == scheme["platlib"] == str(prefix / SITE), "unexpected purelib/platlib"
    )
    require(
        scheme["scripts"] == str(prefix / "bin") and scheme["data"] == str(prefix),
        "unexpected scripts/data",
    )
    scheme["headers"] = scheme["include"]
    for name in ("purelib", "platlib", "scripts", "data", "headers", "include", "platinclude"):
        require(Path(scheme[name]).is_relative_to(prefix), "scheme path escapes prefix")
    require(Path(scheme["headers"]).is_relative_to(prefix / "include"), "headers escape include")
    return scheme


def mapped_path(wheel, name, scheme, prefix):
    """Map one validated native member exactly as installer0.7.0 does, fail closed."""
    parts = name.split("/")
    target_scheme, relative = wheel.root_scheme, name
    if parts[0] == wheel.data_dir:
        require(
            len(parts) >= 3 and parts[1] in ("purelib", "platlib", "headers", "scripts", "data"),
            "invalid .data scheme",
        )
        target_scheme, relative = parts[1], "/".join(parts[2:])
    target = Path(scheme[target_scheme]) / relative
    require(target.is_relative_to(prefix), "destination escape")
    return target.relative_to(prefix).as_posix()


def prepare(rows, prefix, editable_source=None):
    """Validate the full set and all destination conflicts before any prefix writes.

    Requires umask022 and an absent prefix with no symlink parents. Returns an
    in-memory Plan sorted by phase (runtime, then editable Genia), name/version/
    filename/hash, preserving each pinned wheel's native member order. The whole
    set is validated first; the phase boundary permits runtime43 pip check before
    editable installation. Initial editable metadata applies only to Genia.
    """
    umask_022()
    prefix = Path(prefix)
    no_symlink_components(prefix)
    require(not prefix.exists(), "destination prefix already exists")
    scheme = prefix_scheme(prefix)
    wheels = tuple(
        sorted(
            (validate_wheel(row) for row in rows),
            key=lambda w: (
                bool(editable_source) and canonical(w.row["name"]) == "genia",
                canonical(w.row["name"]),
                w.row["version"],
                w.row["filename"],
                w.row["sha256"],
            ),
        )
    )
    require(
        len({canonical(w.row["name"]) for w in wheels}) == len(wheels), "duplicate distribution"
    )
    require(sum(len(w.data) for w in wheels) <= MAX_BATCH, "batch archive limit")
    files, metadata, directories = {}, {}, {"bin", "lib", "lib/python3.12", SITE}

    def reserve(path, mode):
        """Reject exact and file/parent aliases, including scaffold script names."""
        require(
            path not in files and path not in directories and path not in SCAFFOLD_RESERVED,
            "destination collision: " + path,
        )
        require(
            not any(
                str(parent) in files or str(parent) in SCAFFOLD_RESERVED
                for parent in PurePosixPath(path).parents
            ),
            "file/directory conflict",
        )
        directories.update(str(p) for p in PurePosixPath(path).parents if str(p) != ".")
        files[path] = {"kind": "file", "mode": mode}

    for wheel in wheels:
        extra = {"INSTALLER": b"installer\n"}
        if editable_source is not None and canonical(wheel.row["name"]) == "genia":
            source = Path(editable_source)
            no_symlink_components(source)
            extra["direct_url.json"] = json.dumps(
                {"dir_info": {"editable": True}, "url": source.as_uri()},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        metadata[wheel.row["filename"]] = extra
        for script in wheel.scripts:
            reserve("bin/" + script, 0o755)
        for name, executable in wheel.members:
            reserve(mapped_path(wheel, name, scheme, prefix), 0o755 if executable else 0o644)
        for name in extra:
            reserve(SITE + "/" + wheel.dist_info + "/" + name, 0o644)
    return Plan(prefix, scheme, wheels, files, metadata)


def inventory(root):
    """Inventory every file/directory/link (including root), without following links.

    Return relative path -> kind/mode/uid/gid plus content SHA256/size or symlink
    target. Timestamps are deliberately excluded; no generated bytes are excluded.
    """
    root = Path(root)
    result = {}
    for path in [root, *sorted(root.rglob("*"))]:
        info = path.lstat()
        row = {"mode": stat.S_IMODE(info.st_mode), "uid": info.st_uid, "gid": info.st_gid}
        if stat.S_ISLNK(info.st_mode):
            row.update(kind="symlink", target=os.readlink(path))
        elif stat.S_ISDIR(info.st_mode):
            row.update(kind="directory")
        elif stat.S_ISREG(info.st_mode):
            data = path.read_bytes()
            row.update(kind="file", bytes=len(data), sha256=sha(data))
        else:
            raise ValueError("unexpected filesystem object")
        result[path.relative_to(root).as_posix()] = row
    return result


def bootstrap(row, tools_root):
    """Validate the exact pinned installer with stdlib, then extract read-only tools.

    All payloads and collisions are checked before tools_root creation. Final
    files0444/directories0555 are a declared tool protection policy, not metadata
    normalization. No installer code runs during bootstrap validation/extraction.
    """
    umask_022()
    require(
        row["sha256"] == INSTALLER_SHA256
        and row["name"] == "installer"
        and row["version"] == "0.7.0",
        "unapproved installer artifact",
    )
    wheel = validate_wheel(row)
    tools_root = Path(tools_root)
    no_symlink_components(tools_root)
    require(not tools_root.exists(), "tools root exists")
    with zipfile.ZipFile(io.BytesIO(wheel.data)) as archive:
        expected = json.loads(Path(__file__).with_name("installer-files.json").read_text())
        actual = {
            name: {"sha256": sha(archive.read(name)), "bytes": len(archive.read(name))}
            for name, _ in wheel.members
        }
        require(actual == expected, "installer manifest mismatch before extraction")
        tools_root.mkdir()
        for name, _ in wheel.members:
            path = tools_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(archive.read(name))
            path.chmod(0o444)
    for path in sorted(tools_root.rglob("*"), reverse=True):
        if path.is_dir():
            path.chmod(0o555)
    tools_root.chmod(0o555)
    verify_tools(tools_root)


def verify_tools(tools_root):
    """Rehash the entire isolated read-only tools root against pinned source inputs."""
    no_symlink_components(Path(tools_root))
    expected = json.loads(Path(__file__).with_name("installer-files.json").read_text())
    actual = inventory(tools_root)
    files = {
        name: {"sha256": item["sha256"], "bytes": item["bytes"]}
        for name, item in actual.items()
        if item["kind"] == "file"
    }
    require(files == expected, "installer tools bytes differ from verified wheel manifest")
    directories = {"."} | {
        str(parent) for name in expected for parent in PurePosixPath(name).parents
    }
    require(
        {name for name, item in actual.items() if item["kind"] == "directory"} == directories,
        "unexpected/missing installer tool directories",
    )
    for item in actual.values():
        require(
            item["kind"] in ("file", "directory")
            and item["mode"] == (0o444 if item["kind"] == "file" else 0o555),
            "tools root not read-only or unexpected type",
        )


def install(plan, tools_root, uv, python):
    """Install one prevalidated complete plan into a freshly scaffolded venv.

    Revalidates trust and absent destinations before writing. Inputs are immutable
    snapshots; guarded native destination writing cannot escape the approved plan.
    Caller must prevent concurrent destination mutation; a write-phase failure
    leaves an invalid partial tree for disposal, not a committed transaction.
    """
    umask_022()
    no_symlink_components(plan.prefix)
    require(not plan.prefix.exists(), "destination appeared after planning")
    require(sha(Path(uv).read_bytes()) == UV_SHA256, "uv binary mismatch")
    require(sys.dont_write_bytecode, "invoke frontend with -B")
    verify_tools(tools_root)
    for name in list(sys.modules):
        if name == "installer" or name.startswith("installer."):
            del sys.modules[name]
    previous_path = sys.path[:]
    sys.path.insert(0, str(tools_root))
    try:
        import installer
        from installer.destinations import SchemeDictionaryDestination
        from installer.sources import WheelFile

        require(
            installer.__version__ == "0.7.0"
            and Path(installer.__file__).is_relative_to(tools_root),
            "unexpected installer import",
        )
        # Secondary validation by pinned installer occurs for EVERY wheel before
        # uv scaffold writes. Keep the exact native ZIP order and immutable bytes.
        sources = []
        for wheel in plan.wheels:
            archive = zipfile.ZipFile(io.BytesIO(wheel.data))
            archive.filename = wheel.row["filename"]
            source = WheelFile(archive)
            source.validate_record(validate_contents=True)
            sources.append((wheel, archive, source))
        allowed = dict(plan.files)

        class GuardedDestination(SchemeDictionaryDestination):
            """Reject writes outside the plan; retain native installer content/order."""

            def write_to_fs(self, scheme, path, stream, is_executable):
                """Check exact path/mode, parent containment and no prior file writes."""
                target = Path(self.scheme_dict[scheme]) / path
                require(target.is_relative_to(plan.prefix), "unexpected destination")
                relative = target.relative_to(plan.prefix).as_posix()
                expected = allowed.pop(relative, None)
                require(
                    expected is not None
                    and expected["mode"] == (0o755 if is_executable else 0o644),
                    "unplanned write/mode",
                )
                no_symlink_components(target)
                return super().write_to_fs(scheme, path, stream, is_executable)

        umask_022()
        env = clean_environment()
        subprocess.run(
            [
                str(uv),
                "--no-config",
                "--no-cache",
                "venv",
                "--offline",
                "--no-python-downloads",
                "--python",
                str(python),
                str(plan.prefix),
            ],
            env=env,
            check=True,
            timeout=60,
        )
        phase_checks = []
        for index, (wheel, archive, source) in enumerate(sources):
            if index and "direct_url.json" in plan.metadata[wheel.row["filename"]]:
                verify_records(plan.prefix)
                argv = [
                    str(uv),
                    "--no-config",
                    "--no-cache",
                    "pip",
                    "check",
                    "--python",
                    str(plan.prefix / "bin/python"),
                    "--offline",
                ]
                checked = subprocess.run(argv, env=env, capture_output=True, timeout=60)
                phase_checks.append(
                    {
                        "phase": "after runtime wheels, before editable",
                        "argv": argv,
                        "exit_code": checked.returncode,
                        "stdout": checked.stdout.decode(),
                        "stderr": checked.stderr.decode(),
                    }
                )
                require(checked.returncode == 0, "runtime-wheel dependency check failed")
            umask_022()
            destination = GuardedDestination(
                plan.scheme,
                str(plan.prefix / "bin/python"),
                "posix",
                bytecode_optimization_levels=(),
            )
            installer.install(source, destination, plan.metadata[wheel.row["filename"]])
            archive.close()
        require(not allowed, "planned payload was not written")
        actual = inventory(plan.prefix)
        expected_directories = {".", "bin", "lib", "lib/python3.12", SITE}
        expected_directories.update(
            str(parent) for name in plan.files for parent in PurePosixPath(name).parents
        )
        require(
            {name for name, item in actual.items() if item["kind"] == "directory"}
            == expected_directories,
            "unexpected/missing output directory",
        )
        expected_links = {"bin/python", "bin/python3", "bin/python3.12", "lib64"}
        require(
            {name for name, item in actual.items() if item["kind"] == "symlink"} == expected_links,
            "unexpected/missing scaffold link",
        )
        require(
            {name for name, item in actual.items() if item["kind"] == "file"}
            == set(plan.files) | (SCAFFOLD_RESERVED - expected_links),
            "unexpected/missing output file",
        )
        for name, item in actual.items():
            if name in plan.files:
                require(
                    item["kind"] == "file" and item["mode"] == plan.files[name]["mode"],
                    "installed type/mode mismatch",
                )
            elif item["kind"] == "file":
                require(
                    name in SCAFFOLD_RESERVED and item["mode"] == 0o644,
                    "unexpected scaffold file/mode: " + name,
                )
            elif item["kind"] == "symlink":
                require(
                    name in {"bin/python", "bin/python3", "bin/python3.12", "lib64"}
                    and item["mode"] == 0o777,
                    "unexpected scaffold link",
                )
                target = {
                    "bin/python": str(python),
                    "bin/python3": "python",
                    "bin/python3.12": "python",
                    "lib64": "lib",
                }[name]
                require(item["target"] == target, "scaffold link target mismatch")
            else:
                require(item["mode"] == 0o755, "unexpected directory mode")
        verify_records(plan.prefix)
        return phase_checks
    finally:
        sys.path[:] = previous_path


def clean_environment():
    """Return explicit no-acquisition/no-bytecode subprocess policy without selectors.

    Preserves proxy/CA configuration for policy compliance, but no frontend uses
    networking. Actual offline execution requires its separately measured venue
    boundary as well as these flags. Never claims flags are packet-level proof.
    """
    env = os.environ.copy()
    for name in list(env):
        if name.startswith("UV_") and name != "UV_CACHE_DIR":
            env.pop(name)
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "CONDA_PREFIX",
        "UV_PROJECT",
        "UV_PROJECT_ENVIRONMENT",
        "UV_PYTHON",
        "UV_WORKING_DIRECTORY",
    ):
        env.pop(name, None)
    env.update(
        UV_OFFLINE="1",
        UV_PYTHON_DOWNLOADS="never",
        PYTHONDONTWRITEBYTECODE="1",
        UV_NO_SYNC="1",
        UV_FROZEN="1",
        PYTHONNOUSERSITE="1",
        PYTHONHASHSEED="0",
        TZ="UTC",
        LANG="C.UTF-8",
        SOURCE_DATE_EPOCH="1793034850",
    )
    return env


def verify_records(prefix):
    """Validate every installed RECORD row/size/hash and bidirectional file ownership.

    Paths may use installer-generated ../ scripts/data relocations but must resolve
    inside the prefix. Only each RECORD self-row may omit hash/size; only reviewed
    scaffold files/links may lack RECORD ownership. Returns total verified rows.
    """
    prefix = Path(prefix)
    site = prefix / SITE
    owners, count = {}, 0
    for record in sorted(site.glob("*.dist-info/RECORD")):
        seen = set()
        for row in csv.reader(io.StringIO(record.read_text(), newline=""), strict=True):
            require(len(row) == 3, "bad installed RECORD row")
            name, digest, size = row
            path = (site / name).resolve()
            require(
                path.is_relative_to(prefix) and path.is_file() and not (site / name).is_symlink(),
                "installed RECORD escape/missing",
            )
            relative = path.relative_to(prefix).as_posix()
            require(
                relative not in seen and relative not in owners, "duplicate installed ownership"
            )
            seen.add(relative)
            owners[relative] = str(record)
            if path == record:
                require((digest, size) == ("", ""), "bad installed RECORD self-row")
            else:
                expected = (
                    base64.urlsafe_b64encode(hashlib.sha256(path.read_bytes()).digest())
                    .decode()
                    .rstrip("=")
                )
                require(
                    digest == "sha256=" + expected and size == str(path.stat().st_size),
                    "installed RECORD mismatch",
                )
            count += 1
        require(record.relative_to(prefix).as_posix() in seen, "installed RECORD omits itself")
    for name, item in inventory(prefix).items():
        if item["kind"] != "directory" and name not in SCAFFOLD_RESERVED:
            require(name in owners, "unowned installed payload: " + name)
    return count
