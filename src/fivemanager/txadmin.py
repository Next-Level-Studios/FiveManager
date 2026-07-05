from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

TEMPLATE_PATH = Path.home() / ".config" / "fivemanager" / "txadmin-template.json"
DEFAULT_TEMPLATE = {
    "version": 2,
    "general": {"serverName": "servername"},
    "server": {"dataPath": "/full/path/to/server/", "cfgPath": "/full/path/to/server/server.cfg"},
    "whitelist": {"mode": "approvedLicense", "rejectionMessage": "Set up your server in TXAdmin"},
    "gameFeatures": {"menuPageKey": "Backquote"},
}


def load_template(path: Path | None = None) -> dict[str, Any]:
    template_path = path or TEMPLATE_PATH
    try:
        if template_path.exists():
            with template_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
    except OSError:
        return copy.deepcopy(DEFAULT_TEMPLATE)
    return copy.deepcopy(DEFAULT_TEMPLATE)


def build_txadmin_config(server: dict[str, Any], template: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = copy.deepcopy(template or load_template())
    cfg.setdefault("general", {})["serverName"] = server["name"]
    cfg.setdefault("server", {})["dataPath"] = server["data_path"]
    cfg.setdefault("server", {})["cfgPath"] = server["cfg_path"]
    return cfg


def write_txadmin_profile(runtime_dir: Path, server: dict[str, Any], template: dict[str, Any] | None = None) -> Path:
    profile = runtime_dir / "txData" / server["key"] / "default"
    (profile / "data").mkdir(parents=True, exist_ok=True)
    (profile / "logs").mkdir(parents=True, exist_ok=True)
    config_path = profile / "config.json"
    with config_path.open("w", encoding="utf-8") as fh:
        json.dump(build_txadmin_config(server, template), fh, indent=2)
        fh.write("\n")
    return profile
