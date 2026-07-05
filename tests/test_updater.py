import pytest

from fivemanager.updater import GITHUB_LATEST_RELEASE_API, check_for_newer_release, find_wheel_asset, normalise_version


def test_find_wheel_asset_prefers_fivemanager_wheel():
    release = {"assets": [
        {"name": "notes.txt", "browser_download_url": "https://example.test/notes.txt"},
        {"name": "fivemanager-0.9.0-py3-none-any.whl", "browser_download_url": "https://example.test/fivemanager.whl"},
    ]}
    asset = find_wheel_asset(release)
    assert asset["name"] == "fivemanager-0.9.0-py3-none-any.whl"


def test_find_wheel_asset_rejects_plain_http_download_url():
    with pytest.raises(RuntimeError, match="HTTPS"):
        find_wheel_asset({"assets": [{"name": "fivemanager-0.9.0-py3-none-any.whl", "browser_download_url": "http://example.test/fivemanager.whl"}]})


def test_normalise_version_handles_alpha_tag():
    assert normalise_version("v0.9.0-alpha") == (0, 9, 0)


def test_check_for_newer_release_detects_update():
    release = {"tag_name": "v0.9.1", "html_url": "https://example.test/release", "assets": [{"name": "fivemanager-0.9.1-py3-none-any.whl", "browser_download_url": "https://example.test/fivemanager.whl"}]}
    update = check_for_newer_release("0.9.0", release)
    assert update is not None
    assert update.latest_version == "v0.9.1"


def test_check_for_newer_release_returns_none_when_current():
    release = {"tag_name": "v0.9.0", "assets": [{"name": "fivemanager-0.9.0-py3-none-any.whl", "browser_download_url": "https://example.test/fivemanager.whl"}]}
    assert check_for_newer_release("0.9.0", release) is None


def test_github_update_api_uses_renamed_repo_casing():
    assert GITHUB_LATEST_RELEASE_API == "https://api.github.com/repos/Next-Level-Studios/FiveManager/releases/latest"


def test_release_url_fallback_uses_renamed_repo_casing():
    release = {"tag_name": "v0.9.1", "assets": [{"name": "fivemanager-0.9.1-py3-none-any.whl", "browser_download_url": "https://example.test/fivemanager.whl"}]}
    update = check_for_newer_release("0.9.0", release)
    assert update is not None
    assert update.release_url == "https://github.com/Next-Level-Studios/FiveManager/releases/latest"
