# Troubleshooting

Start with the creation log: in the Codespace, open the Command Palette and run **Codespaces: View Creation Log**. Lines starting with `[Frappe Lab]` are from `scripts/bootstrap.sh`.

## Setup is slow

The first start installs Frappe and its apps and builds assets. It took about 8 minutes on a 2-core machine for Frappe + ERPNext. Later starts, and reruns of `scripts/bootstrap.sh`, take seconds.

## The site does not open on port 8000

The web server starts after setup finishes. Check `docker`-level state from the Codespace terminal:

```
ls /workspace/frappe-bench/.lab-ready   # exists once setup has finished
```

If the file is missing, setup has not finished or failed: read the creation log, fix the cause and run `bash scripts/bootstrap.sh` again. If the file exists, wait a minute, then open the **Ports** tab and open the address for port 8000.

## "Preset ... is invalid" or "preset not found"

`LAB_PRESET` selects `config/presets/<name>.json`. The error says which field is wrong. Run `python3 scripts/lab_config.py check` to validate all presets.

## "Site ... is only partly created"

An earlier run stopped while creating the site. Run the `bench drop-site` command printed in the message (it removes only that site), then run `bash scripts/bootstrap.sh` again.

## Incompatible app branches

An app branch must match the Frappe branch (for example every `version-15`). If installing an app fails after downloading it, compare its branch with `frappe_branch` in the preset.

## Database connection or TLS errors

`TLS/SSL error: SSL is required, but the server does not support it` means the MariaDB client option is missing. The bootstrap adds `skip-ssl` to `~/.my.cnf`; check that the file contains it.

## Redis URL errors

`Redis URL must specify one of the following schemes` means a Redis host was set without `redis://`. The bootstrap sets `redis://redis-cache:6379` and the two matching queue and Socket.IO hosts.

## The Codespace stopped

Codespaces stop when idle and can be resumed from github.com/codespaces. Data is kept while the Codespace exists. The web server starts again by itself.
