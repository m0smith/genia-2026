"""Local adversarial ZIP fixtures for hosted evidence; no real artifact download."""

import hashlib
import importlib
import io
import json
import stat
import tarfile
import zipfile

import pytest


def security():
    """Load the proposed extraction interface lazily for deterministic RED."""
    return importlib.import_module("tools.issue_1250.hosted_archive")


def artifact(entries=None):
    """Build a minimal valid manifest-bound diagnostic ZIP entirely in memory."""
    files = {"execution.log": b"retained failure or preparation log\n"}
    files["manifest.json"] = json.dumps(
        {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    ).encode()
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        for name, data, mode, extra in entries or ():
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = mode << 16
            info.extra = extra
            archive.writestr(info, data)
    return out.getvalue()


@pytest.fixture(autouse=True)
def restore_owned_test_directory_modes(tmp_path):
    """Allow pytest to remove read-only snapshots after asserting their permissions."""
    yield
    for path in [tmp_path, *tmp_path.rglob("*")]:
        if not path.is_symlink():
            path.chmod(0o700 if path.is_dir() else 0o600)


def test_valid_snapshot_is_manifest_verified_and_read_only(tmp_path):
    target = tmp_path / "verified"
    result = security().extract_snapshot(artifact(), target)
    assert result == target
    assert (target / "execution.log").read_text().startswith("retained")
    assert all(not (p.stat().st_mode & 0o222) for p in [target, *target.rglob("*")])


@pytest.mark.parametrize(
    "name,mode,extra",
    [
        ("/outside", stat.S_IFREG | 0o600, b""),
        ("../outside", stat.S_IFREG | 0o600, b""),
        ("baseline/../../outside", stat.S_IFREG | 0o600, b""),
        ("baseline\\outside", stat.S_IFREG | 0o600, b""),
        ("C:/outside", stat.S_IFREG | 0o600, b""),
        ("baseline//x", stat.S_IFREG | 0o600, b""),
        ("baseline/./x", stat.S_IFREG | 0o600, b""),
        ("baseline/../x", stat.S_IFREG | 0o600, b""),
        ("baseline/baseline-sync.log", stat.S_IFLNK | 0o777, b""),
        ("baseline/baseline-sync.log", stat.S_IFIFO | 0o600, b""),
        ("baseline/baseline-sync.log", stat.S_IFCHR | 0o600, b""),
        ("baseline/baseline-sync.log", stat.S_IFREG | 0o600, b"\x6e\x75\x04\x00link"),
        ("unexpected.py", stat.S_IFREG | 0o600, b""),
        ("baseline/nesting/baseline-sync.log", stat.S_IFREG | 0o600, b""),
    ],
)
def test_malicious_entries_never_escape_or_publish(tmp_path, name, mode, extra):
    outside = tmp_path / "outside"
    outside.write_text("immutable outside sentinel")
    target = tmp_path / "untrusted"
    with pytest.raises(RuntimeError):
        security().extract_snapshot(artifact([(name, b"attack", mode, extra)]), target)
    assert not target.exists()
    assert outside.read_text() == "immutable outside sentinel"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["outside"]


def test_duplicate_and_ambiguous_paths_rejected(tmp_path):
    with pytest.warns(UserWarning, match="Duplicate"):
        data = artifact([("execution.log", b"duplicate", stat.S_IFREG | 0o600, b"")])
    with pytest.raises(RuntimeError):
        security().extract_snapshot(data, tmp_path / "target")
    assert not (tmp_path / "target").exists()


@pytest.mark.parametrize("limit", ["archive", "member", "total", "count", "ratio"])
def test_archive_resource_limits_fail_before_publication(tmp_path, limit):
    kwargs = {
        "archive": {"max_archive": 1},
        "member": {"max_member": 1},
        "total": {"max_total": 1},
        "count": {"max_files": 1},
        "ratio": {"max_ratio": 1},
    }[limit]
    with pytest.raises(RuntimeError):
        security().extract_snapshot(artifact(), tmp_path / "target", **kwargs)
    assert not (tmp_path / "target").exists()


@pytest.mark.parametrize("kind", ["corrupt", "tar-hardlink", "wrong-manifest", "extra-unlisted"])
def test_corruption_hardlinks_and_inventory_mismatch_rejected(tmp_path, kind):
    data = artifact()
    if kind == "corrupt":
        data = data[:20]
    elif kind == "tar-hardlink":
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as archive:
            info = tarfile.TarInfo("link")
            info.type, info.linkname = tarfile.LNKTYPE, "../outside"
            archive.addfile(info)
        data = stream.getvalue()
    elif kind == "extra-unlisted":
        data = artifact([("collection-result.json", b"{}", stat.S_IFREG | 0o600, b"")])
    expected = "0" * 64 if kind == "wrong-manifest" else None
    with pytest.raises(RuntimeError):
        security().extract_snapshot(data, tmp_path / "target", expected_manifest_sha256=expected)
    assert not (tmp_path / "target").exists()


def test_existing_destination_is_never_overwritten(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "original").write_text("keep")
    with pytest.raises(RuntimeError):
        security().extract_snapshot(artifact(), target)
    assert (target / "original").read_text() == "keep"


@pytest.mark.parametrize("kind", ["duplicate-manifest", "crc", "bomb"])
def test_ambiguous_manifest_crc_and_actual_ratio_bomb_fail_closed(tmp_path, kind):
    content = b"retained qualification log" if kind != "bomb" else b"x" * (1024 * 1024)
    digest = hashlib.sha256(content).hexdigest()
    manifest = '{"execution.log":"' + digest + '"}'
    if kind == "duplicate-manifest":
        manifest = '{"execution.log":"' + digest + '","execution.log":"' + digest + '"}'
    output = io.BytesIO()
    compression = zipfile.ZIP_STORED if kind == "crc" else zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(output, "w", compression) as archive:
        archive.writestr("execution.log", content)
        archive.writestr("manifest.json", manifest)
    data = output.getvalue()
    if kind == "crc":
        offset = data.index(content)
        data = data[:offset] + bytes([data[offset] ^ 1]) + data[offset + 1 :]
    with pytest.raises(RuntimeError):
        security().extract_snapshot(data, tmp_path / "target")
    assert not (tmp_path / "target").exists()
