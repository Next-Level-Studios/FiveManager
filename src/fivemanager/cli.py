from __future__ import annotations

import shutil
import sys
from pathlib import Path

import typer
from rich.table import Table

from . import __version__
from .artifacts import download_artifact, selected_artifact
from .backup import create_backup, list_backups, restore_backup
from .config import get_server, load_config, remove_server as remove_server_config, require_config, runtime_dir, save_config, validate_runtime_dir
from .installer import install_archive
from .paths import cache_dir
from .tmux import attach_console, format_bytes, memory_bytes_for_session, restart_server, session_exists, session_name, start_server, stop_server
from .txadmin import write_txadmin_profile
from .ui import console, error, info, success, warn
from .updater import install_update, latest_newer_release
from .wizard import add_server_interactively, ask_confirm, ask_select, run_setup_wizard

app = typer.Typer(help="FiveManager — FiveM runtime updater and tmux-based server manager.", no_args_is_help=False)


def _alias_notice() -> None:
    if Path(sys.argv[0]).name == "updatefivem":
        warn("updatefivem has been renamed to fivemanager. This alias will remain during the transition.")


def _update_runtime(config: dict, *, force: bool = False, artifact: str | None = None) -> None:
    runtime = runtime_dir(config)
    if config.get("mode") == "manager" and not force:
        running = [s for s in config.get("servers", []) if session_exists(session_name(s))]
        if running:
            choice = ask_select(
                "Managed servers are running. What should FiveManager do before updating the runtime?",
                [
                    ("Stop running managed servers and update", "stop"),
                    ("Update without stopping managed servers (not recommended)", "anyway"),
                    ("Cancel", "cancel"),
                ],
            )
            if choice == "cancel":
                warn("Runtime update cancelled.")
                return
            if choice == "stop":
                for server in running:
                    stop_server(server)
    backup = create_backup(runtime)
    success(f"Created backup: {backup}")
    artifact_obj = selected_artifact(artifact)
    archive = download_artifact(artifact_obj, cache_dir())
    install_archive(archive, cache_dir(), runtime)
    success(f"Installed FiveM artifact {artifact_obj.build} into {runtime}")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    artifact: str | None = typer.Option(None, "--artifact", help="Explicit artifact build or .tar.xz URL for runtime update."),
):
    _alias_notice()
    if ctx.invoked_subcommand is not None:
        return
    config = load_config()
    if not config:
        run_setup_wizard(update_callback=lambda cfg, force=False: _update_runtime(cfg, force=force, artifact=artifact), start_callback=start_server_by_id)
        return
    if config.get("mode") == "runtime":
        _update_runtime(config, force=True, artifact=artifact)
        return
    console.print("[bold cyan]FiveManager[/] is configured in full manager mode.")
    console.print("Use [bold]fivemanager status[/] to view server IDs and running state. Then use [bold]fivemanager start <id>[/], [bold]fivemanager stop <id>[/], [bold]fivemanager console <id>[/], or [bold]fivemanager update-runtime[/].")


@app.command("setup")
def setup_command():
    """Run the interactive setup wizard again."""
    run_setup_wizard(update_callback=lambda cfg, force=False: _update_runtime(cfg, force=force), start_callback=start_server_by_id)


@app.command("update-runtime")
def update_runtime_command(artifact: str | None = typer.Option(None, "--artifact")):
    """Backup and update the shared FiveM runtime."""
    _update_runtime(require_config(), artifact=artifact)


@app.command("restore")
def restore_command():
    """Restore alpine/, txData/, and run.sh from a runtime backup."""
    config = require_config()
    runtime = runtime_dir(config)
    backups = list_backups(runtime)
    if not backups:
        warn("No backups found.")
        return
    choices = [(f"{idx}. {path.name}", str(idx)) for idx, path in enumerate(backups, 1)] + [("Cancel", "cancel")]
    choice = ask_select("Select a backup to restore", choices)
    if choice == "cancel":
        return
    selected = backups[int(choice) - 1]
    warn("This restore will replace the current alpine/, txData/, and run.sh in the runtime directory.")
    if not ask_confirm(f"Restore backup {selected.name}?", default=False):
        warn("Restore cancelled.")
        return
    restore_backup(runtime, selected)
    success(f"Restored backup: {selected}")


def start_server_by_id(config: dict, server_id: int) -> None:
    server = get_server(config, server_id)
    write_txadmin_profile(runtime_dir(config), server)
    name = start_server(runtime_dir(config), server)
    success(f"Started {server['name']} in tmux session {name}")


