import pytest

from updatefivem.artifacts import Artifact, parse_artifacts, resolve_artifact, select_blue_recommended

HTML = """
<html><body>
<a class="button is-info" href="/artifacts/fivem/build_proot_linux/master/9999/fx.tar.xz">LATEST RECOMMENDED</a>
<table>
<tr><td><span class="panel-icon" style="color: #999"></span></td><td><a href="1234/fx.tar.xz">1234</a></td></tr>
<tr><td><span class="panel-icon" style="color: #3273dc"></span></td><td><a href="2345/fx.tar.xz">2345</a></td></tr>
<tr><td><span class="panel-icon" style="color: rgb(50, 115, 220)"></span></td><td><a href="3456/fx.tar.xz">3456</a></td></tr>
</table>
</body></html>
"""

def test_parse_selects_first_blue_table_row_not_top_button():
    artifacts = parse_artifacts(HTML, "https://runtime.fivem.net/artifacts/fivem/build_proot_linux/master/")
    selected = select_blue_recommended(artifacts)

    assert selected.build == "2345"
    assert selected.url.endswith("/2345/fx.tar.xz")


def test_parse_accepts_rgb_blue():
    html = '<table><tr><td><span class="panel-icon" style="color: rgb(50, 115, 220)"></span></td><td><a href="7777/fx.tar.xz">fx</a></td></tr></table>'
    artifacts = parse_artifacts(html, "https://example.test/master/")

    assert select_blue_recommended(artifacts).build == "7777"


def test_parse_accepts_bulma_active_panel_block_as_computed_blue_icon():
    html = '''
    <div class="panel-block"><a href="./9999-hash/fx.tar.xz">LATEST RECOMMENDED</a></div>
    <a class="panel-block is-active" href="./31689-abc/fx.tar.xz" style="display: block;">
      <span class="panel-icon"><i class="fas fa-download"></i></span>
      31689
    </a>
    '''
    artifacts = parse_artifacts(html, "https://runtime.fivem.net/artifacts/fivem/build_proot_linux/master/")

    selected = select_blue_recommended(artifacts)
    assert selected.build == "31689"
    assert selected.url.endswith("/31689-abc/fx.tar.xz")


def test_select_blue_recommended_raises_when_missing():
    artifacts = [Artifact(build="1", url="https://example/fx.tar.xz", recommended=False, icon_color="#999")]

    with pytest.raises(RuntimeError, match="blue"):
        select_blue_recommended(artifacts)


def test_resolve_artifact_by_url():
    artifact = resolve_artifact("https://example.test/123/fx.tar.xz", [])
    assert artifact.build == "123"
    assert artifact.url == "https://example.test/123/fx.tar.xz"


def test_resolve_artifact_rejects_plain_http_url():
    with pytest.raises(RuntimeError, match="HTTPS"):
        resolve_artifact("http://example.test/123/fx.tar.xz", [])


def test_resolve_artifact_by_build():
    artifacts = [Artifact(build="2345", url="https://example/2345/fx.tar.xz", recommended=True, icon_color="#3273dc")]
    assert resolve_artifact("2345", artifacts) == artifacts[0]
