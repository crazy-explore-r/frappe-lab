#!/usr/bin/env python3
"""Load and validate Frappe Lab presets (config/presets/<name>.json).

    lab_config.py show <preset>   print the Frappe branch and enabled apps as TSV
    lab_config.py check           validate every preset in config/presets

Used by scripts/bootstrap.sh before it changes anything, and by CI.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

PRESET_DIR = Path(__file__).resolve().parent.parent / "config" / "presets"
NAME_RE = re.compile(r"[A-Za-z0-9_-]+")
BRANCH_RE = re.compile(r"[A-Za-z0-9._/-]+")
PRESET_KEYS = {"title", "description", "frappe_branch", "apps"}
APP_KEYS = {"name", "repository", "branch", "enabled", "requires"}


class ConfigError(ValueError):
    pass


def _branch(value, where):
    if not isinstance(value, str) or not BRANCH_RE.fullmatch(value):
        raise ConfigError(f"{where}: branch must be a non-empty name such as 'version-15', got {value!r}")


def validate(preset, label="preset"):
    """Return the preset if valid, otherwise raise ConfigError with an actionable message."""
    if not isinstance(preset, dict):
        raise ConfigError(f"{label}: must be a JSON object")
    unknown = set(preset) - PRESET_KEYS
    if unknown:
        raise ConfigError(f"{label}: unknown key(s) {sorted(unknown)}; allowed: {sorted(PRESET_KEYS)}")
    for key in ("title", "description"):
        if not isinstance(preset.get(key), str) or not preset[key].strip():
            raise ConfigError(f"{label}: '{key}' must be a non-empty string")
    _branch(preset.get("frappe_branch"), f"{label}: frappe_branch")

    apps = preset.get("apps")
    if not isinstance(apps, list):
        raise ConfigError(f"{label}: 'apps' must be a list (use [] for Frappe only)")

    seen = set()
    installed_before = set()
    for index, app in enumerate(apps):
        where = f"{label}: apps[{index}]"
        if not isinstance(app, dict):
            raise ConfigError(f"{where}: must be an object")
        unknown = set(app) - APP_KEYS
        if unknown:
            raise ConfigError(f"{where}: unknown key(s) {sorted(unknown)}; allowed: {sorted(APP_KEYS)}")
        name = app.get("name")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            raise ConfigError(f"{where}: invalid app name {name!r} (letters, digits, '_' and '-' only)")
        where = f"{label}: app '{name}'"
        if name in seen:
            raise ConfigError(f"{where}: defined more than once")
        seen.add(name)

        repository = app.get("repository")
        parsed = urlparse(repository if isinstance(repository, str) else "")
        if parsed.scheme != "https" or not parsed.netloc or not parsed.path.strip("/"):
            raise ConfigError(f"{where}: repository must be an https Git URL, got {repository!r}")
        _branch(app.get("branch"), where)

        enabled = app.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ConfigError(f"{where}: 'enabled' must be true or false")
        requires = app.get("requires", [])
        if not isinstance(requires, list) or not all(isinstance(r, str) for r in requires):
            raise ConfigError(f"{where}: 'requires' must be a list of app names")

        if enabled:
            for required in requires:
                if required not in installed_before:
                    raise ConfigError(
                        f"{where}: requires '{required}', which must be enabled and listed "
                        f"before it in 'apps' (apps install in list order)"
                    )
            installed_before.add(name)
    return preset


def load(name):
    if not NAME_RE.fullmatch(name):
        raise ConfigError(f"invalid preset name {name!r}")
    path = PRESET_DIR / f"{name}.json"
    if not path.is_file():
        available = sorted(p.stem for p in PRESET_DIR.glob("*.json"))
        raise ConfigError(f"preset '{name}' not found in config/presets (available: {', '.join(available)})")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigError(f"{path.name}: invalid JSON ({error})") from error
    return validate(data, label=path.name)


def main(argv):
    try:
        if len(argv) == 3 and argv[1] == "show":
            preset = load(argv[2])
            print(f"frappe\t{preset['frappe_branch']}")
            for app in preset["apps"]:
                if app.get("enabled", True):
                    print(f"{app['name']}\t{app['repository']}\t{app['branch']}")
            return 0
        if len(argv) == 2 and argv[1] == "check":
            names = sorted(p.stem for p in PRESET_DIR.glob("*.json"))
            if not names:
                raise ConfigError("no presets found in config/presets")
            for name in names:
                load(name)
                print(f"ok: {name}")
            return 0
    except ConfigError as error:
        print(f"config error: {error}", file=sys.stderr)
        return 1
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
