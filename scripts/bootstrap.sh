#!/usr/bin/env bash
# Frappe Lab workspace initialization. Safe to re-run after a partial setup.
set -Eeuo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_DIR="$WORKSPACE_ROOT/frappe-bench"
READY_FILE="$BENCH_DIR/.lab-ready"

# The official development image installs Bench in the user's local bin directory.
export PATH="$HOME/.local/bin:$PATH"
if [[ -f "$HOME/.nvm/nvm.sh" ]]; then
  # shellcheck disable=SC1091
  source "$HOME/.nvm/nvm.sh"
fi

LAB_PRESET="${LAB_PRESET:-erpnext}"
BENCH_PYTHON="${BENCH_PYTHON:-python3.12}"
SITE_NAME="${SITE_NAME:-lab.localhost}"
MARIADB_ROOT_PASSWORD="${MARIADB_ROOT_PASSWORD:-frappe-lab-dev-only}"
SITE_ADMIN_PASSWORD="${SITE_ADMIN_PASSWORD:-frappe-lab-admin-only}"

log() {
  printf '\n[Frappe Lab] %s\n' "$*"
}

die() {
  printf '\n[Frappe Lab] ERROR: %s\n' "$*" >&2
  exit 1
}

wait_for_port() {
  local host="$1"
  local port="$2"
  local attempt
  log "Waiting for $host:$port..."
  for attempt in $(seq 1 60); do
    if (echo >"/dev/tcp/$host/$port") >/dev/null 2>&1; then
      log "$host:$port is ready."
      return 0
    fi
    sleep 2
  done
  die "Timed out waiting for $host:$port. Check Docker service status and creation logs."
}

command -v bench >/dev/null 2>&1 || die "Bench is not on PATH. Rebuild the Codespace container and try again."
command -v "$BENCH_PYTHON" >/dev/null 2>&1 || die "$BENCH_PYTHON not found. Set BENCH_PYTHON to an installed Python 3.10-3.14."
command -v python3 >/dev/null 2>&1 || die "Python 3 is required to read the preset."

# Validate the preset before making changes to the bench or site.
log "Using preset '$LAB_PRESET'."
PRESET_ROWS="$(python3 "$WORKSPACE_ROOT/scripts/lab_config.py" show "$LAB_PRESET")" \
  || die "Preset '$LAB_PRESET' is invalid. Fix config/presets/$LAB_PRESET.json (or set LAB_PRESET to another preset) and rerun scripts/bootstrap.sh."
mapfile -t PRESET_LINES <<< "$PRESET_ROWS"
IFS=$'\t' read -r _ FRAPPE_BRANCH <<< "${PRESET_LINES[0]}"
ENABLED_APPS=("${PRESET_LINES[@]:1}")

# Not ready until this run finishes; scripts/run.sh waits for the marker.
rm -f "$READY_FILE"

# The bench image ships a MariaDB 11.x client that requires TLS by default, but the
# Compose database does not offer it. Traffic stays on the private Compose network.
if ! grep -qs '^skip-ssl' "$HOME/.my.cnf"; then
  log "Configuring the MariaDB client for the container network (skip-ssl)..."
  printf '[client]\nskip-ssl\n' >> "$HOME/.my.cnf"
  chmod 600 "$HOME/.my.cnf"
fi

wait_for_port "database" 3306
wait_for_port "redis-cache" 6379
wait_for_port "redis-queue" 6379
wait_for_port "redis-socketio" 6379

cd "$WORKSPACE_ROOT"

if [[ ! -d "$BENCH_DIR/apps/frappe" ]]; then
  log "Creating a new bench on Frappe branch '$FRAPPE_BRANCH'..."
  bench init \
    --ignore-exist \
    --frappe-branch "$FRAPPE_BRANCH" \
    --python "$BENCH_PYTHON" \
    --skip-redis-config-generation \
    frappe-bench
else
  log "Existing bench found; keeping it and continuing configuration."
fi

cd "$BENCH_DIR"

log "Configuring the container-managed database and Redis services..."
bench set-mariadb-host database
bench set-redis-cache-host redis://redis-cache:6379
bench set-redis-queue-host redis://redis-queue:6379
bench set-redis-socketio-host redis://redis-socketio:6379

# Redis is provided as separate Compose services, not as child processes of bench start.
if [[ -f Procfile ]]; then
  sed -i -E '/^(redis_cache|redis_queue|redis_socketio):/d' Procfile
fi

site_is_initialised() {
  bench --site "$SITE_NAME" list-apps 2>/dev/null | grep -q '^frappe'
}

if [[ -f "sites/$SITE_NAME/site_config.json" ]] && ! site_is_initialised; then
  die "Site '$SITE_NAME' is only partly created (an earlier setup stopped midway). Remove it with: cd $BENCH_DIR && bench drop-site $SITE_NAME --root-password <MARIADB_ROOT_PASSWORD> --force   then rerun scripts/bootstrap.sh"
fi

if [[ ! -f "sites/$SITE_NAME/site_config.json" ]]; then
  log "Creating development site '$SITE_NAME'..."
  bench new-site "$SITE_NAME" \
    --mariadb-root-password "$MARIADB_ROOT_PASSWORD" \
    --admin-password "$SITE_ADMIN_PASSWORD" \
    --no-mariadb-socket
else
  log "Site '$SITE_NAME' already exists; skipping site creation."
fi

bench --site "$SITE_NAME" set-config developer_mode 1

# Apps install in the order listed in the preset (validated: dependencies come first).
for app_entry in ${ENABLED_APPS[@]+"${ENABLED_APPS[@]}"}; do
  IFS=$'\t' read -r app_name app_repository app_branch <<< "$app_entry"
  [[ -n "$app_name" ]] || continue

  if [[ ! -d "$BENCH_DIR/apps/$app_name" ]]; then
    log "Downloading '$app_name' from $app_repository (branch: $app_branch)..."
    bench get-app --branch "$app_branch" "$app_repository"
  else
    log "App source '$app_name' already exists; skipping download."
  fi

  if ! bench --site "$SITE_NAME" list-apps 2>/dev/null | grep -Eq "^${app_name}([[:space:]]|\$)"; then
    log "Installing '$app_name' on site '$SITE_NAME'..."
    bench --site "$SITE_NAME" install-app "$app_name"
  else
    log "App '$app_name' is already installed on '$SITE_NAME'."
  fi
done

bench use "$SITE_NAME"
bench --site "$SITE_NAME" clear-cache

touch "$READY_FILE"
log "Bootstrap completed. Site '$SITE_NAME' is ready; the web server starts automatically."
log "Open forwarded port 8000 and log in as Administrator."
