# FiveManager 0.9.0 Rewrite Implementation Plan

> For Hermes: Use TDD and focused subagents where useful. This is a major rewrite from updatefivem to FiveManager.

Goal: rename to FiveManager/fivemanager and support runtime-updater-only plus tmux-based full multi-server management.

Architecture: keep artifact download/extraction core, replace systemd-centric service management with on-demand tmux lifecycle. Store clean config at ~/.config/fivemanager/config.json and warn about old updatefivem config without migrating. Backups are runtime-level folders under runtime/backup/.

Key tasks:
1. Rename package metadata and CLI scripts to fivemanager, keep updatefivem alias.
2. Add config model helpers for runtime mode, manager mode, stable server IDs, slug keys, port defaults/conflict checks.
3. Add txAdmin config generation from an embedded default template, with optional user override at ~/.config/fivemanager/txadmin-template.json.
4. Add backup/restore with max 3 backups.
5. Add tmux lifecycle and status memory helpers.
6. Add wizard using InquirerPy with graceful fallback prompts.
7. Add tests for config, backup, txadmin, tmux commands, status, remove, restore.
8. Update README and verify build.
