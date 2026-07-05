# FiveManager

> FiveManager is a terminal-first FiveM runtime updater and tmux-based multi-server manager.

Created by AI, assisted by Next Level Studio.

FiveManager replaces the old `updatefivem` direction with a cleaner 0.9 rewrite aimed at a future stable `1.0.0`.

The actual command is lowercase:

```bash
fivemanager
```

The old command remains as a temporary alias:

```bash
updatefivem
```

It prints a rename notice and runs the same app.

---

## Modes

FiveManager has two setup modes.

### Runtime updater only

Use this if you only want to update the shared FXServer/FiveM runtime directory.

The runtime directory is the folder containing:

```text
run.sh
alpine/
txData/
```

In this mode, running:

```bash
fivemanager
```

or:

```bash
fivemanager update-runtime
```

backs up the runtime and updates it.

FiveManager does not check whether servers are running in runtime-only mode. If you use this mode, you are responsible for stopping anything that uses the runtime before updating. Congratulations, you are now the safety interlock.

### Full server manager

Use this if you want FiveManager to manage one or more FiveM servers from one shared runtime.

Each server gets:

```text
<runtime>/txData/<server-key>/default/config.json
<runtime>/txData/<server-key>/default/data/
<runtime>/txData/<server-key>/default/logs/
```

Servers are started in named tmux sessions, not systemd services.

FiveManager works on command. It does not run constantly in the background.

---

## Install

Download a release wheel from GitHub.

For the 0.9 rewrite:

```bash
wget https://github.com/Next-Level-Studios/fivemanager/releases/download/v0.9.0-alpha/fivemanager-0.9.0-py3-none-any.whl
```

Recommended system venv install:

```bash
sudo mkdir -p /opt/fivemanager
sudo python3 -m venv /opt/fivemanager/venv
sudo /opt/fivemanager/venv/bin/pip install ./fivemanager-0.9.0-py3-none-any.whl
sudo ln -sf /opt/fivemanager/venv/bin/fivemanager /usr/local/bin/fivemanager
sudo ln -sf /opt/fivemanager/venv/bin/updatefivem /usr/local/bin/updatefivem
```

Requirements:

```bash
sudo apt install -y python3 python3-venv tmux
```

---

## First run

Run:

```bash
fivemanager
```

If no config exists, FiveManager launches the interactive setup wizard.

It asks:

```text
Do you want the full FiveM server manager experience, or just the runtime updater?
```

Config is stored at:

```text
~/.config/fivemanager/config.json
```

Cache is stored at:

```text
~/.cache/fivemanager/
```

If an old config exists at:

```text
~/.config/updatefivem/config.json
```

FiveManager tells you where it is, but does not migrate it. Clean start, fewer haunted assumptions.

---

## Runtime update and backups

Before updating the runtime, FiveManager creates a backup in:

```text
<runtime>/backup/<date>/
```

It backs up:

```text
alpine/
txData/
run.sh
```

Only the latest 3 backups are kept. Older backups are deleted automatically.

Run:

```bash
fivemanager update-runtime
```

In full manager mode, if managed servers are running, FiveManager offers:

- stop running managed servers and update
- update anyway
- cancel

---

## Restore

Run:

```bash
fivemanager restore
```

FiveManager lists available backups and lets you choose one or cancel.

Restore replaces the current:

```text
alpine/
txData/
run.sh
```

with the selected backup.

This is runtime-level restore. It restores all txData profiles, not just one server.

---

## Full manager server setup

For each server, FiveManager asks for:

- server name
- internal server key, suggested from the name
- server data path, where that server’s `resources/` folder lives
- server config path, full path to `server.cfg`
- txAdmin port
- FXServer port
- interface/bind address, default `0.0.0.0`

Default ports increment per server:

```text
Server 1: txAdmin 40120, FXServer 30120
Server 2: txAdmin 40121, FXServer 30121
Server 3: txAdmin 40122, FXServer 30122
```

FiveManager warns if another configured server already uses the same txAdmin or FXServer port.

Server IDs are stable. If server 2 is removed, servers 3 and 4 remain 3 and 4. A newly added server reuses the lowest free ID.

---

## txAdmin config generation

FiveManager generates each server’s txAdmin config from the template shape provided in `/home/neo/config.json`:

```json
{
  "version": 2,
  "general": {
    "serverName": "servername"
  },
  "server": {
    "dataPath": "/full/path/to/server/",
    "cfgPath": "/full/path/to/server/server.cfg"
  },
  "whitelist": {
    "mode": "approvedLicense",
    "rejectionMessage": "Set up your server in TXAdmin"
  },
  "gameFeatures": {
    "menuPageKey": "Backquote"
  }
}
```

At runtime, FiveManager starts each tmux session with:

```bash
TXHOST_DATA_PATH=<runtime>/txData/<server-key>
TXHOST_TXA_PORT=<txadmin-port>
TXHOST_FXS_PORT=<fxserver-port>
TXHOST_INTERFACE=<interface>
```

txAdmin then uses its default profile under that server-specific `TXHOST_DATA_PATH`. This avoids the deprecated `serverProfile` ConVar warning.

Then it runs:

```bash
<runtime>/run.sh +exec <server.cfg filename>
```

from the directory containing that server’s cfg. This makes lines like:

```cfg
exec resources.cfg
```

resolve beside `server.cfg`, which is what FiveM admins generally expect and computers somehow needed explaining.

---

## Commands

```bash
fivemanager                         # setup wizard, or runtime update in runtime-only mode
fivemanager setup                   # run setup wizard again
fivemanager update-runtime          # backup and update shared runtime
fivemanager restore                 # restore runtime backup

fivemanager status                  # list configured servers
fivemanager start 1                 # start server ID 1
fivemanager stop 1                  # stop server ID 1
fivemanager restart 1               # restart server ID 1
fivemanager console 1               # attach to server ID 1 tmux console
fivemanager remove 1                # remove server ID 1 from config

fivemanager self-update             # update FiveManager from latest release
```

Detach from console without stopping the server:

```text
Ctrl+B, then D
```

---

## Status output

```bash
fivemanager status
```

Shows:

```text
ID | Server name | Active status | Memory usage
```

Memory usage is best-effort current RSS from the tmux session process tree.

Peak memory is intentionally not shown in 0.9.0 because FiveManager does not run as a background monitor. We can add persisted peak tracking later when a daemon/web panel exists.

---

## Remove behaviour

```bash
fivemanager remove 1
```

This:

- asks for confirmation
- stops and kills the tmux session if it exists
- removes the server from FiveManager config
- asks whether to delete that server’s txData directory

It does not delete the server data/resources path. That would be reckless, and not the fun kind.

---

## Road to 1.0

Planned direction:

- multi-server polish
- config migration/import flow
- stronger validation and doctor command
- optional web panel
- optional autostart/systemd integration
- stable release as `1.0.0` after real server testing

---

## Credits

Created by AI, assisted by Next Level Studio.

No third-party project source code is copied into this repository.

Runtime dependencies:

- Typer
- Rich
- Requests
- Beautiful Soup
- InquirerPy

FiveM and txAdmin are third-party tools/projects. FiveManager is not affiliated with Cfx.re/FiveM.
