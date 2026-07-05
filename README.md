# UpdateFivem

> A polished terminal updater for FiveM Linux server artifacts, with system-wide config and a tmux-backed systemd service.

`updatefivem` downloads the correct FiveM Linux artifact, installs it into your server directory, and can manage your server as a proper service while still letting you attach to the live console through tmux.

Created by AI, assisted by Next Level Studio.

---

## What it does

- Finds the latest active/recommended FiveM Linux artifact from:
  `https://runtime.fivem.net/artifacts/fivem/build_proot_linux/master/`
- Ignores the top `LATEST RECOMMENDED` button when it is not the artifact you actually want.
- Selects the first active/blue artifact entry in the artifact list.
- Downloads the `.tar.xz` artifact with a nice terminal progress bar.
- Extracts the artifact safely, with path traversal protection.
- Verifies the archive contains:
  - `alpine/`
  - `run.sh`
- Overwrites only:
  - `<server-dir>/alpine/`
  - `<server-dir>/run.sh`
- Leaves your `server.cfg`, resources, database files, and other server content alone.
- Stores config in the user's XDG config directory by default:
  `~/.config/updatefivem/config.json`
- Downloads artifacts to the user's XDG cache directory by default:
  `~/.cache/updatefivem/`
- Can install a systemd service that launches FiveM inside tmux.
- Lets you attach to the live server console with:
  `updatefivem console`

---

## Current commands

```bash
updatefivem                         # Download and install selected artifact
updatefivem --check                 # Show selected artifact without installing
updatefivem --artifact <build|url>  # Install a specific build or artifact URL
updatefivem --no-update-check       # Skip checking for newer updatefivem releases
updatefivem --server-dir /path      # Override/save server directory
updatefivem --config /path.cfg      # Override/save config path passed to +exec
updatefivem --config-dir /path      # Directory containing the server cfg
updatefivem --config-file name.cfg  # Server cfg filename
updatefivem --yes                   # Assume yes for stop/start prompts
updatefivem --run                   # Start the configured service after updating
updatefivem --no-service-control    # Update files without stopping/starting service

updatefivem config                  # Interactive config setup/edit
updatefivem service install         # Install/update systemd unit
updatefivem service install --dry-run

updatefivem self-update             # Upgrade this CLI from the latest GitHub release
updatefivem update-cli              # Alias for self-update

updatefivem start
updatefivem stop
updatefivem restart
updatefivem status
updatefivem logs
updatefivem console
```

---

## Requirements

On the FiveM server:

- Linux
- Python 3.10+
- `python3-venv`
- `tmux`
- `systemd` if you want service management

Install base packages on Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y python3 python3-venv tmux
```

---

## Install from GitHub release

Download the latest wheel from the releases page:

https://github.com/Next-Level-Studios/fivem-updater/releases

Example using `v0.1.11`:

```bash
wget https://github.com/Next-Level-Studios/fivem-updater/releases/download/v0.1.11/updatefivem-0.1.11-py3-none-any.whl
```

Recommended system venv install:

```bash
sudo mkdir -p /opt/updatefivem
sudo python3 -m venv /opt/updatefivem/venv
sudo /opt/updatefivem/venv/bin/pip install ./updatefivem-0.1.11-py3-none-any.whl
sudo ln -sf /opt/updatefivem/venv/bin/updatefivem /usr/local/bin/updatefivem
```

Check it works:

```bash
updatefivem --help
updatefivem --check
```

---

## First-run configuration

Run as the user that will normally update the server:

```bash
updatefivem config
```

It will ask for:

- FiveM artifact/server directory — the directory where `run.sh` and `alpine/` are installed
- Server config directory
- Server config filename
- Service name
- Linux user to run FiveM as

Important: the server config directory does **not** have to be the same as the FiveM artifact/server directory. Use an absolute path if your `server.cfg` lives elsewhere.

The config is saved to your user config path by default:

```text
~/.config/updatefivem/config.json
```

The artifact download cache uses:

```text
~/.cache/updatefivem/
```

Both paths respect `XDG_CONFIG_HOME` and `XDG_CACHE_HOME`. You can override them explicitly with `UPDATEFIVEM_CONFIG_PATH` and `UPDATEFIVEM_CACHE_DIR`.

---

## Config path examples

### Config inside the FiveM server directory

If your server looks like this:

```text
/opt/fivem/server/
├── run.sh
├── alpine/
├── resources/
└── configs/live/production.cfg
```

Use:

```bash
updatefivem config \
  --server-dir /opt/fivem/server \
  --config-dir configs/live \
  --config-file production.cfg
