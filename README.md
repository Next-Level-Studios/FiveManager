# updatefivem

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
- Stores config system-wide at:
  `/etc/updatefivem/config.json`
- Can install a systemd service that launches FiveM inside tmux.
- Lets you attach to the live server console with:
  `updatefivem console`

---

## Current commands

```bash
updatefivem                         # Download and install selected artifact
updatefivem --check                 # Show selected artifact without installing
updatefivem --artifact <build|url>  # Install a specific build or artifact URL
updatefivem --server-dir /path      # Override/save server directory
updatefivem --config /path.cfg      # Override/save config path passed to +exec
updatefivem --config-dir /path      # Directory containing the server cfg
updatefivem --config-file name.cfg  # Server cfg filename

updatefivem config                  # Interactive config setup/edit
updatefivem service install         # Install/update systemd unit
updatefivem service install --dry-run

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

Example using `v0.1.1`:

```bash
wget https://github.com/Next-Level-Studios/fivem-updater/releases/download/v0.1.1/updatefivem-0.1.1-py3-none-any.whl
```

Recommended system venv install:

```bash
sudo mkdir -p /opt/updatefivem
sudo python3 -m venv /opt/updatefivem/venv
sudo /opt/updatefivem/venv/bin/pip install ./updatefivem-0.1.1-py3-none-any.whl
sudo ln -sf /opt/updatefivem/venv/bin/updatefivem /usr/local/bin/updatefivem
```

Check it works:

```bash
updatefivem --help
updatefivem --check
```

---

## First-run configuration

Run:

```bash
sudo updatefivem config
```

It will ask for:

- FiveM server directory
- Server config directory
- Server config filename
- Service name
- Linux user to run FiveM as

The config is saved to:

```text
/etc/updatefivem/config.json
```

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
sudo updatefivem config \
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
sudo updatefivem config \
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
sudo updatefivem config \
  --server-dir /opt/fivem/server \
  --config /etc/fivem/configs/production.cfg
```

---

## Updating FiveM artifacts

Check what artifact will be installed:

```bash
updatefivem --check
```

Install/update artifacts:

```bash
sudo updatefivem
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
