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
wget https://github.com/Next-Level-Studios/FiveManager/releases/download/v0.9.1-alpha/fivemanager-0.9.1-py3-none-any.whl
```

Recommended system venv install:

```bash
sudo mkdir -p /opt/fivemanager
sudo python3 -m venv /opt/fivemanager/venv
sudo /opt/fivemanager/venv/bin/pip install ./fivemanager-0.9.1-py3-none-any.whl
sudo ln -sf /opt/fivemanager/venv/bin/fivemanager /usr/local/bin/fivemanager
sudo ln -sf /opt/fivemanager/venv/bin/updatefivem /usr/local/bin/updatefivem
```

Requirements:

```bash
sudo apt install -y python3 python3-venv tmux
```

Check the install:

```bash
fivemanager --help
updatefivem --help
```

The `updatefivem` command is currently only a compatibility alias. New docs, scripts, and muscle memory should use `fivemanager`.

---

## Upgrading from updateFivem to FiveManager

FiveManager is not a tiny patch over the old updater. It is the 0.9 rewrite: new name, new config location, optional tmux multi-server management, and a cleaner runtime backup/update flow. In other words, the old tool grew up, changed its name, and now expects less chaos. Allegedly.

### What changed

| Old updateFivem | New FiveManager |
| --- | --- |
| Command: `updatefivem` | Primary command: `fivemanager` |
| Config: `~/.config/updatefivem/config.json` | Config: `~/.config/fivemanager/config.json` |
| Runtime updater focus | Runtime updater plus optional full server manager |
| Older service/systemd direction | 0.9 uses tmux sessions directly for managed servers |
| Old repository name: `fivem-updater` | New repository: `Next-Level-Studios/FiveManager` |

The old `updatefivem` command is still installed as a temporary alias so existing fingers/scripts do not immediately explode. It prints a rename notice and runs the same CLI app.

### Before upgrading

1. Stop any FiveM servers that use the runtime you are about to manage or update.
2. Back up your old updater config if it exists:

```bash
cp -a ~/.config/updatefivem ~/.config/updatefivem.backup.$(date +%Y%m%d-%H%M%S)
```

3. Make a note of your current paths:

```bash
realpath /path/to/your/fivem/runtime
realpath /path/to/your/server.cfg
```

FiveManager does not automatically migrate the old config in 0.9. That is deliberate: the new model asks clearer questions and avoids dragging old assumptions into the new setup like a haunted suitcase.

### Upgrade install

Install FiveManager into its own system venv:

```bash
wget https://github.com/Next-Level-Studios/FiveManager/releases/download/v0.9.1-alpha/fivemanager-0.9.1-py3-none-any.whl

sudo mkdir -p /opt/fivemanager
sudo python3 -m venv /opt/fivemanager/venv
sudo /opt/fivemanager/venv/bin/pip install --upgrade ./fivemanager-0.9.1-py3-none-any.whl
sudo ln -sf /opt/fivemanager/venv/bin/fivemanager /usr/local/bin/fivemanager
sudo ln -sf /opt/fivemanager/venv/bin/updatefivem /usr/local/bin/updatefivem
```

Then run the new setup wizard:

```bash
fivemanager setup
```

Choose one of the two modes:

- **Runtime updater only** if you only want backup/update/restore for the shared FiveM runtime.
- **Full server manager** if you want FiveManager to start, stop, restart, list, and attach to servers through tmux.

### Moving existing habits/scripts over

Replace direct script calls gradually:

```bash
# old
updatefivem

# new
fivemanager
```

For explicit runtime updates:

```bash
fivemanager update-runtime
```

For full manager mode:

```bash
fivemanager status
fivemanager start 1
fivemanager console 1
```

If you have cron jobs or shell scripts calling `updatefivem`, leave them alone until you have tested FiveManager manually. The alias exists to buy you time, not to be a permanent monument to old naming choices.

### What to keep from the old setup

Keep:

- your FiveM runtime directory
- your server data/resources directories
- your `server.cfg` files
- your old `~/.config/updatefivem/` backup until you are happy

Do not copy the old config directly into `~/.config/fivemanager/config.json`. Run `fivemanager setup` and answer the prompts instead.

### After upgrading

Verify:

```bash
fivemanager --help
fivemanager status
```

If you chose runtime-only mode, run an update only after stopping anything using the runtime:

```bash
fivemanager update-runtime
```

If you chose full manager mode, start one configured server and attach to its console:

```bash
fivemanager start 1
fivemanager console 1
```

Detach from tmux with:

```text
Ctrl+B, then D
```

---

## Updating FiveManager

For this 0.9 alpha, the safest update path is to download the wheel from the release page and install it into the existing venv:

```bash
wget https://github.com/Next-Level-Studios/FiveManager/releases/download/v0.9.1-alpha/fivemanager-0.9.1-py3-none-any.whl
sudo /opt/fivemanager/venv/bin/pip install --upgrade ./fivemanager-0.9.1-py3-none-any.whl
```

There is also a CLI helper:

```bash
fivemanager self-update
```

Important alpha note: GitHub's “latest release” API ignores prereleases. Because `v0.9.1-alpha` is a prerelease, `self-update` may not see it until a non-prerelease build is published or FiveManager gets an explicit prerelease update channel.

---

## Uninstall

This removes the FiveManager install but leaves your FiveM runtime, server data/resources, and config backups alone.

```bash
sudo rm -f /usr/local/bin/fivemanager /usr/local/bin/updatefivem
sudo rm -rf /opt/fivemanager
```

Optional: remove FiveManager config/cache after you are sure you do not need them:

```bash
rm -rf ~/.config/fivemanager ~/.cache/fivemanager
```

Optional: remove old updateFivem config only after you are completely done with it:

```bash
rm -rf ~/.config/updatefivem
```

Do **not** delete your FiveM runtime directory, server resources, or `server.cfg` files as part of uninstalling FiveManager unless you explicitly mean to delete your actual server. Obvious, but so is “do not put diesel in a petrol car”, and yet here we are.

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

FiveManager generates each server’s txAdmin config from an embedded default template. If you need to override that template, create:

```text
~/.config/fivemanager/txadmin-template.json
```

The template shape is:

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
