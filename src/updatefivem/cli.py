from __future__ import annotations

import os
import subprocess
from pathlib import Path

import typer
from rich.prompt import Confirm, Prompt

from .artifacts import ARTIFACT_PAGE_URL, download_artifact, fetch_artifact_page, parse_artifacts, resolve_artifact
from .config import default_run_user, load_config, merge_config, resolve_server_cfg, save_config, validate_config
from .installer import install_archive
from .paths import cache_dir
from .service import install_service, service_is_active, service_unit_exists, systemctl_args, tmux_session_exists, validate_service_name
from .ui import console, error, info, success, warn
from .updater import run_self_update

app = typer.Typer(help="Update FiveM artifacts and manage the FiveM service.", no_args_is_help=False)
service_app = typer.Typer(help="Install or inspect the tmux-backed systemd service.")
app.add_typer(service_app, name="service")


def _interactive_config(
    existing: dict | None = None,
    *,
    server_dir: str | None = None,
    server_cfg: str | None = None,
    server_cfg_dir: str | None = None,
    server_cfg_file: str | None = None,
) -> dict:
    config = merge_config(
        existing,
        server_dir=server_dir,
        server_cfg=server_cfg,
        server_cfg_dir=server_cfg_dir,
        server_cfg_file=server_cfg_file,
    )
    if not config.get("server_dir"):
        config["server_dir"] = Prompt.ask("FiveM artifact/server directory (where run.sh and alpine/ are installed)")
    if server_cfg is None and server_cfg_dir is None and server_cfg_file is None:
        current_cfg = Path(config.get("server_cfg") or "server.cfg")
        default_cfg_dir = str(current_cfg.parent) if str(current_cfg.parent) != "." else "."
        default_cfg_file = current_cfg.name or "server.cfg"
        console.print(
            "[dim]Your server config can live anywhere. Use '.' only if the cfg is directly in the FiveM server directory.[/]"
        )
        config["server_cfg_dir"] = Prompt.ask(
            "Directory containing your server cfg (absolute path, or relative to the FiveM server directory)",
            default=default_cfg_dir,
        )
        config["server_cfg_file"] = Prompt.ask("Server config filename, e.g. server.cfg or server.dev.cfg", default=default_cfg_file)
        config = merge_config(config)
    config["service_name"] = Prompt.ask("Service name", default=config.get("service_name", "fivem"))
    config["run_user"] = Prompt.ask("Linux user to run FiveM as", default=config.get("run_user") or default_run_user())
    config["console_mode"] = "tmux"

    cfg_path = resolve_server_cfg(config)
    info(f"Resolved server cfg path: {cfg_path}")
    if not cfg_path.exists():
        warn(f"Config file not found yet: {cfg_path}")
        if not Confirm.ask("Save anyway?", default=True):
            raise typer.Exit(1)

    errors = validate_config(config)
    if errors:
        for msg in errors:
            error(msg)
        raise typer.Exit(1)
    save_config(config)
    success("Config saved")
    return config


def _load_or_create_config(
    server_dir: str | None = None,
    server_cfg: str | None = None,
    server_cfg_dir: str | None = None,
    server_cfg_file: str | None = None,
) -> dict:
    existing = load_config()
    if existing is None:
        info("No config found. First-run setup time.")
        return _interactive_config(
            existing,
            server_dir=server_dir,
            server_cfg=server_cfg,
            server_cfg_dir=server_cfg_dir,
            server_cfg_file=server_cfg_file,
        )
    config = merge_config(
        existing,
        server_dir=server_dir,
        server_cfg=server_cfg,
        server_cfg_dir=server_cfg_dir,
        server_cfg_file=server_cfg_file,
    )
    if server_dir or server_cfg or server_cfg_dir or server_cfg_file:
        errors = validate_config(config)
        if errors:
            for msg in errors:
                error(msg)
            raise typer.Exit(1)
        save_config(config)
    return config


