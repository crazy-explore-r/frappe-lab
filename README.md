# Frappe Lab

**A temporary Frappe and ERPNext environment you can start from a web page, with no server to set up.**

Frappe Lab runs Frappe Framework, ERPNext and other Frappe apps in a GitHub Codespace. It is for showing a demo, checking how a version looks, trying an idea, or developing and debugging a custom app. The workspace is disposable: start it, use it, delete it.

**Launcher:** <https://crazy-explore-r.github.io/frappe-lab/> (explains the steps for people without a GitHub account and has one Launch button per stack)

> **Status: early development.** One stack, Frappe + ERPNext, has been verified end to end in GitHub Codespaces. See [What has been tested](#what-has-been-tested). Do not rely on anything listed as untested.

## Stacks

| Stack | Preset | Status |
|---|---|---|
| Frappe + ERPNext (version-15) | `erpnext` | Tested |
| Frappe Framework only (version-15) | `frappe` | Not yet tested |
| Frappe + ERPNext + HRMS (version-15) | `erpnext-hrms` | Not yet tested |

Each stack is a small file in [`config/presets`](config/presets), selected by a matching folder in [`.devcontainer`](.devcontainer).

## Start a workspace

**From the launcher (no technical knowledge needed):** open the launcher page, choose a stack and press Launch. You need a free GitHub account.

**From this repository:** select **Code → Codespaces → New with options**, then choose a configuration (`erpnext`, `frappe` or `erpnext-hrms`).

The first start takes roughly 8 to 10 minutes. When it finishes, the web server starts on its own. Open the **Ports** tab, open the address for port 8000, and sign in as `Administrator` with the demo password from [`.devcontainer/frappe-lab.env`](.devcontainer/frappe-lab.env).

That password is public because it is in this repository. It is for disposable demo sites only. **Never use it for real data or any server reachable from the internet.**

## Choose versions and apps

A preset is a JSON file:

```json
{
  "title": "Frappe + ERPNext + HRMS",
  "description": "ERPNext with the HRMS app, all on the version-15 branches.",
  "frappe_branch": "version-15",
  "apps": [
    { "name": "erpnext", "repository": "https://github.com/frappe/erpnext", "branch": "version-15" },
    { "name": "hrms", "repository": "https://github.com/frappe/hrms", "branch": "version-15", "requires": ["erpnext"] }
  ]
}
```

- Change `frappe_branch` or an app's `branch` to use another version. Every app branch must be compatible with the Frappe branch; not every combination works.
- Set `"enabled": false` on an app to skip it. Apps install in list order, and `requires` stops the setup early if a dependency is missing or listed after the app that needs it.
- To add a stack, add a preset file and a [`.devcontainer`](.devcontainer) folder with the same name. Tests check that they match.

The preset is validated before anything is installed. Run `python3 scripts/lab_config.py check` to validate all of them.

## Develop and debug

[`.vscode/launch.json`](.vscode/launch.json) has debug profiles for the web server and the background workers. The web server runs from `bench start` by default; stop that process before starting the debug profile for the web server.

Useful references: [Frappe installation requirements](https://docs.frappe.io/framework/user/en/installation), [Frappe Bench](https://github.com/frappe/bench), [ERPNext](https://github.com/frappe/erpnext), [Frappe HRMS](https://github.com/frappe/hrms).

## What has been tested

Run in GitHub Codespaces on a 2-core, 8 GB machine, from the repository owner's account (its plan type was not checked):

- First start of the Frappe + ERPNext stack on Python 3.12: setup finished in about 8 minutes.
- The site opened through the forwarded port in a browser and accepted the Administrator login. Installed versions were Frappe 15.123.0 and ERPNext 15.122.0.
- Rerunning the setup on a finished workspace took 12 seconds and kept existing data.

Automated checks run on every push (preset validation, unit tests, shell syntax, Dev Container and Compose configuration). They do not start Frappe.

**Not verified yet:**

- The `frappe` and `erpnext-hrms` stacks.
- The web server starting by itself after setup and after a stopped Codespace resumes (the supervised start in [`scripts/run.sh`](scripts/run.sh)).
- A free-plan GitHub account. Machine sizes and the monthly allowance are set by GitHub.
- The launcher's Launch links selecting a stack from the browser.
- The debugger profiles.
- Local development with Docker outside Codespaces.

## Resources and limits

- Needs a GitHub account. Codespaces time and storage count against that account's allowance; see [GitHub's billing page](https://docs.github.com/en/billing/managing-billing-for-your-products/about-billing-for-github-codespaces).
- Codespaces stop when idle, and the site is private to your account unless you make the port public.
- The setup needs MariaDB, three Redis instances and the Frappe processes. The launch links ask for a 4-core, 16 GB machine; the verified minimum is 2-core, 8 GB.
- Node is v24 in the base image although Frappe version-15 lists Node 18. The asset build passed, but this is not otherwise checked.

More detail: [architecture](docs/architecture.md), [troubleshooting](docs/troubleshooting.md).

## Credits

An earlier version of this workspace was informed by [`frappe_codespace`](https://github.com/vjFaLk/frappe_codespace) by [Valmik (vjFaLk)](https://github.com/vjFaLk). Frappe Lab has since been rebuilt as a separate project with its own presets, bootstrap, launcher and tests. The original MIT license notice is kept in [`license.txt`](license.txt).

Frappe Lab is a community project. It is not an official Frappe or ERPNext product.

## Contributing

Bug reports and pull requests are welcome. Include the preset, the Frappe and app branches, and the relevant lines of the creation log, with credentials removed.

## License

MIT. See [`license.txt`](license.txt).
