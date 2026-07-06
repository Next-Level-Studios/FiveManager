from pathlib import Path

import pytest

from fivemanager.config import add_server, default_config, get_server, next_ports, next_server_id, port_conflicts, remove_server, slugify
from fivemanager.paths import OLD_CONFIG_PATH, cache_dir, config_path


def test_default_paths_are_fivemanager_xdg_paths(monkeypatch, tmp_path):
    monkeypatch.delenv("FIVEMANAGER_CONFIG_PATH", raising=False)
    monkeypatch.delenv("FIVEMANAGER_CACHE_DIR", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    assert config_path() == tmp_path / "config" / "fivemanager" / "config.json"
    assert cache_dir() == tmp_path / "cache" / "fivemanager"


def test_slugify_server_names():
    assert slugify("Main RP Server") == "main-rp-server"
    assert slugify("  DEV_01!! ") == "dev_01"


def test_add_server_rejects_unsafe_internal_key():
    cfg = default_config()
    cfg["runtime_dir"] = "/runtime"
    with pytest.raises(RuntimeError, match="internal server key"):
        add_server(cfg, name="Bad", key="bad;rm -rf", data_path="/srv/bad", cfg_path="/srv/bad/server.cfg", txadmin_port=40120, fxserver_port=30120, interface="0.0.0.0")


def test_add_server_rejects_duplicate_internal_key():
    cfg = default_config()
    cfg["runtime_dir"] = "/runtime"
    add_server(cfg, name="Main", key="main", data_path="/srv/main", cfg_path="/srv/main/server.cfg", txadmin_port=40120, fxserver_port=30120, interface="0.0.0.0")

    with pytest.raises(RuntimeError, match="internal server key main is already used by Main"):
        add_server(cfg, name="Copy", key="main", data_path="/srv/copy", cfg_path="/srv/copy/server.cfg", txadmin_port=40121, fxserver_port=30121, interface="0.0.0.0")


def test_stable_ids_reuse_lowest_free_id():
    cfg = default_config()
    cfg["runtime_dir"] = "/runtime"
    add_server(cfg, name="one", key="one", data_path="/srv/one", cfg_path="/srv/one/server.cfg", txadmin_port=40120, fxserver_port=30120, interface="0.0.0.0")
    add_server(cfg, name="two", key="two", data_path="/srv/two", cfg_path="/srv/two/server.cfg", txadmin_port=40121, fxserver_port=30121, interface="0.0.0.0")
    remove_server(cfg, 1)
    assert next_server_id(cfg) == 1


def test_next_ports_increment_from_existing_servers():
    cfg = default_config()
    cfg["servers"] = [{"id": 1, "name": "one", "txadmin_port": 40120, "fxserver_port": 30120}]
    assert next_ports(cfg) == (40121, 30121)


def test_port_conflicts_report_duplicate_ports():
    cfg = default_config()
    cfg["servers"] = [{"id": 1, "name": "one", "txadmin_port": 40120, "fxserver_port": 30120}]
    conflicts = port_conflicts(cfg, 40120, 30121)
    assert "txAdmin port 40120" in conflicts[0]


def test_get_server_raises_for_missing_id():
    with pytest.raises(RuntimeError, match="No configured server"):
        get_server(default_config(), 99)
