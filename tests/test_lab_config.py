import copy
import json
import re
import sys
import unittest
from urllib.parse import unquote
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import lab_config  # noqa: E402

BASE = {
    "title": "T",
    "description": "D",
    "frappe_branch": "version-15",
    "apps": [
        {"name": "erpnext", "repository": "https://github.com/frappe/erpnext", "branch": "version-15"},
        {
            "name": "hrms",
            "repository": "https://github.com/frappe/hrms",
            "branch": "version-15",
            "requires": ["erpnext"],
        },
    ],
}


def make(**changes):
    preset = copy.deepcopy(BASE)
    preset.update(changes)
    return preset


class ValidateTests(unittest.TestCase):
    def assertRejects(self, preset, fragment):
        with self.assertRaises(lab_config.ConfigError) as ctx:
            lab_config.validate(preset)
        self.assertIn(fragment, str(ctx.exception))

    def test_valid_preset(self):
        self.assertIs(lab_config.validate(make()) is not None, True)

    def test_frappe_only_is_valid(self):
        lab_config.validate(make(apps=[]))

    def test_duplicate_app(self):
        apps = copy.deepcopy(BASE["apps"]) + [copy.deepcopy(BASE["apps"][0])]
        self.assertRejects(make(apps=apps), "defined more than once")

    def test_non_https_repository(self):
        apps = copy.deepcopy(BASE["apps"])
        apps[0]["repository"] = "http://github.com/frappe/erpnext"
        self.assertRejects(make(apps=apps), "https Git URL")

    def test_repository_without_path(self):
        apps = copy.deepcopy(BASE["apps"])
        apps[0]["repository"] = "https://github.com"
        self.assertRejects(make(apps=apps), "https Git URL")

    def test_missing_branch(self):
        apps = copy.deepcopy(BASE["apps"])
        del apps[0]["branch"]
        self.assertRejects(make(apps=apps), "branch")

    def test_blank_frappe_branch(self):
        self.assertRejects(make(frappe_branch=" "), "frappe_branch")

    def test_invalid_app_name(self):
        apps = copy.deepcopy(BASE["apps"])
        apps[0]["name"] = "erp next; rm -rf"
        self.assertRejects(make(apps=apps), "invalid app name")

    def test_unknown_key_is_a_typo_guard(self):
        apps = copy.deepcopy(BASE["apps"])
        apps[0]["brach"] = "version-15"
        self.assertRejects(make(apps=apps), "unknown key")

    def test_requires_must_come_first(self):
        apps = list(reversed(copy.deepcopy(BASE["apps"])))
        self.assertRejects(make(apps=apps), "requires 'erpnext'")

    def test_requires_disabled_app(self):
        apps = copy.deepcopy(BASE["apps"])
        apps[0]["enabled"] = False
        self.assertRejects(make(apps=apps), "requires 'erpnext'")

    def test_disabled_app_with_unmet_requirement_is_ignored(self):
        apps = copy.deepcopy(BASE["apps"])
        apps[0]["enabled"] = False
        apps[1]["enabled"] = False
        lab_config.validate(make(apps=apps))

    def test_enabled_must_be_boolean(self):
        apps = copy.deepcopy(BASE["apps"])
        apps[0]["enabled"] = "yes"
        self.assertRejects(make(apps=apps), "'enabled'")


class ShippedPresetTests(unittest.TestCase):
    def test_every_shipped_preset_is_valid(self):
        names = sorted(p.stem for p in (ROOT / "config" / "presets").glob("*.json"))
        self.assertTrue(names)
        for name in names:
            with self.subTest(preset=name):
                lab_config.load(name)

    def test_unknown_preset_lists_available(self):
        with self.assertRaises(lab_config.ConfigError) as ctx:
            lab_config.load("does-not-exist")
        self.assertIn("available:", str(ctx.exception))

    def test_preset_name_cannot_escape_directory(self):
        with self.assertRaises(lab_config.ConfigError):
            lab_config.load("../../etc/passwd")


class DevcontainerTests(unittest.TestCase):
    """Each preset has a Dev Container folder that selects it and nothing else."""

    def test_devcontainer_per_preset(self):
        presets = {p.stem for p in (ROOT / "config" / "presets").glob("*.json")}
        folders = {p.parent.name for p in (ROOT / ".devcontainer").glob("*/devcontainer.json")}
        self.assertEqual(presets, folders)
        for name in presets:
            config = json.loads((ROOT / ".devcontainer" / name / "devcontainer.json").read_text())
            self.assertEqual(config["remoteEnv"]["LAB_PRESET"], name)
            self.assertEqual(config["dockerComposeFile"], "../docker-compose.yml")


class LauncherSiteTests(unittest.TestCase):
    """The launcher page links to real Dev Container files, one per preset."""

    def setUp(self):
        html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        self.links = re.findall(r'href="(https://codespaces\.new/[^"]+)"', html.replace("&amp;", "&"))

    def test_every_link_targets_an_existing_devcontainer(self):
        self.assertTrue(self.links)
        for link in self.links:
            with self.subTest(link=link):
                match = re.search(r"devcontainer_path=([^&]+)", link)
                self.assertIsNotNone(match, "launch link has no devcontainer_path")
                self.assertTrue((ROOT / unquote(match.group(1))).is_file())

    def test_every_preset_has_a_launch_link(self):
        linked = {unquote(re.search(r"devcontainer_path=([^&]+)", l).group(1)).split("/")[1] for l in self.links}
        presets = {p.stem for p in (ROOT / "config" / "presets").glob("*.json")}
        self.assertEqual(presets, linked)


if __name__ == "__main__":
    unittest.main()