@app.command("add")
def add_command():
    """Add another managed server to an existing full manager configuration."""
    config = load_config()
    if not config:
        warn("FiveManager is not configured yet. Run fivemanager setup first.")
        raise typer.Exit(1)
    if config.get("mode") != "manager":
        warn("fivemanager add requires full manager mode. Run fivemanager setup to configure full server management.")
        raise typer.Exit(1)
    runtime = runtime_dir(config)
    info(f"Runtime directory: {runtime}")
    runtime_errors = validate_runtime_dir(runtime)
    if runtime_errors:
        for runtime_error in runtime_errors:
            warn(runtime_error)
        info("You can still save the server now. Run fivemanager update-runtime before starting it.")
    existing = sorted(config.get("servers", []), key=lambda s: int(s["id"]))
    if existing:
        info("Existing managed servers:")
        for server in existing:
            info(f"  {server['id']} | {server['name']} ({server['key']})")
    server = add_server_interactively(config, runtime)
    save_config(config)
    if ask_confirm("Start this server now?", default=False):
        start_server_by_id(config, int(server["id"]))
    else:
        info(f"Server saved. Start it later with: fivemanager start {server['id']}")


@app.command("start")
def start_command(server_id: int):
    start_server_by_id(require_config(), server_id)


@app.command("stop")
def stop_command(server_id: int):
    server = get_server(require_config(), server_id)
    stop_server(server)
    success(f"Stopped {server['name']}")


@app.command("restart")
def restart_command(server_id: int):
    config = require_config()
    server = get_server(config, server_id)
    write_txadmin_profile(runtime_dir(config), server)
    name = restart_server(runtime_dir(config), server)
    success(f"Restarted {server['name']} in tmux session {name}")


@app.command("console")
def console_command(server_id: int):
    server = get_server(require_config(), server_id)
    name = session_name(server)
    if not session_exists(name):
        warn(f"Server {server['name']} is not running. FiveManager could not find tmux session {name}.")
        info(f"Start the server first with: fivemanager start {server_id}")
        raise typer.Exit(0)
    console.print("Attach to the server console. To leave the console without stopping the server, press Ctrl+B, then D.")
    attach_console(server)


@app.command("status")
def status_command():
    config = require_config()
    table = Table(title="FiveManager servers")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Server name", style="bold")
    table.add_column("Active status")
    table.add_column("Memory usage", justify="right")
    for server in sorted(config.get("servers", []), key=lambda s: int(s["id"])):
        name = session_name(server)
        active = session_exists(name)
        table.add_row(str(server["id"]), server["name"], "[green]running[/]" if active else "[red]stopped[/]", format_bytes(memory_bytes_for_session(name)) if active else "-")
    console.print(table)


@app.command("remove")
def remove_command(server_id: int):
    config = require_config()
    server = get_server(config, server_id)
    warn(f"This will remove {server['name']} from FiveManager and stop its tmux session if it is running.")
    if not ask_confirm("Continue?", default=False):
        return
    stop_server(server)
    removed = remove_server_config(config, server_id)
    txdata = runtime_dir(config) / "txData" / removed["key"]
    if ask_confirm(f"Also delete this server's txAdmin data/profile folder? This does not delete server resources: {txdata}", default=False):
        if txdata.exists():
            shutil.rmtree(txdata)
            success(f"Deleted {txdata}")
    else:
        info(f"Server data path still exists: {removed['data_path']}")
        info(f"txData path still exists: {txdata}")
    save_config(config)
    success(f"Removed server {removed['name']}")


@app.command("self-update")
def self_update(
    dry_run: bool = typer.Option(False, "--dry-run"),
    prerelease: bool = typer.Option(False, "--prerelease", help="Include prerelease alpha/beta builds."),
):
    try:
        update = latest_newer_release(__version__, include_prereleases=prerelease)
        if update is None:
            channel = "release/prerelease" if prerelease else "stable release"
            raise RuntimeError(f"No newer {channel} found for FiveManager {__version__}.")
        cmd = install_update(update, dry_run=True)
    except RuntimeError as exc:
        warn(str(exc))
        if not prerelease:
            info("Use --prerelease to opt into alpha/beta builds, or install a specific release wheel manually.")
        raise typer.Exit(0)

    console.print("[bold cyan]FiveManager self-update[/]")
    info(f"Current version: {update.current_version}")
    info(f"Target release: {update.latest_version}")
    info(f"Wheel: {update.wheel_name}")
    if dry_run:
        console.print(" ".join(cmd))
        return

    try:
        with console.status("Installing update...", spinner="dots"):
            install_update(update)
    except RuntimeError as exc:
        warn(str(exc))
        raise typer.Exit(1)
    success(f"Updated FiveManager to {update.latest_version}")


def run():
    app()