def _selected_artifact(artifact_value: str | None):
    html = fetch_artifact_page(ARTIFACT_PAGE_URL)
    artifacts = parse_artifacts(html, ARTIFACT_PAGE_URL)
    return resolve_artifact(artifact_value, artifacts)


def _run_service_action(action: str, service_name: str) -> None:
    args = systemctl_args(action, service_name)
    subprocess.run(args, check=True)


def _service_is_active(service_name: str) -> bool:
    return service_is_active(service_name)


def _service_unit_exists(service_name: str) -> bool:
    return service_unit_exists(service_name)


def _prepare_service_for_update(config: dict, *, assume_yes: bool, service_control: bool) -> bool:
    if not service_control:
        return False
    service_name = config.get("service_name", "fivem")
    if not _service_is_active(service_name):
        info(f"FiveM service '{service_name}' is not running; skipping stop prompt.")
        return False
    if not assume_yes:
        ready = Confirm.ask(
            f"Ready to stop the FiveM service '{service_name}' before updating?",
            default=False,
        )
        if not ready:
            warn("Update cancelled before stopping the server.")
            raise typer.Exit(1)
    info(f"Stopping FiveM service: {service_name}")
    _run_service_action("stop", service_name)
    return True


def _offer_start_after_update(config: dict, *, assume_yes: bool, service_control: bool, run_after_update: bool) -> None:
    if not service_control:
        return
    service_name = config.get("service_name", "fivem")
    if not _service_unit_exists(service_name):
        console.print(f"No systemd service named '{service_name}' is installed yet.")
        console.print("Install the tmux-backed service with: sudo updatefivem service install")
        console.print(f"Then start it with: updatefivem start")
        return
    should_start = run_after_update or assume_yes or Confirm.ask(
        f"Update complete. Would you like to start the FiveM service '{service_name}' now?",
        default=True,
    )
    if should_start:
        info(f"Starting FiveM service: {service_name}")
        _run_service_action("start", service_name)
    else:
        console.print("Start it later with: updatefivem start")
        console.print(f"Or directly with: sudo systemctl start {service_name}")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    check: bool = typer.Option(False, "--check", help="Show selected artifact without installing."),
    server_dir: str | None = typer.Option(None, "--server-dir", help="Override and save FiveM server directory."),
    server_cfg: str | None = typer.Option(None, "--config", help="Override and save config path passed to +exec. Can be relative or absolute."),
    server_cfg_dir: str | None = typer.Option(None, "--config-dir", help="Directory containing the server config. Can be relative to server dir or absolute."),
    server_cfg_file: str | None = typer.Option(None, "--config-file", help="Server config filename, e.g. production.cfg."),
    artifact: str | None = typer.Option(None, "--artifact", help="Explicit artifact build or .tar.xz URL."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Assume yes for stop/start prompts during update."),
    run_after_update: bool = typer.Option(False, "--run", help="Start the configured FiveM service after updating."),
    service_control: bool = typer.Option(True, "--service-control/--no-service-control", help="Stop the configured service before updating and offer to start it afterwards."),
):
    if ctx.invoked_subcommand is not None:
        return
    try:
        selected = _selected_artifact(artifact)
        if check:
            console.print("[bold]Selected FiveM artifact:[/]")
            console.print(f"  Build: {selected.build}")
            console.print(f"  URL:   {selected.url}")
            return
        config = _load_or_create_config(server_dir, server_cfg, server_cfg_dir, server_cfg_file)
        _prepare_service_for_update(config, assume_yes=yes, service_control=service_control)
        archive = download_artifact(selected, cache_dir())
        install_archive(archive, cache_dir(), Path(config["server_dir"]))
        success(f"Installed FiveM artifact {selected.build} into {config['server_dir']}")
        _offer_start_after_update(
            config,
            assume_yes=yes,
            service_control=service_control,
            run_after_update=run_after_update,
        )
        console.print(f"Console: updatefivem console  [dim](detach: Ctrl+B, then D)[/]")
    except Exception as exc:
        error(str(exc))
        raise typer.Exit(1) from exc


