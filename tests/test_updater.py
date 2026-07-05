import pytest

from updatefivem.updater import (
    build_pip_upgrade_command,
    check_for_newer_release,
    find_wheel_asset,
    normalise_version,
)


def test_find_wheel_asset_prefers_updatefivem_wheel():
    release = {
        "tag_name": "v0.1.3",
        "assets": [
            {"name": "notes.txt", "browser_download_url": "https://example.test/notes.txt"},
            {"name": "updatefivem-0.1.3-py3-none-any.whl", "browser_download_url": "https://example.test/updatefivem.whl"},
        ],
    }

    asset = find_wheel_asset(release)

    assert asset["name"] == "updatefivem-0.1.3-py3-none-any.whl"
    assert asset["browser_download_url"] == "https://example.test/updatefivem.whl"


def test_find_wheel_asset_raises_without_wheel():
    with pytest.raises(RuntimeError, match="wheel"):
        find_wheel_asset({"assets": [{"name": "source.tar.gz"}]})


def test_build_pip_upgrade_command_uses_current_python():
    cmd = build_pip_upgrade_command("https://example.test/updatefivem.whl", python_executable="/opt/updatefivem/venv/bin/python")

    assert cmd == [
        "/opt/updatefivem/venv/bin/python",
        "-m",
        "pip",
        "install",
        "--upgrade",
        "https://example.test/updatefivem.whl",
    ]


def test_normalise_version_handles_tags_and_suffixes():
    assert normalise_version("v0.1.8") == (0, 1, 8)
    assert normalise_version("0.2.0") == (0, 2, 0)
    assert normalise_version("v1.2.3-beta") == (1, 2, 3)


def test_check_for_newer_release_detects_update():
    release = {
        "tag_name": "v0.1.9",
        "html_url": "https://github.com/Next-Level-Studios/fivem-updater/releases/tag/v0.1.9",
        "assets": [
            {"name": "updatefivem-0.1.9-py3-none-any.whl", "browser_download_url": "https://example.test/updatefivem.whl"},
        ],
    }

    update = check_for_newer_release("0.1.8", release)

    assert update is not None
    assert update.current_version == "0.1.8"
    assert update.latest_version == "v0.1.9"
    assert update.wheel_url == "https://example.test/updatefivem.whl"


def test_check_for_newer_release_returns_none_when_current():
    release = {
        "tag_name": "v0.1.8",
        "assets": [
            {"name": "updatefivem-0.1.8-py3-none-any.whl", "browser_download_url": "https://example.test/updatefivem.whl"},
        ],
    }

    assert check_for_newer_release("0.1.8", release) is None