```

The service will run:

```bash
./run.sh +exec configs/live/production.cfg
```

### Config outside the FiveM server directory

If your config lives somewhere else:

```text
/etc/fivem/configs/production.cfg
```

Use:

```bash
updatefivem config \
  --server-dir /opt/fivem/server \
  --config-dir /etc/fivem/configs \
  --config-file production.cfg
```

The service will run:

```bash
./run.sh +exec /etc/fivem/configs/production.cfg
```

### One-shot config path

You can also provide the config path directly:

```bash
updatefivem config \
  --server-dir /opt/fivem/server \
  --config /etc/fivem/configs/production.cfg
```

---

## Updating FiveM artifacts

Check what artifact will be installed:

```bash
updatefivem --check
```

By default, `updatefivem` also checks GitHub for a newer CLI release before running. If one exists, it prints the release and the `updatefivem self-update` command. Skip that advisory check with:

```bash
updatefivem --no-update-check
```

Install/update artifacts:

```bash
updatefivem
```

You should only need `sudo` here if your FiveM server directory is owned by root or another user and your current user cannot replace `alpine/` and `run.sh`.

By default, before replacing `alpine/` and `run.sh`, `updatefivem` checks whether the configured FiveM service is currently running. If it is running, it asks you to confirm that the service can be stopped. If it is already stopped, it skips the stop prompt and simply updates the files. After the update completes, it asks whether to start the service.

For unattended use:

```bash
updatefivem --yes
```

To start the server automatically after updating:

```bash
updatefivem --run
```

If the tmux-backed systemd service has not been installed yet, `updatefivem` will not try to start a missing unit. Install it first:

```bash
sudo updatefivem service install
```

If you decline the start prompt, `updatefivem` prints the command you can run later:

```bash
updatefivem start
```

If you want the old file-only behavior and will manage the running server yourself:

```bash
updatefivem --no-service-control
```

This overwrites:

```text
<server-dir>/alpine/
<server-dir>/run.sh
```

It does not intentionally touch:

```text
<server-dir>/server.cfg
<server-dir>/resources/
<server-dir>/cache/
<server-dir>/txData/
```

Still, this is a server updater. Backups are not cowardice; they are how adults avoid Discord panic.

---

## Updating updatefivem itself

Once `updatefivem` is installed, you can upgrade the CLI from the latest GitHub release with:

```bash
sudo updatefivem self-update
```

or:

```bash
sudo updatefivem update-cli
```

Preview the pip command without running it:

```bash
updatefivem self-update --dry-run
```

---

## Installing the systemd service

Preview the generated unit first:

```bash
sudo updatefivem service install --dry-run
```

Install it:

```bash
sudo updatefivem service install
```

Start and enable on boot:

```bash
sudo systemctl enable --now fivem
```

If you chose a different service name, replace `fivem` with that name.

---

## Console access

Attach to the live tmux console:

```bash
updatefivem console
```

Detach without stopping the server:

```text
Ctrl+B, then D
```

That is tmux's normal detach sequence. Pressing `Ctrl+C` in the console may stop the server, so don't fat-finger that unless you mean it.

---

## Service helpers

```bash
updatefivem start
updatefivem stop
updatefivem restart
updatefivem status
updatefivem logs
updatefivem console
```

Under the hood these call `systemctl`, `journalctl`, and `tmux` for the configured service.

---

## Development

Clone and set up:

```bash
git clone https://github.com/Next-Level-Studios/fivem-updater.git
cd fivem-updater
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest -q
updatefivem --help
```

Build a wheel:

```bash
python -m pip wheel . --no-deps -w dist
```

---

## Test status

Current local test suite at time of release:

```text
24 passed
```

The generated systemd unit has also been checked with:

```bash
systemd-analyze verify
```

---

## Credits

Created by AI, assisted by Next Level Studio.

This project was generated and iterated with AI assistance for Next Level Studio.
No third-party project source code was copied into this repository.

The project uses these open-source Python libraries:

- Typer — CLI framework
- Rich — terminal formatting and progress UI
- Requests — HTTP client
- Beautiful Soup — HTML parsing
- pytest — test runner

It also integrates with standard Linux tools:

- systemd
- tmux
- journalctl

FiveM artifacts are provided by the FiveM/Cfx.re runtime artifact service. This project is not affiliated with or endorsed by FiveM, Cfx.re, or Rockstar Games.

---

## License

No license file has been added yet. Until one is added, all rights are reserved by the repository owner.
