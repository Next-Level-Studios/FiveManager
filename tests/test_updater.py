import subprocess

import pytest

from fivemanager.updater import GITHUB_LATEST_RELEASE_API, UpdateInfo, check_for_newer_release, find_wheel_asset, install_update, latest_newer_release, normalise_version, run_self_update


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


def test_latest_newer_release_ignores_older_stable(monkeypatch):
    monkeypatch.setattr("fivemanager.updater.fetch_latest_release", lambda: {"tag_name": "v0.1.14", "assets": [{"name": "updatefivem-0.1.14-py3-none-any.whl", "browser_download_url": "https://example.test/old.whl"}]})
    assert latest_newer_release("0.9.3") is None


def test_latest_newer_release_can_include_prereleases(monkeypatch):
    monkeypatch.setattr("fivemanager.updater.fetch_releases", lambda: [
        {"tag_name": "v0.9.4-alpha", "draft": False, "assets": [{"name": "fivemanager-0.9.4-py3-none-any.whl", "browser_download_url": "https://example.test/new.whl"}]},
        {"tag_name": "v0.1.14", "draft": False, "assets": [{"name": "updatefivem-0.1.14-py3-none-any.whl", "browser_download_url": "https://example.test/old.whl"}]},
    ])
    update = latest_newer_release("0.9.3", include_prereleases=True)
    assert update is not None
    assert update.latest_version == "v0.9.4-alpha"


def test_run_self_update_refuses_when_no_newer_release(monkeypatch):
    monkeypatch.setattr("fivemanager.updater.latest_newer_release", lambda *args, **kwargs: None)
    with pytest.raises(RuntimeError, match="No newer"):
        run_self_update(dry_run=True)


def test_install_update_runs_pip_quietly_and_captures_output(monkeypatch):
    calls = []
    update = UpdateInfo("0.9.8", "v0.9.9-alpha", "https://example.test/release", "fivemanager-0.9.9-py3-none-any.whl", "https://example.test/fivemanager.whl")

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout="pip output", stderr="")

    monkeypatch.setattr("fivemanager.updater.subprocess.run", fake_run)

    cmd = install_update(update)

    assert "--quiet" in cmd
    assert "--disable-pip-version-check" in cmd
    assert calls == [(cmd, {"check": True, "capture_output": True, "text": True})]


def test_install_update_reports_captured_pip_output_on_failure(monkeypatch):
    update = UpdateInfo("0.9.8", "v0.9.9-alpha", "https://example.test/release", "fivemanager-0.9.9-py3-none-any.whl", "https://example.test/fivemanager.whl")

    def fake_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd, output="stdout details", stderr="stderr details")

    monkeypatch.setattr("fivemanager.updater.subprocess.run", fake_run)

    with pytest.raises(RuntimeError) as exc:
        install_update(update)

    message = str(exc.value)
    assert "pip install failed" in message
    assert "stdout details" in message
    assert "stderr details" in message
