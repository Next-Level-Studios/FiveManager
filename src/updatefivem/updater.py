from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

import requests

GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/Next-Level-Studios/fivem-updater/releases/latest"


@dataclass(frozen=True)
class UpdateInfo:
    current_version: str
    latest_version: str
    release_url: str
    wheel_name: str
    wheel_url: str


def fetch_latest_release(api_url: str = GITHUB_LATEST_RELEASE_API) -> dict[str, Any]:
    response = requests.get(api_url, timeout=30)
    response.raise_for_status()
    return response.json()


def find_wheel_asset(release: dict[str, Any]) -> dict[str, Any]:
    for asset in release.get("assets", []):
        name = asset.get("name", "")
        if name.startswith("updatefivem-") and name.endswith(".whl") and asset.get("browser_download_url"):
            return asset
    raise RuntimeError("Latest release does not contain an updatefivem wheel asset")


def normalise_version(version: str) -> tuple[int, ...]:
    """Return a comparable tuple from versions like 'v0.1.8' or '1.2.3-beta'."""
    match = re.search(r"(\d+(?:\.\d+)*)", version)
    if not match:
        return (0,)
    return tuple(int(part) for part in match.group(1).split("."))


def check_for_newer_release(current_version: str, release: dict[str, Any]) -> UpdateInfo | None:
    latest_version = str(release.get("tag_name") or "")
    if not latest_version:
        return None
    if normalise_version(latest_version) <= normalise_version(current_version):
        return None
    asset = find_wheel_asset(release)
    return UpdateInfo(
        current_version=current_version,
        latest_version=latest_version,
        release_url=release.get("html_url") or "https://github.com/Next-Level-Studios/fivem-updater/releases/latest",
        wheel_name=asset.get("name", "updatefivem.whl"),
        wheel_url=asset["browser_download_url"],
    )


def build_pip_upgrade_command(url: str, python_executable: str | None = None) -> list[str]:
    return [python_executable or sys.executable, "-m", "pip", "install", "--upgrade", url]


def latest_wheel_info() -> tuple[str, str, str]:
    release = fetch_latest_release()
    asset = find_wheel_asset(release)
    tag = release.get("tag_name", "latest")
    name = asset.get("name", "updatefivem.whl")
    url = asset["browser_download_url"]
    return tag, name, url


def run_self_update(dry_run: bool = False) -> tuple[str, str, str, list[str]]:
    tag, name, url = latest_wheel_info()
    cmd = build_pip_upgrade_command(url)
    if not dry_run:
        subprocess.run(cmd, check=True)
    return tag, name, url, cmd
