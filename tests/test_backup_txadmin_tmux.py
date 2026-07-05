import json
import subprocess
from pathlib import Path
from typing import Any, cast

from fivemanager.backup import create_backup, list_backups, restore_backup
from fivemanager.tmux import start_server, stop_server
from fivemanager.txadmin import build_txadmin_config, load_template, write_txadmin_profile


def test_backup_prunes_to_three_and_restore_replaces_runtime(tmp_path):
    runtime = tmp_path / "runtime"
    (runtime / "alpine").mkdir(parents=True)
    (runtime / "alpine" / "file.txt").write_text("original")
    (runtime / "txData" / "profile").mkdir(parents=True)
    (runtime / "txData" / "profile" / "config.json").write_text("{}")
    (runtime / "run.sh").write_text("run")

    for index in range(4):
        (runtime / "alpine" / "file.txt").write_text(f"backup-{index}")
        create_backup(runtime)

    backups = list_backups(runtime)
    assert len(backups) == 3
    (runtime / "alpine" / "file.txt").write_text("changed")
    restore_backup(runtime, backups[0])
    assert (runtime / "alpine" / "file.txt").read_text().startswith("backup-")
    assert (runtime / "run.sh").exists()


def test_txadmin_config_generation_and_profile_creation(tmp_path):
    server = {
        "name": "Main RP Server",
        "key": "main-rp",
        "data_path": str(tmp_path / "server-data"),
        "cfg_path": str(tmp_path / "server-data" / "server.cfg"),
    }
    cfg = build_txadmin_config(server)
    assert cfg["general"]["serverName"] == "Main RP Server"
    assert cfg["server"]["dataPath"] == server["data_path"]
    assert cfg["server"]["cfgPath"] == server["cfg_path"]

    profile = write_txadmin_profile(tmp_path / "runtime", server)
    assert profile == tmp_path / "runtime" / "txData" / "main-rp" / "default"
    assert (profile / "data").is_dir()
    assert (profile / "logs").is_dir()
    written = json.loads((profile / "config.json").read_text())
    assert written["general"]["serverName"] == "Main RP Server"


def test_txadmin_template_permission_error_falls_back_to_default(monkeypatch):
    class ForbiddenPath:
        def exists(self):
            raise PermissionError("blocked")

    cfg = load_template(cast(Any, ForbiddenPath()))

    assert cfg["version"] == 2
    assert cfg["general"]["serverName"] == "servername"


def test_txadmin_default_template_path_uses_current_home():
    import fivemanager.txadmin as txadmin

    assert txadmin.TEMPLATE_PATH == Path.home() / ".config" / "fivemanager" / "txadmin-template.json"


def test_start_server_builds_expected_tmux_command(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("fivemanager.tmux.session_exists", lambda name: False)
    monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: calls.append(args) or type("R", (), {"returncode": 0})())
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    server_data = tmp_path / "server-data"
    server_data.mkdir()
    server = {
        "id": 1,
        "name": "Main",
        "key": "main",
        "cfg_path": str(server_data / "server.cfg"),
        "txadmin_port": 40120,
        "fxserver_port": 30120,
        "interface": "0.0.0.0",
    }

    name = start_server(runtime, server)

    assert name == "fivemanager-1-main"
    cmd = calls[0]
    joined = " ".join(cmd)
    assert "TXHOST_DATA_PATH" in joined
    assert str(runtime / "txData" / "main") in joined
    assert "TXHOST_TXA_PORT" in joined
    assert str(runtime / "run.sh") in joined
    assert "main" in joined
    assert "server.cfg" in joined
