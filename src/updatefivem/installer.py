from __future__ import annotations

import os
import shutil
import tarfile
import tempfile
from pathlib import Path


def _safe_member_path(root: Path, member_name: str) -> Path:
    target = (root / member_name).resolve()
    root_resolved = root.resolve()
    if target != root_resolved and root_resolved not in target.parents:
        raise RuntimeError(f"Refusing to extract unsafe tar member: {member_name}")
    return target


def _validate_tar_member(root: Path, member: tarfile.TarInfo) -> None:
    _safe_member_path(root, member.name)
    if member.issym() or member.islnk():
        # Tar links are resolved relative to the link's containing directory.
        # Reject absolute or escaping targets before extraction so an archive
        # cannot plant links pointing outside the temporary work directory.
        link_target = Path(member.linkname)
        if link_target.is_absolute():
            raise RuntimeError(f"Refusing to extract unsafe tar link: {member.name} -> {member.linkname}")
        _safe_member_path((root / member.name).parent, member.linkname)


def extract_artifact(archive_path: Path, work_dir: Path) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    extract_root = Path(tempfile.mkdtemp(prefix="extract-", dir=work_dir))
    with tarfile.open(archive_path, "r:xz") as tar:
        for member in tar.getmembers():
            _validate_tar_member(extract_root, member)
        tar.extractall(extract_root, filter="fully_trusted")
    for root, dirs, _files in os.walk(extract_root):
        root_path = Path(root)
        if not root_path.is_symlink():
            root_path.chmod(root_path.stat().st_mode | 0o700)
        for dirname in dirs:
            path = Path(root) / dirname
            if path.is_symlink():
                continue
            path.chmod(path.stat().st_mode | 0o700)
    return extract_root


def find_payload_dir(extracted_dir: Path) -> Path:
    if (extracted_dir / "alpine").is_dir() and (extracted_dir / "run.sh").is_file():
        return extracted_dir
    for child in extracted_dir.iterdir():
        if child.is_dir() and (child / "alpine").is_dir() and (child / "run.sh").is_file():
            return child
    raise RuntimeError("Extracted artifact does not contain alpine/ and run.sh")


def validate_payload(payload_dir: Path) -> None:
    if not (payload_dir / "alpine").is_dir():
        raise RuntimeError(f"Artifact payload missing alpine/: {payload_dir}")
    if not (payload_dir / "run.sh").is_file():
        raise RuntimeError(f"Artifact payload missing run.sh: {payload_dir}")


def install_payload(payload_dir: Path, server_dir: Path) -> None:
    validate_payload(payload_dir)
    if not server_dir.exists():
        raise RuntimeError(f"Server directory does not exist: {server_dir}")
    dest_alpine = server_dir / "alpine"
    dest_run = server_dir / "run.sh"
    if dest_alpine.exists():
        shutil.rmtree(dest_alpine)
    if dest_run.exists() or dest_run.is_symlink():
        dest_run.unlink()
    shutil.copytree(payload_dir / "alpine", dest_alpine, symlinks=True)
    shutil.copy2(payload_dir / "run.sh", dest_run)
    current_mode = dest_run.stat().st_mode
    dest_run.chmod(current_mode | 0o111)


def install_archive(archive_path: Path, cache_dir: Path, server_dir: Path) -> Path:
    extracted = extract_artifact(archive_path, cache_dir)
    payload = find_payload_dir(extracted)
    install_payload(payload, server_dir)
    return payload
