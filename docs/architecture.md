# Workspace architecture

Frappe Lab separates the editor, Frappe Bench, and supporting services so the environment can be reproduced and customized without hand-editing setup commands.

## Components

- **VS Code / Codespaces** — opens the repository root and exposes the development ports.
- **Workspace container** — runs Bench commands and the Frappe development processes.
- **MariaDB** — stores site data in a named Docker volume.
- **Redis services** — isolate cache, queue, and Socket.IO workloads.
- **Bootstrap script** — waits for dependent services, initializes Bench only when needed, creates the site, and installs apps from the app manifest.

## Configuration

- `.devcontainer/frappe-lab.env` configures the Frappe branch, site name, and demo-only credentials.
- `config/apps.json` specifies which app repositories and branches to install. Enabled apps are processed in manifest order so dependencies can be listed first.
- `.devcontainer/devcontainer.json` configures the editor and forwarded ports.
- `.devcontainer/docker-compose.yml` defines the containers and persistent database volume.

Keep the Frappe branch and every installed app branch compatible. The current defaults target the version-15 line; other combinations should be tested before being documented as supported.

## Lifecycle

The post-create command runs `scripts/bootstrap.sh`. It is designed to skip an already initialized bench, preserve an existing site, and continue configuring or installing missing apps. Once bootstrap has finished, run `bench start` from the `frappe-bench` directory to start the development processes.

## Security boundary

This repository is a public development template. The default passwords are visible to anyone who reads the source and are intended only for disposable local/Codespaces use. Never use this configuration for production, confidential data, or an internet-facing deployment.
