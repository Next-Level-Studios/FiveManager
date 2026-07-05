from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from .config import server_cfg_exec_arg

SERVICE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def validate_service_name(name: str) -> None:
    if not SERVICE_NAME_RE.match(name):
        raise ValueError("service_name may only contain letters, numbers, dot, underscore, and dash")


def render_systemd_unit(config: dict) -> str:
    service_name = config["service_name"]
    validate_service_name(service_name)
    server_dir = str(Path(config["server_dir"]).resolve())
    server_cfg = server_cfg_exec_arg(config)
    run_user = str(config.get("run_user") or "fivem")
    fx_cmd = f"exec ./run.sh +exec {shlex.quote(server_cfg)}"
    tmux_cmd = f"/usr/bin/tmux new-session -d -s {shlex.quote(service_name)} /bin/sh -lc {shlex.quote(fx_cmd)}"
    return f"""[Unit]
Description=FiveM Server ({service_name})
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
User={run_user}
WorkingDirectory={server_dir}
ExecStart={tmux_cmd}
ExecStop=/usr/bin/tmux send-keys -t {service_name} C-c
ExecStop=/bin/sleep 5
ExecStop=/usr/bin/tmux kill-session -t {service_name}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""


def service_path(service_name: str) -> Path:
    validate_service_name(service_name)
    return Path("/etc/systemd/system") / f"{service_name}.service"


def install_service(config: dict, dry_run: bool = False) -> str:
    if not shutil.which("tmux"):
        raise RuntimeError("tmux is required. Install it with: sudo apt install tmux")
    unit = render_systemd_unit(config)
    if dry_run:
        return unit
    path = service_path(config["service_name"])
    path.write_text(unit, encoding="utf-8")
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    return unit


def systemctl_args(action: str, service_name: str) -> list[str]:
    validate_service_name(service_name)
    base = ["systemctl", action, service_name]
    if action in {"start", "stop", "restart"} and os.geteuid() != 0:
        return ["sudo", *base]
    return base


def service_is_active(service_name: str) -> bool:
    validate_service_name(service_name)
    result = subprocess.run(["systemctl", "is-active", "--quiet", service_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def service_unit_exists(service_name: str) -> bool:
    validate_service_name(service_name)
    result = subprocess.run(["systemctl", "cat", service_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def tmux_session_exists(service_name: str) -> bool:
    validate_service_name(service_name)
    result = subprocess.run(["tmux", "has-session", "-t", service_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0
