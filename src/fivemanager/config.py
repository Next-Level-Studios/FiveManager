from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .paths import config_path

Mode = Literal["runtime", "manager"]
SLUG_RE = re.compile(r"[^a-z0-9_-]+")
SAFE_KEY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def slugify(value: str) -> str:
    slug = SLUG_RE.sub("-", value.lower().strip()).strip("-")
    return slug or "server"


def default_config() -> dict[str, Any]:
    return {"version": 1, "app": "FiveManager", "mode": None, "runtime_dir": None, "servers": []}


def load_config() -> dict[str, Any] | None:
    path = config_path()
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    merged = default_config()
    merged.update(data)
    merged["servers"] = list(merged.get("servers") or [])
    return merged


def save_config(config: dict[str, Any]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)
        fh.write("\n")
    tmp.replace(path)


def require_config() -> dict[str, Any]:
    config = load_config()
    if not config:
        raise RuntimeError("FiveManager is not configured yet. Run fivemanager to launch setup.")
    return config


def runtime_dir(config: dict[str, Any]) -> Path:
    value = config.get("runtime_dir")
    if not value:
        raise RuntimeError("runtime_dir is not configured")
    return Path(value).expanduser()


def validate_runtime_dir(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        errors.append(f"Runtime directory does not exist: {path}")
    if not (path / "run.sh").exists():
        errors.append(f"Runtime directory missing run.sh: {path}")
    if not (path / "alpine").exists():
        errors.append(f"Runtime directory missing alpine/: {path}")
    return errors


def server_ids(config: dict[str, Any]) -> set[int]:
    return {int(server["id"]) for server in config.get("servers", [])}


def next_server_id(config: dict[str, Any]) -> int:
    used = server_ids(config)
    candidate = 1
    while candidate in used:
        candidate += 1
    return candidate


def next_ports(config: dict[str, Any]) -> tuple[int, int]:
    used_txa = {int(s.get("txadmin_port", 0)) for s in config.get("servers", [])}
    used_fxs = {int(s.get("fxserver_port", 0)) for s in config.get("servers", [])}
    txa = 40120
    fxs = 30120
    while txa in used_txa:
        txa += 1
    while fxs in used_fxs:
        fxs += 1
    return txa, fxs


def port_conflicts(config: dict[str, Any], txadmin_port: int, fxserver_port: int, exclude_id: int | None = None) -> list[str]:
    conflicts: list[str] = []
    for server in config.get("servers", []):
        if exclude_id is not None and int(server["id"]) == exclude_id:
            continue
        if int(server.get("txadmin_port", 0)) == int(txadmin_port):
            conflicts.append(f"txAdmin port {txadmin_port} is already used by {server['name']}")
        if int(server.get("fxserver_port", 0)) == int(fxserver_port):
            conflicts.append(f"FXServer port {fxserver_port} is already used by {server['name']}")
    return conflicts


def txdata_path(config: dict[str, Any], key: str) -> Path:
    return runtime_dir(config) / "txData" / key


def get_server(config: dict[str, Any], server_id: int) -> dict[str, Any]:
    for server in config.get("servers", []):
        if int(server["id"]) == int(server_id):
            return server
    raise RuntimeError(f"No configured server with ID {server_id}")


def add_server(config: dict[str, Any], *, name: str, key: str, data_path: str, cfg_path: str, txadmin_port: int, fxserver_port: int, interface: str) -> dict[str, Any]:
    if not SAFE_KEY_RE.match(key):
        raise RuntimeError("internal server key may only contain letters, numbers, dot, underscore, and dash")
    for server in config.get("servers", []):
        if str(server.get("key", "")).lower() == key.lower():
            raise RuntimeError(f"internal server key {key} is already used by {server['name']}")
    conflicts = port_conflicts(config, txadmin_port, fxserver_port)
    if conflicts:
        raise RuntimeError("; ".join(conflicts))
    server = {
        "id": next_server_id(config),
        "name": name,
        "key": key,
        "data_path": str(Path(data_path).expanduser()),
        "cfg_path": str(Path(cfg_path).expanduser()),
        "txadmin_port": int(txadmin_port),
        "fxserver_port": int(fxserver_port),
        "interface": interface or "0.0.0.0",
    }
    config.setdefault("servers", []).append(server)
    return server


def remove_server(config: dict[str, Any], server_id: int) -> dict[str, Any]:
    server = get_server(config, server_id)
    config["servers"] = [s for s in config.get("servers", []) if int(s["id"]) != int(server_id)]
    return server
