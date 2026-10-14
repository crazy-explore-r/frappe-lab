# Workspace architecture

Frappe Lab turns a GitHub repository into a disposable Frappe environment. A launcher page links to a Codespace, a preset chooses the stack, and a bootstrap script builds it.

```
site/index.html  --(launch link)-->  Codespace  --(devcontainer for a preset)-->  Docker Compose
                                                                                    |-- workspace  (Bench, Frappe, apps)
                                                                                    |-- database   (MariaDB)
                                                                                    '-- redis-cache / redis-queue / redis-socketio
```

## Pieces

| Path | Role |
|---|---|
| `site/` | Static launcher page (GitHub Pages). Explains the steps and holds one Launch link per preset. |
| `config/presets/*.json` | One file per stack: Frappe branch and the apps to install, with repository, branch and optional `requires`. |
| `.devcontainer/<preset>/devcontainer.json` | One Dev Container per preset. It only selects the preset (`LAB_PRESET`) and sets ports, extensions and the minimum machine. |
| `.devcontainer/docker-compose.yml` | The shared services and the persistent database volume. |
| `.devcontainer/frappe-lab.env` | Site name and development-only credentials. |
| `scripts/lab_config.py` | Loads and validates a preset. Used by the bootstrap and by CI, so both apply the same rules. |
| `scripts/bootstrap.sh` | One-time and repeatable setup: waits for services, creates the bench, site and apps. |
| `scripts/run.sh` | Main process of the workspace container. Waits for the bootstrap to finish, then keeps `bench start` running. |
| `tests/` | Unit tests for the validator, the Dev Container and launcher links, and a bash check that every preset parses. |

## Adding or changing a stack

Add or edit a file in `config/presets/`, and add a matching folder under `.devcontainer/` with the same name whose `remoteEnv.LAB_PRESET` is that name. A test fails if a preset and a Dev Container do not match, or if the launcher has no link for a preset. Apps install in the order listed; use `requires` to make a missing or mis-ordered dependency fail before anything is installed.

Keep the Frappe branch and every installed app branch compatible. Only combinations that have been run are labelled "Tested" on the launcher page.

## Bootstrap behaviour

- The preset is validated first. An invalid preset stops the run before the bench or site is touched.
- An existing bench, site and installed apps are kept. A rerun finishes in seconds.
- If an earlier run stopped halfway through site creation, the script stops and prints the command to remove the half-made site. It does not delete data on its own.
- `frappe-bench/.lab-ready` is removed at the start and written at the end. `scripts/run.sh` starts the web server only when it exists.

## Container database client

The bench image ships a MariaDB 11.x client that requires TLS by default, and the Compose MariaDB 10.11 server offers none. The bootstrap writes `skip-ssl` to `~/.my.cnf`. Database traffic stays on the private Compose network.

## Security boundary

This is a public development template. The default passwords are visible to anyone who reads the source and are for disposable Codespaces only. Never use this configuration for production, confidential data or an internet-facing deployment.
