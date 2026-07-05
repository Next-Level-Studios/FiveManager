from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn, TimeRemainingColumn, TransferSpeedColumn

ARTIFACT_PAGE_URL = "https://runtime.fivem.net/artifacts/fivem/build_proot_linux/master/"
BLUE_HEX = "#3273dc"
BLUE_RGB = "rgb(50, 115, 220)"


@dataclass(frozen=True)
class Artifact:
    build: str
    url: str
    recommended: bool
    icon_color: str | None = None


def fetch_artifact_page(url: str = ARTIFACT_PAGE_URL) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def _style_is_blue(style: str | None) -> bool:
    if not style:
        return False
    normalised = re.sub(r"\s+", " ", style.strip().lower())
    compact = normalised.replace(" ", "")
    return BLUE_HEX in compact or BLUE_RGB.replace(" ", "") in compact


def _build_from_url(url: str, text: str = "") -> str:
    match = re.search(r"/(\d+)(?:-[^/]*)?/(?:[^/]+\.tar\.xz)$", url)
    if match:
        return match.group(1)
    match = re.search(r"\b(\d{3,})\b", text)
    if match:
        return match.group(1)
    return Path(url).stem.replace(".tar", "")


def parse_artifacts(html: str, base_url: str = ARTIFACT_PAGE_URL) -> list[Artifact]:
    soup = BeautifulSoup(html, "html.parser")
    artifacts: list[Artifact] = []
    rows = soup.find_all("tr") or soup.select(".panel-block")
    for row in rows:
        if getattr(row, "name", None) == "a" and row.get("href") and ".tar.xz" in row.get("href"):
            link = row
        else:
            link = row.find("a", href=lambda href: bool(href and ".tar.xz" in href))
        if not link:
            continue
        icon = row.find(class_=lambda classes: classes and "panel-icon" in str(classes).split())
        style = icon.get("style") if icon else None
        classes = row.get("class") or []
        computed_blue = "panel-block" in classes and "is-active" in classes and icon is not None
        url = urljoin(base_url, link.get("href"))
        artifacts.append(
            Artifact(
                build=_build_from_url(url, row.get_text(" ", strip=True)),
                url=url,
                recommended=_style_is_blue(style) or computed_blue,
                icon_color=style,
            )
        )
    return artifacts


def select_blue_recommended(artifacts: list[Artifact]) -> Artifact:
    for artifact in artifacts:
        if artifact.recommended:
            return artifact
    raise RuntimeError("Could not find a blue recommended artifact row on the FiveM artifacts page")


def resolve_artifact(value: str | None, artifacts: list[Artifact]) -> Artifact:
    if not value:
        return select_blue_recommended(artifacts)
    if value.startswith("http://"):
        raise RuntimeError("Artifact URLs must use HTTPS")
    if value.startswith("https://"):
        parsed = urlparse(value)
        if not parsed.path.endswith(".tar.xz"):
            raise RuntimeError("Artifact URL must point to a .tar.xz file")
        return Artifact(build=_build_from_url(value), url=value, recommended=False)
    for artifact in artifacts:
        if artifact.build == value:
            return artifact
    raise RuntimeError(f"Artifact build not found on artifacts page: {value}")


def download_artifact(artifact: Artifact, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(artifact.url).name or f"{artifact.build}.tar.xz"
    if not filename.endswith(".tar.xz"):
        filename = f"{artifact.build}.tar.xz"
    dest = cache_dir / f"{artifact.build}-{filename}"

    with requests.get(artifact.url, stream=True, timeout=60) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length") or 0)
        if dest.exists() and total and dest.stat().st_size == total:
            return dest
        with Progress(
            TextColumn("[bold blue]Downloading[/] {task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task(filename, total=total or None)
            with dest.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue
                    fh.write(chunk)
                    progress.update(task, advance=len(chunk))
    return dest
