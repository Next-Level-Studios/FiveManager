from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path


def session_name(server: dict) -> str:
    return f"fivemanager-{server['id']}-{server['key']}"


def session_exists(name: str) -> bool:
    return subprocess.run(["tmux", "has-session", "-t", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def start_server(runtime_dir: Path, server: dict) -> str:
    name = session_name(server)
    if session_exists(name):
        return name
    txdata_root = runtime_dir / "txData" / server["key"]
    run_sh = runtime_dir / "run.sh"
    env = (
        f"export TXHOST_DATA_PATH={str(txdata_root)!r}; "
        f"export TXHOST_TXA_PORT={str(server['txadmin_port'])!r}; "
        f"export TXHOST_FXS_PORT={str(server['fxserver_port'])!r}; "
        f"export TXHOST_INTERFACE={server.get('interface', '0.0.0.0')!r}; "
    )
    cmd = f"{env} cd {str(Path(server['cfg_path']).parent)!r}; {str(run_sh)!r} +exec {Path(server['cfg_path']).name!r}; code=$?; printf '\\nFiveM exited with status %s. Press Ctrl+B then D to detach.\\n' \"$code\"; exec /bin/sh"
    subprocess.run(["tmux", "new-session", "-d", "-s", name, "/bin/sh", "-lc", cmd], check=True)
    return name


def stop_server(server: dict, timeout: float = 5.0) -> None:
    name = session_name(server)
    if not session_exists(name):
        return
    subprocess.run(["tmux", "send-keys", "-t", name, "C-c"], check=False)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not session_exists(name):
            return
        time.sleep(0.25)
    subprocess.run(["tmux", "kill-session", "-t", name], check=False)


def restart_server(runtime_dir: Path, server: dict) -> str:
    stop_server(server)
    return start_server(runtime_dir, server)


def attach_console(server: dict) -> None:
    name = session_name(server)
    if not session_exists(name):
        raise RuntimeError(f"No tmux session named {name} was found")
    os.execvp("tmux", ["tmux", "attach-session", "-t", name])


def tmux_pane_pid(name: str) -> int | None:
    result = subprocess.run(["tmux", "display-message", "-p", "-t", name, "#{pane_pid}"], text=True, capture_output=True)
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def _children(pid: int) -> list[int]:
    result = subprocess.run(["pgrep", "-P", str(pid)], text=True, capture_output=True)
    if result.returncode != 0:
        return []
    return [int(x) for x in result.stdout.split() if x.isdigit()]


def process_tree(pid: int) -> set[int]:
    seen = {pid}
    stack = [pid]
    while stack:
        current = stack.pop()
        for child in _children(current):
            if child not in seen:
                seen.add(child)
                stack.append(child)
    return seen


def memory_bytes_for_session(name: str) -> int | None:
    pid = tmux_pane_pid(name)
    if pid is None:
        return None
    total_kb = 0
    for proc in process_tree(pid):
        try:
            with open(f"/proc/{proc}/status", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("VmRSS:"):
                        total_kb += int(line.split()[1])
                        break
        except OSError:
            continue
    return total_kb * 1024


def format_bytes(value: int | None) -> str:
    if value is None:
        return "-"
    units = ["B", "K", "M", "G", "T"]
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.1f}{unit}" if unit in {"G", "T"} else f"{amount:.0f}{unit}"
        amount /= 1024
    return f"{value}B"
