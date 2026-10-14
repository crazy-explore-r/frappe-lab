# Frappe Lab

**A configurable playground for Frappe Framework, ERPNext, and other Frappe apps.**

Frappe Lab is a development workspace built around GitHub Codespaces, Docker Compose, and Frappe Bench. Its goal is to give developers a repeatable place to test apps, explore framework behavior, and debug customizations without preparing a machine from scratch.

> **Status:** Early development. One end-to-end run has been verified in GitHub Codespaces (2-core, 8 GB): the bootstrap finished in about 8 minutes, and Frappe 15.123.0 with ERPNext 15.122.0 opened through the forwarded port 8000 and accepted an Administrator login. A rerun of the bootstrap kept existing data. Not yet verified: free-plan accounts, other app combinations such as HRMS, the debugger profiles, and the site starting automatically when a stopped workspace resumes (run `bench start` yourself for now).

## What it is designed for

- Install Frappe Framework and select compatible apps from a manifest.
- Configure app repositories and branches without editing bootstrap commands.
- Use a preconfigured VS Code workspace and debugger.
- Keep database and Redis services isolated from the Frappe workspace.
- Recreate a disposable environment for demos, learning, and app compatibility checks.

## Start a workspace

1. Open this repository on GitHub.
2. Select **Code → Codespaces → Create codespace on the default branch**.
3. Wait for the bootstrap command to finish; follow the Codespaces creation log if it takes time.
4. In the terminal, run `cd frappe-bench && bench start`, or launch **Frappe Lab: Web Server** from the VS Code **Run and Debug** panel.
5. Open forwarded port **8000**.

The initial configuration uses development-only database and site administrator passwords. These values are public because they are in this demo repository. **Never use them for production, real customer data, or a publicly exposed server.**

## Configure your apps

Edit [`.devcontainer/frappe-lab.env`](.devcontainer/frappe-lab.env) to select the Frappe branch, site name, and local demo credentials.

Edit [`config/apps.json`](config/apps.json) to choose which app repositories to install. Each enabled entry defines a repository, branch, and install flag. Add app dependencies before the apps that require them. The app name must match the app's directory/package name so Bench can find it.

Keep every app branch compatible with the selected Frappe branch; arbitrary combinations are not guaranteed to work. The committed defaults target the version-15 line and enable ERPNext. HRMS is provided as an optional example and is disabled by default.

## Developer workflow

VS Code includes launch configurations for the Frappe web server and background workers. Use the **Run and Debug** panel to select the process you need.

Useful references:

- [Frappe Framework installation requirements](https://docs.frappe.io/framework/user/en/installation)
- [Frappe Bench commands](https://github.com/frappe/bench)
- [ERPNext repository](https://github.com/frappe/erpnext)
- [Frappe HRMS repository](https://github.com/frappe/hrms)

## Credits

The early version of this project was informed by the community project [`frappe_codespace`](https://github.com/vjFaLk/frappe_codespace) by [Valmik (vjFaLk)](https://github.com/vjFaLk). Frappe Lab is being independently redesigned and maintained with its own configuration, workflow, and roadmap.

Frappe Lab is a community project and is not an official Frappe or ERPNext product.

The original MIT license notice is retained in [`license.txt`](license.txt).

## Contributing

Bug reports and pull requests are welcome. Please include the operating environment, Frappe and app branches, and the relevant setup output. Remove credentials and other sensitive information from logs before sharing.

## License

MIT. See [`license.txt`](license.txt) for the retained copyright and license notice.
