"""Minimal PEP 660 frontend operations for #1250's isolated Hatchling build.

Executed with -I in either the dedicated build venv (inspect/build) or the target
venv (record). No package acquisition, resolver, Genia execution or acceptance.
"""

from __future__ import annotations

import base64
import csv
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import re
import sys
import tomllib


def canonical(name):
    """Normalize distribution names using the packaging-name equivalence rule."""
    return re.sub(r"[-_.]+", "-", name).lower()


def inspect_environment(inputs, report):
    """Require the complete build distribution/version set, retaining any drift."""
    expected = sorted(f"{p['name']}=={p['version']}" for p in inputs["packages"])
    actual = sorted(f"{canonical(d.metadata['Name'])}=={d.version}" for d in metadata.distributions())
    report.write_text(json.dumps({"expected": expected, "actual": actual}, indent=2) + "\n")
    if actual != expected:
        raise RuntimeError("build distribution drift")
    return actual


def build(inputs, root, output, report):
    """Validate static/dynamic requirements and build the existing editable project.

    Every active requirement must already be satisfied in the exact isolated
    inventory. Hatchling receives the original pyproject; no build contract edits.
    Record the produced wheel hash and requirements before returning its filename.
    """
    actual = inspect_environment(inputs, report)
    from packaging.requirements import Requirement

    def validate(requirements):
        """Reject any active backend requirement absent from the pinned closure."""
        for text in requirements:
            requirement = Requirement(text)
            if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
                continue
            try:
                version = metadata.version(requirement.name)
            except metadata.PackageNotFoundError as error:
                raise RuntimeError(f"missing pinned build requirement: {text}") from error
            if requirement.url or not requirement.specifier.contains(version):
                raise RuntimeError(f"unsatisfied pinned build requirement: {text}")

    project = tomllib.loads((root / "pyproject.toml").read_text())
    system = project["build-system"]
    if system["build-backend"] != "hatchling.build" or "backend-path" in system:
        raise RuntimeError("unregistered build backend")
    static = system["requires"]
    validate(static)
    os.chdir(root)
    from hatchling import build as hatchling
    dynamic = hatchling.get_requires_for_build_editable({})
    validate(dynamic)
    filename = hatchling.build_editable(str(output), {})
    wheel = output / filename
    if Path(filename).name != filename or not wheel.is_file() or not filename.endswith(".whl"):
        raise RuntimeError("invalid editable wheel output")
    report.write_text(json.dumps({
        "actual": actual, "static_requires": static, "dynamic_requires": dynamic,
        "wheel": filename, "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "source": str(root), "python": sys.version,
    }, indent=2) + "\n")


def verify_record(record):
    """Validate installed RECORD structure, unique safe paths and SHA-256/size pairs.

    uv's evidenced wheel install uses SHA-256 for every entry except RECORD's
    own empty pair. Relative console-script paths may climb within the venv;
    missing files, paths outside it, ambiguous rows or bad hashes/sizes reject.
    Return parsed rows only after every entry has verified, without mutation.
    """
    try:
        environment = Path(sys.prefix).resolve()
        if not record.resolve().is_relative_to(environment):
            raise ValueError("RECORD outside target environment")
        with record.open(newline="") as stream:
            rows = list(csv.reader(stream, strict=True))
        seen = set()
        self_name = record.parent.name + "/RECORD"
        for row in rows:
            if len(row) != 3 or not row[0] or row[0] in seen or Path(row[0]).is_absolute():
                raise ValueError("invalid/duplicate RECORD row")
            seen.add(row[0])
            target = (record.parent.parent / row[0]).resolve(strict=True)
            if not target.is_relative_to(environment) or not target.is_file():
                raise ValueError("RECORD path escaped target")
            if row[0] == self_name:
                if row[1:] != ["", ""]:
                    raise ValueError("invalid RECORD self-row")
                continue
            content = target.read_bytes()
            digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
            if row[1] != "sha256=" + digest or row[2] != str(len(content)):
                raise ValueError("RECORD hash/size mismatch")
        if self_name not in seen:
            raise ValueError("missing RECORD self-row")
        return rows
    except (OSError, ValueError, csv.Error) as error:
        raise RuntimeError("invalid installed RECORD: " + str(error)) from error


def record_editable(root):
    """Apply frontend-owned PEP 610 editable metadata and maintain installed RECORD.

    The wheel is an actual PEP 660 editable wheel, installed by uv without deps.
    PEP 660 requires its frontend to record the source URL and editable=true;
    installing the intermediate wheel by archive path alone cannot supply that.
    No distribution/version is removed or hidden from freeze comparison.
    """
    dist = metadata.distribution("genia")
    records = [f for f in dist.files or () if str(f).endswith(".dist-info/RECORD")]
    if len(records) != 1:
        raise RuntimeError("installed Genia RECORD missing or ambiguous")
    record = Path(dist.locate_file(records[0]))
    rows = verify_record(record)
    direct = record.parent / "direct_url.json"
    content = (json.dumps({"url": root.as_uri(), "dir_info": {"editable": True}}) + "\n").encode()
    direct.write_bytes(content)
    relative = record.parent.name + "/direct_url.json"
    rows = [row for row in rows if row[0] != relative]
    digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
    rows.append([relative, "sha256=" + digest, str(len(content))])
    with record.open("w", newline="") as stream:
        csv.writer(stream).writerows(rows)
    verify_record(record)
    print(direct.read_text().strip())


def main(argv):
    """Run only the explicit isolated inspect/build or installed-metadata operation."""
    mode = argv[0]
    if mode == "record":
        record_editable(Path(argv[1]).resolve())
    elif mode == "inspect":
        inspect_environment(json.loads(Path(argv[1]).read_text()), Path(argv[2]))
    elif mode == "build":
        build(json.loads(Path(argv[1]).read_text()), Path(argv[2]).resolve(),
              Path(argv[3]).resolve(), Path(argv[4]))
    else:
        raise RuntimeError("unknown editable frontend operation")


if __name__ == "__main__":
    main(sys.argv[1:])