@app.command("config")
def configure(
    server_dir: str | None = typer.Option(None, "--server-dir"),
    server_cfg: str | None = typer.Option(None, "--config", help="Config path passed to +exec. Can be relative or absolute."),
    server_cfg_dir: str | None = typer.Option(None, "--config-dir", help="Directory containing the server config."),
    server_cfg_file: str | None = typer.Option(None, "--config-file", help="Server config filename."),
):
    _interactive_config(
        load_config(),
        server_dir=server_dir,
        server_cfg=server_cfg,
        server_cfg_dir=server_cfg_dir,
        server_cfg_file=server_cfg_file,
    )


def _self_update(dry_run: bool) -> None:
    try:
        tag, name, url, cmd = run_self_update(dry_run=dry_run)
        info(f"Latest updatefivem release: {tag}")
        info(f"Wheel: {name}")
        if dry_run:
            console.print("Command that would run:")
            console.print(" ".join(cmd))
            return
        success(f"Updated updatefivem from {url}")
    except Exception as exc:
        error(str(exc))
        raise typer.Exit(1) from exc


@app.command("self-update")
def self_update(dry_run: bool = typer.Option(False, "--dry-run", help="Show the pip upgrade command without running it.")):
    """Update this updatefivem CLI from the latest GitHub release."""
    _self_update(dry_run=dry_run)


@app.command("update-cli")
def update_cli(dry_run: bool = typer.Option(False, "--dry-run", help="Show the pip upgrade command without running it.")):
    """Alias for self-update."""
    _self_update(dry_run=dry_run)


@service_app.command("install")
def service_install(dry_run: bool = typer.Option(False, "--dry-run", help="Print unit without writing.")):
    config = _load_or_create_config()
    try:
        unit = install_service(config, dry_run=dry_run)
        if dry_run:
            typer.echo(unit)
            return
        service_name = config["service_name"]
        success(f"Installed /etc/systemd/system/{service_name}.service")
        console.print(f"Start server: sudo systemctl start {service_name}")
        console.print(f"Enable on boot: sudo systemctl enable {service_name}")
        console.print("Open console: updatefivem console")
        console.print("Detach without stopping server: press Ctrl+B, then D")
    except Exception as exc:
        error(str(exc))
        raise typer.Exit(1) from exc


def _run_systemctl(action: str):
    config = _load_or_create_config()
    service_name = config["service_name"]
    try:
        args = systemctl_args(action, service_name)
        subprocess.run(args, check=False)
    except Exception as exc:
        error(str(exc))
        raise typer.Exit(1) from exc


@app.command()
def start():
    _run_systemctl("start")


@app.command()
def stop():
    _run_systemctl("stop")


@app.command()
def restart():
    _run_systemctl("restart")


@app.command()
def status():
    _run_systemctl("status")


@app.command()
def logs():
    config = _load_or_create_config()
    subprocess.run(["journalctl", "-u", config["service_name"], "-f"], check=False)


@app.command("console")
def console_command():
    """Attach to the live tmux console."""
    config = _load_or_create_config()
    service_name = config["service_name"]
    try:
        validate_service_name(service_name)
        if not tmux_session_exists(service_name):
            error(f"No tmux session named '{service_name}' was found.")
            console.print(f"Start the server first: sudo systemctl start {service_name}")
            raise typer.Exit(1)
        console.print(f"Attaching to FiveM console: [bold]{service_name}[/]")
        console.print("Detach without stopping the server: press [bold]Ctrl+B[/], then [bold]D[/]")
        os.execvp("tmux", ["tmux", "attach-session", "-t", service_name])
    except typer.Exit:
        raise
    except Exception as exc:
        error(str(exc))
        raise typer.Exit(1) from exc

