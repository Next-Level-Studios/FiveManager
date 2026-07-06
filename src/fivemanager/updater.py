from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests

from . import __version__

GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/Next-Level-Studios/FiveManager/releases/latest"
GITHUB_RELEASES_API = "https://api.github.com/repos/Next-Level-Studios/FiveManager/releases"


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


def fetch_releases(api_url: str = GITHUB_RELEASES_API) -> list[dict[str, Any]]:
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


def latest_newer_release(current_version: str, include_prereleases: bool = False) -> UpdateInfo | None:
    if not include_prereleases:
        return check_for_newer_release(current_version, fetch_latest_release())
    best: UpdateInfo | None = None
    for release in fetch_releases():
        if release.get("draft"):
            continue
        update = check_for_newer_release(current_version, release)
        if update and (best is None or normalise_version(update.latest_version) > normalise_version(best.latest_version)):
            best = update
    return best


def install_update(update: UpdateInfo, dry_run: bool = False) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--disable-pip-version-check",
        "--quiet",
        update.wheel_url,
    ]
    if dry_run:
        return cmd
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        details = ["pip install failed."]
        if exc.stdout:
            details.append(f"stdout:\n{exc.stdout.strip()}")
        if exc.stderr:
            details.append(f"stderr:\n{exc.stderr.strip()}")
        raise RuntimeError("\n".join(details)) from exc
    return cmd


def run_self_update(dry_run: bool = False, include_prereleases: bool = False) -> tuple[str, str, str, list[str]]:
    update = latest_newer_release(__version__, include_prereleases=include_prereleases)
    if update is None:
        channel = "release/prerelease" if include_prereleases else "stable release"
        raise RuntimeError(f"No newer {channel} found for FiveManager {__version__}.")
    cmd = install_update(update, dry_run=dry_run)
    return update.latest_version, update.wheel_name, update.wheel_url, cmd
