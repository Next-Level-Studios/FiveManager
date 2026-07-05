from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests

GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/Next-Level-Studios/FiveManager/releases/latest"


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
        url = asset.get("browser_download_url")
        if name.startswith("fivemanager-") and name.endswith(".whl") and url:
            if urlparse(url).scheme != "https":
                raise RuntimeError("FiveManager wheel download URL must use HTTPS")
            return asset
    # Alpha transition fallback while repository/release assets may still be catching up.
    for asset in release.get("assets", []):
        name = asset.get("name", "")
        url = asset.get("browser_download_url")
        if name.endswith(".whl") and url:
            if urlparse(url).scheme != "https":
                raise RuntimeError("FiveManager wheel download URL must use HTTPS")
            return asset
    raise RuntimeError("Latest release does not contain a FiveManager wheel asset")


def normalise_version(version: str) -> tuple[int, ...]:
    match = re.search(r"(\d+(?:\.\d+)*)", version)
    if not match:
        return (0,)
    return tuple(int(part) for part in match.group(1).split("."))


def check_for_newer_release(current_version: str, release: dict[str, Any]) -> UpdateInfo | None:
    latest = str(release.get("tag_name") or "")
    if not latest or normalise_version(latest) <= normalise_version(current_version):
        return None
    asset = find_wheel_asset(release)
    return UpdateInfo(current_version, latest, release.get("html_url") or "https://github.com/Next-Level-Studios/FiveManager/releases/latest", asset.get("name", "fivemanager.whl"), asset["browser_download_url"])


def run_self_update(dry_run: bool = False) -> tuple[str, str, str, list[str]]:
    release = fetch_latest_release()
    asset = find_wheel_asset(release)
    tag = release.get("tag_name", "latest")
    name = asset.get("name", "fivemanager.whl")
    url = asset["browser_download_url"]
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", url]
    if not dry_run:
        subprocess.run(cmd, check=True)
    return tag, name, url, cmd
