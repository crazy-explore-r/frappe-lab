#!/usr/bin/env bash
# Checks that the bash side of scripts/bootstrap.sh can read every shipped preset,
# including Frappe-only (empty app list) under `set -u`, and that a bad preset fails.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
failures=0

parse_preset() {
  local preset="$1" rows lines branch apps
  rows="$(python3 "$ROOT/scripts/lab_config.py" show "$preset")" || return 1
  mapfile -t lines <<< "$rows"
  IFS=$'\t' read -r _ branch <<< "${lines[0]}"
  apps=("${lines[@]:1}")
  printf '%s: frappe_branch=%s apps=%s' "$preset" "$branch" "${#apps[@]}"
  local entry name repo app_branch
  for entry in ${apps[@]+"${apps[@]}"}; do
    IFS=$'\t' read -r name repo app_branch <<< "$entry"
    printf ' [%s@%s]' "$name" "$app_branch"
  done
  printf '\n'
}

for file in "$ROOT"/config/presets/*.json; do
  preset="$(basename "$file" .json)"
  parse_preset "$preset" || { echo "FAIL: $preset did not parse" >&2; failures=$((failures + 1)); }
done

if parse_preset "does-not-exist" >/dev/null 2>&1; then
  echo "FAIL: an unknown preset was accepted" >&2
  failures=$((failures + 1))
else
  echo "ok: unknown preset is rejected"
fi

exit "$failures"
