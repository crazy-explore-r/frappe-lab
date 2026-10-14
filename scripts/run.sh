#!/usr/bin/env bash
# Main process of the workspace container. Waits until scripts/bootstrap.sh has finished,
# then keeps `bench start` running, so the site is up whenever the workspace is running
# (including after a stopped Codespace resumes).
set -Eeuo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_DIR="$WORKSPACE_ROOT/frappe-bench"
READY_FILE="$BENCH_DIR/.lab-ready"

export PATH="$HOME/.local/bin:$PATH"
if [[ -f "$HOME/.nvm/nvm.sh" ]]; then
  # shellcheck disable=SC1091
  source "$HOME/.nvm/nvm.sh"
fi

log() {
  printf '[Frappe Lab] %s\n' "$*"
}

log "Waiting for the first-time setup (scripts/bootstrap.sh) to finish..."
until [[ -f "$READY_FILE" ]]; do
  sleep 5
done

cd "$BENCH_DIR"
child=0
trap 'kill -TERM "$child" 2>/dev/null || true; wait "$child" 2>/dev/null || true; exit 0' TERM INT

while true; do
  log "Starting bench..."
  bench start &
  child=$!
  wait "$child" || true
  log "bench exited; restarting in 5 seconds..."
  sleep 5
done
