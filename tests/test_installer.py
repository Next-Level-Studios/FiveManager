import io
import os
import tarfile
from pathlib import Path

import pytest

from updatefivem.installer import extract_artifact, find_payload_dir, install_payload, validate_payload


def make_tar(path: Path, members: dict[str, bytes]):
    with tarfile.open(path, "w:xz") as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            if name.endswith("/"):
                info.type = tarfile.DIRTYPE
                info.size = 0
                tar.addfile(info)
            else:
                info.size = len(data)
                if name.endswith("run.sh"):
                    info.mode = 0o755
                tar.addfile(info, io.BytesIO(data))


def test_extract_validate_and_install_payload(tmp_path):
    archive = tmp_path / "fx.tar.xz"
    make_tar(archive, {
        "alpine/": b"",
        "alpine/file.txt": b"new",
        "run.sh": b"#!/bin/sh\necho hi\n",
    })
    server = tmp_path / "server"
    (server / "alpine").mkdir(parents=True)
    (server / "alpine" / "old.txt").write_text("old")
    (server / "run.sh").write_text("old")
    (server / "server.cfg").write_text("keep")
    (server / "resources").mkdir()

    extracted = extract_artifact(archive, tmp_path / "work")
    payload = find_payload_dir(extracted)
    validate_payload(payload)
    install_payload(payload, server)

    assert (server / "alpine" / "file.txt").read_text() == "new"
    assert not (server / "alpine" / "old.txt").exists()
    assert (server / "server.cfg").read_text() == "keep"
    assert (server / "resources").is_dir()
    assert os.access(server / "run.sh", os.X_OK)


def test_validate_payload_rejects_missing_run_sh(tmp_path):
    payload = tmp_path / "payload"
    (payload / "alpine").mkdir(parents=True)
    with pytest.raises(RuntimeError, match="run.sh"):
        validate_payload(payload)


def test_validate_payload_rejects_missing_alpine(tmp_path):
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / "run.sh").write_text("run")
    with pytest.raises(RuntimeError, match="alpine"):
        validate_payload(payload)


def test_extract_rejects_path_traversal(tmp_path):
    archive = tmp_path / "evil.tar.xz"
    make_tar(archive, {"../evil": b"bad"})
    with pytest.raises(RuntimeError, match="unsafe"):
        extract_artifact(archive, tmp_path / "work")


def test_extract_rejects_symlink_escaping_extract_root(tmp_path):
    archive = tmp_path / "evil-link.tar.xz"
    with tarfile.open(archive, "w:xz") as tar:
        info = tarfile.TarInfo("alpine/evil-link")
        info.type = tarfile.SYMTYPE
        info.linkname = "../../outside"
        tar.addfile(info)

    with pytest.raises(RuntimeError, match="unsafe"):
        extract_artifact(archive, tmp_path / "work")


def test_extract_allows_absolute_symlink_used_by_fivem_artifact(tmp_path):
    archive = tmp_path / "fx-absolute-link.tar.xz"
    with tarfile.open(archive, "w:xz") as tar:
        alpine = tarfile.TarInfo("alpine/")
        alpine.type = tarfile.DIRTYPE
        tar.addfile(alpine)

        link = tarfile.TarInfo("alpine/lib/ld-linux-x86-64.so.2")
        link.type = tarfile.SYMTYPE
        link.linkname = "/usr/glibc-compat/lib/ld-linux-x86-64.so.2"
        tar.addfile(link)

        run = tarfile.TarInfo("run.sh")
        data = b"#!/bin/sh\n"
        run.size = len(data)
        tar.addfile(run, io.BytesIO(data))

    extracted = extract_artifact(archive, tmp_path / "work")

    link_path = extracted / "alpine/lib/ld-linux-x86-64.so.2"
    assert link_path.is_symlink()
    assert os.readlink(link_path) == "/usr/glibc-compat/lib/ld-linux-x86-64.so.2"


def test_extract_rejects_special_tar_members(tmp_path):
    archive = tmp_path / "evil-special.tar.xz"
    with tarfile.open(archive, "w:xz") as tar:
        info = tarfile.TarInfo("alpine/fifo")
        info.type = tarfile.FIFOTYPE
        tar.addfile(info)

    with pytest.raises(RuntimeError, match="unsupported tar member"):
        extract_artifact(archive, tmp_path / "work")
