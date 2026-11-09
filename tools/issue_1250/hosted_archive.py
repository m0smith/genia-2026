"""Bounded ZIP-only extraction of GitHub qualification evidence, never executable content.

Only known evidence paths are accepted. Integrity/inventory checks precede any
publication; a successful snapshot has read-only modes outside the candidate.
This is not isolation against the snapshot owner/root changing permissions.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import zipfile

ROOT_FILES = {
    "manifest.json",
    "integration.json",
    "execution.log",
    "source-identity.json",
    "collection-result.json",
    "pytest.log",
    "junit.xml",
    "dispatch.json",
    "bootstrap.log",
    "uv-bootstrap.log",
}
STAGES = {
    "uv-version",
    "sync",
    "build-venv",
    "build-install",
    "build-editable",
    "project-install",
    "editable-metadata",
    "freeze",
    "installed-project",
    "editable-record",
}
DATA = {
    "cold-start.json",
    "identity.json",
    "freeze-diff.json",
    "build-inventory.json",
    "build-inputs.json",
    "build-requirements.txt",
    "project-requirements.txt",
    "after-sync.lock",
}


def allowed_path(name, directory=False):
    """Require canonical relative evidence names and at most one subject directory."""
    if (
        not name
        or "\\" in name
        or ":" in name
        or "\0" in name
        or name.startswith("/")
        or any(part in {"", ".", ".."} for part in name.split("/"))
    ):
        raise ValueError("unsafe archive path")
    parts = PurePosixPath(name).parts
    if directory:
        return len(parts) == 1 and parts[0] in {"baseline", "candidate"}
    if len(parts) == 1:
        return name in ROOT_FILES
    if len(parts) != 2 or parts[0] not in {"baseline", "candidate"}:
        return False
    label, filename = parts
    if filename == "manifest.json" or filename == label + ".lock":
        return True
    return filename in {
        f"{label}-{stage}.{suffix}" for stage in STAGES for suffix in ("json", "log")
    } or filename in {f"{label}-{suffix}" for suffix in DATA}


def extract_snapshot(
    data,
    destination,
    expected_manifest_sha256=None,
    *,
    max_archive=32 * 1024**2,
    max_total=64 * 1024**2,
    max_member=8 * 1024**2,
    max_files=256,
    max_ratio=200,
):
    """Validate ZIP entries/digests, then atomically publish one read-only snapshot.

    No extract()/extractall(), links, metadata permissions, tar or nested archives.
    The caller must first authenticate archive bytes against GitHub API metadata.
    A partial/failed extraction never creates the trusted destination. Existing
    destinations are rejected. Limits apply to declared and actually read bytes.
    """
    staging = None
    try:
        if len(data) > max_archive or not data.startswith(b"PK\x03\x04"):
            raise ValueError("unsupported or oversized archive")
        if destination.exists() or destination.is_symlink() or not destination.parent.is_dir():
            raise ValueError("destination must be new under an existing trusted parent")
        files, seen, total = {}, set(), 0
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > max_files:
                raise ValueError("archive entry count exceeded")
            for info in entries:
                directory = info.is_dir()
                name = info.filename[:-1] if directory else info.filename
                mode = info.external_attr >> 16
                kind = stat.S_IFMT(mode)
                if (
                    info.orig_filename != info.filename
                    or name in seen
                    or not allowed_path(name, directory)
                    or info.flag_bits & 1
                    or info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                    or kind not in ({0, stat.S_IFDIR} if directory else {0, stat.S_IFREG})
                ):
                    raise ValueError("unsafe, duplicate or unexpected archive entry")
                seen.add(name)
                # Reject Unix link/alternate-path extras. Only timestamp metadata is supported.
                extra = info.extra
                while extra:
                    if len(extra) < 4:
                        raise ValueError("malformed ZIP extra")
                    tag, length = (
                        int.from_bytes(extra[:2], "little"),
                        int.from_bytes(extra[2:4], "little"),
                    )
                    if tag != 0x5455 or len(extra) < 4 + length:
                        raise ValueError("unsupported ZIP link/extra metadata")
                    extra = extra[4 + length :]
                if directory:
                    if info.file_size:
                        raise ValueError("directory contains data")
                    continue
                if (
                    info.file_size > max_member
                    or info.file_size > max_ratio * max(info.compress_size, 1)
                    or total + info.file_size > max_total
                ):
                    raise ValueError("archive decompression limit exceeded")
                with archive.open(info) as stream:
                    content = stream.read(min(max_member, max_total - total) + 1)
                if len(content) != info.file_size or len(content) > max_member:
                    raise ValueError("archive expanded size mismatch")
                total += len(content)
                files[name] = content
        if "manifest.json" not in files:
            raise ValueError("artifact manifest missing")
        manifest_bytes = files["manifest.json"]
        if (
            expected_manifest_sha256 is not None
            and hashlib.sha256(manifest_bytes).hexdigest() != expected_manifest_sha256
        ):
            raise ValueError("qualification manifest digest mismatch")

        def unique_object(pairs):
            """Reject duplicate manifest paths instead of silently taking the last hash."""
            values = {}
            for key, value in pairs:
                if key in values:
                    raise ValueError("duplicate manifest path")
                values[key] = value
            return values

        expected = json.loads(manifest_bytes, object_pairs_hook=unique_object)
        actual = {
            name: hashlib.sha256(content).hexdigest()
            for name, content in files.items()
            if name != "manifest.json"
        }
        if (
            not isinstance(expected, dict)
            or expected != actual
            or any(not re.fullmatch(r"[0-9a-f]{64}", value) for value in expected.values())
        ):
            raise ValueError("artifact file inventory/hash mismatch")
        staging = Path(tempfile.mkdtemp(prefix=".untrusted-qualification-", dir=destination.parent))
        for name, content in files.items():
            path = staging / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(content)
            path.chmod(0o444)
        # Parent is control-plane owned; no candidate/test process may write here.
        if destination.exists() or destination.is_symlink():
            raise ValueError("destination appeared during verification")
        for path in sorted(staging.rglob("*"), reverse=True):
            if path.is_dir():
                path.chmod(0o555)
        staging.chmod(0o555)
        os.rename(staging, destination)
        staging = None
        return destination
    except (
        OSError,
        ValueError,
        TypeError,
        zipfile.BadZipFile,
        NotImplementedError,
        RuntimeError,
    ) as error:
        raise RuntimeError("qualification archive rejected: " + str(error)) from error
    finally:
        if staging is not None:
            for path in [staging, *staging.rglob("*")]:
                if path.is_dir():
                    path.chmod(0o700)
            shutil.rmtree(staging)
