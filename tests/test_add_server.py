import json

import pytest
import typer

from fivemanager import cli
from fivemanager.config import default_config, save_config
from fivemanager.paths import config_path


def _configured_manager(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    runtime = tmp_path / "runtime"
    (runtime / "alpine").mkdir(parents=True)
    (runtime / "run.sh").write_text("#!/bin/sh\n")
    cfg = default_config()
    cfg["mode"] = "manager"
    cfg["runtime_dir"] = str(runtime)
    cfg["servers"] = [
        {
            "id": 1,
            "name": "Main",
            "key": "main",
            "data_path": str(tmp_path / "main-data"),
            "cfg_path": str(tmp_path / "main-data" / "server.cfg"),
            "txadmin_port": 40120,
            "fxserver_port": 30120,
            "interface": "0.0.0.0",
        }
    ]
    save_config(cfg)
    return runtime


def test_add_command_refuses_missing_config(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    messages = []
    monkeypatch.setattr(cli, "warn", messages.append)

    with pytest.raises(typer.Exit) as exc:
        cli.add_command()

    assert exc.value.exit_code == 1
    assert any("Run fivemanager setup first" in message for message in messages)


def test_add_command_refuses_runtime_only_config(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    cfg = default_config()
    cfg["mode"] = "runtime"
    cfg["runtime_dir"] = str(tmp_path / "runtime")
    save_config(cfg)
    messages = []
    monkeypatch.setattr(cli, "warn", messages.append)

    with pytest.raises(typer.Exit) as exc:
        cli.add_command()

    assert exc.value.exit_code == 1
    assert any("full manager mode" in message for message in messages)


def test_add_command_appends_server_bootstraps_profile_and_does_not_start_when_declined(monkeypatch, tmp_path):
    runtime = _configured_manager(tmp_path, monkeypatch)
    data_path = tmp_path / "dev-data"
    cfg_path = data_path / "server.cfg"
    answers = iter([
        "Dev Survival",
        "dev-survival",
        str(data_path),
        str(cfg_path),
        "40121",
        "30121",
        "0.0.0.0",
    ])
    starts = []

    monkeypatch.setattr("fivemanager.wizard.ask_text", lambda *args, **kwargs: next(answers))
    monkeypatch.setattr("fivemanager.wizard.ask_confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(cli, "ask_confirm", lambda *args, **kwargs: False)
    monkeypatch.setattr(cli, "start_server_by_id", lambda config, sid: starts.append(sid))

    cli.add_command()

    saved = json.loads(config_path().read_text())
    assert [server["id"] for server in saved["servers"]] == [1, 2]
    added = saved["servers"][1]
    assert added["name"] == "Dev Survival"
    assert added["key"] == "dev-survival"
    assert added["txadmin_port"] == 40121
    assert added["fxserver_port"] == 30121
    assert (data_path / "resources").is_dir()
    assert cfg_path.is_file()
    assert (runtime / "txData" / "dev-survival" / "default" / "config.json").is_file()
    assert starts == []


def test_add_command_starts_new_server_when_requested(monkeypatch, tmp_path):
    _configured_manager(tmp_path, monkeypatch)
    data_path = tmp_path / "second-data"
    cfg_path = data_path / "server.cfg"
    answers = iter([
        "Second",
        "second",
        str(data_path),
        str(cfg_path),
        "40121",
        "30121",
        "0.0.0.0",
    ])
    starts = []

    monkeypatch.setattr("fivemanager.wizard.ask_text", lambda *args, **kwargs: next(answers))
    monkeypatch.setattr("fivemanager.wizard.ask_confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(cli, "ask_confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(cli, "start_server_by_id", lambda config, sid: starts.append(sid))

    cli.add_command()

    assert starts == [2]
