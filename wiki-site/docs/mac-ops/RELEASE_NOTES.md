# mac-ops Release Notes

**Author:** Mike Anderson
**Project:** Maytag Ansible Console (mac-ops)

---

## v1.2.0 — 2025-03-15

### Summary
Production hardening update. Adds SELinux port labeling and an explicit ownership-fix step to the installer, ensuring the `macops` service user always has write access to data directories after install. Version bump reflected in `install.sh` and `ansible.cfg`.

### New Features
- **SELinux port labeling** — `install.sh` now runs `semanage port -a -t http_port_t -p tcp 5000` (with a `modify` fallback) so Flask can bind to port 5000 on enforcing SELinux systems without manual intervention. Requires `policycoreutils-python-utils`, which the installer installs automatically if missing.
- **`restorecon` on install directory** — File contexts under `/opt/mac-ops` are restored after SELinux labeling to prevent context-mismatch denials.
- **Ownership fix step (Step 9c)** — Installer explicitly runs `chown -R macops:macops` on `ansible/`, `backend/`, `reports/`, and `logs/` after SELinux work. Prevents "Permission denied" save errors that occur when `restorecon` or package operations reset file ownership.

### Changes
- `install.sh` version bumped to 1.2.0
- `ansible.cfg` version comment updated to 1.2.0
- `systemd` service description updated to reflect v1.2.0
- Platform reference broadened from Rocky Linux 9.7 to Rocky Linux 9.x

### Bug Fixes
- Fixed "Cannot save playbooks or inventory" errors on SELinux-enforcing systems caused by ownership being reset by `restorecon` during installation

---

## v1.1.0 — 2025-03-15

### Summary
Major update introducing full airgap support, web-based SSH console, ad-hoc runner, host checker, file browser with folder support, and production hardening.

### New Features
- **Airgap deployment** — All CDN dependencies removed from the main console. CodeMirror assets are now bundled locally under `frontend/vendor/codemirror/`. No internet access required at runtime for the main console.
- **`prep-airgap.sh`** — New preparation script downloads all pip wheel files (`flask`, `ansible-core`, `apscheduler`, etc.) into a `pip-packages/` bundle for fully offline installation.
- **`install.sh --airgap`** — Flag installs all Python packages from the local bundle instead of PyPI.
- **Web SSH Console (`/ssh-console`)** — Full browser-based SSH terminal powered by xterm.js 5.3 and Socket.IO over WebSocket. Supports any host/port, username/password authentication, PTY resize, 3,000-line scrollback, and a password show/hide toggle. Implemented with Paramiko on the backend and a dedicated `/ssh` Socket.IO namespace.
- **Ad-hoc Runner (`/adhoc`)** — Run any Ansible module against any host pattern from the browser without writing a playbook. Supports 12 modules (ping, shell, command, setup, service, dnf, copy, file, user, group, stat, raw) with context-sensitive argument hints and colorized ANSI output.
- **Host Checker (`/hostcheck`)** — Reachability and inventory audit tool. Checks ICMP ping (with latency), TCP port 22, and inventory membership for any list of hosts. Includes a **Load all inventory hosts** button, summary chips, progress bar, skeleton rows for instant feedback, and CSV export.
- **File browser — Playbooks** — Full recursive directory tree in the Playbooks editor sidebar. Create sub-folders, expand/collapse directories, click to open any file. Supports nested playbook organization (e.g. `linux/`, `networking/`, `docker/`).
- **File browser — Inventory** — Browse, open, and manage inventory files from a live file listing with in-place editing.
- **New Folder button** — Create subdirectory structure in the playbooks tree via the UI.
- **Path breadcrumb bar** — Shows full relative path of the currently open file (e.g. `ansible/playbooks/linux/setup.yml`).
- **New Playbook templates** — Five starter templates available when creating a new playbook: Blank, Gather Facts, Package Install, Service Management, and File Copy.
- **Playbook upload** — Upload one or more `.yml`/`.yaml` files directly from the browser into the playbooks directory.
- **`/api/browse/playbooks`** — New API endpoint returning a recursive directory tree (dirs + files).
- **`/api/browse/inventory`** — New API endpoint for inventory file listing.
- **`/api/playbooks/mkdir`** — New API endpoint to create subdirectories.
- **Dashboard** — New view with playbook count, inventory count, report count, schedule count, active schedule count, and the 10 most recent run logs with pass/fail status.
- **Quick Actions** — Dashboard shortcuts for New Playbook, View Reports, and Schedule Job.
- **Mascot** — Contextual Bitmoji reactions that change per active view and on idle timeout.
- **New built-in playbooks** — Added seven additional playbooks to the default library: `add_local_user.yml`, `change_local_user_password.yml`, `deploy_ssh_key.yml`, `disk_space_report.yml`, `freeipa_client_enroll.yml`, `reboot_hosts.yml`, and `service_control.yml`.

### Changes
- **AI Assistant removed** — Tab and all associated JS/API code removed. Not appropriate for airgapped environments.
- **Branding updated** — All references to `ansibleops` and `AnsibleOps` replaced with `mac-ops`. Install path changed from `/opt/mac` to `/opt/mac-ops`. Service renamed from `mac.service` to `mac-ops.service`.
- **Font stack** — Google Fonts (IBM Plex Mono, Epilogue) removed. Replaced with system font stack (`Consolas/Courier New` mono, `Segoe UI/Helvetica` sans). No external font requests.
- **`app.py` rewritten** — Full Python docstring with author, version, and license. Improved logging format. All route handlers documented with inline comments.
- **Author header** — `# Author: Mike Anderson` and version comment added to all source files.
- **Settings panel** — About section updated to reflect v1.1.0 and airgap status.
- **`install.sh` hardened** — EPEL removed entirely. `python3-virtualenv` replaced with stdlib `python3 -m venv`. `ansible-core` installed via pip into venv instead of dnf. Ansible binaries symlinked to `/usr/local/bin`. Sudoers updated to reference `/usr/local/bin/ansible-playbook`. Logrotate configured for 30-day daily compressed rotation.

### Bug Fixes
- Fixed `openRunModal` and `openSchedModal` to use `/api/browse/inventory` for correct file listing
- Fixed editor `clearHistory()` call on file open to prevent undo contamination across files
- Fixed `refreshPBTree()` to reload tree without losing editor state

### Security
- `prep-airgap.sh` validates same OS/arch to prevent architecture mismatch in pip wheels
- Security audit report path updated to `/opt/mac-ops/reports/`
- Reports directory set to mode 700 (readable only by the `macops` service user)

---

## v1.0.1 — 2025-03-14

### Summary
Hotfix for EPEL dependency failure during installation.

### Bug Fixes
- **Critical:** Removed `python3-virtualenv` from the `dnf install` block. The EPEL 9 package has a broken dependency: `python3-virtualenv → python3-wheel-wheel` (missing in Rocky 9). Installation now uses Python stdlib `venv` module (`python3 -m venv`) which is built into Python 3.9+ and requires no separate package.
- Removed `ansible` and `ansible-core` from the `dnf install` block entirely. Both are now installed via `pip install ansible-core` into the venv, bypassing the EPEL dependency chain completely.
- `ansible-playbook`, `ansible`, and `ansible-galaxy` symlinked to `/usr/local/bin` after pip install.
- Sudoers updated to reference `/usr/local/bin/ansible-playbook` instead of `/usr/bin/`.
- `systemd` service `Environment=PATH` updated to include venv bin directory.

---

## v1.0.0 — 2025-03-14

### Summary
Initial release of the Maytag Ansible Console (mac-ops).

### Features
- Browser-based YAML playbook editor (CodeMirror 5, material-darker theme)
- Inventory file manager (INI/YAML formats)
- Cron-based job scheduler with APScheduler (persists across restarts)
- System Inventory playbook — full HW, network, software, Docker → JSON report
- Security Audit playbook — login history, SSH, SUID, firewall → JSON report (mode 600)
- System Maintenance playbook — dnf update, kernel cleanup, log rotation
- Execution log viewer with colorized PLAY RECAP parsing
- Light/dark mode toggle (localStorage persistence)
- Bitmoji mascot with contextual reactions
- MAC logo (Maytag Ansible Console branding)
- `install.sh` for Rocky Linux 9.x (one-command deployment)
- systemd service (`mac-ops.service`) with auto-start
- firewalld integration (port 5000)
- APScheduler cron scheduling
- AI Assistant (Claude API) — *removed in v1.1.0*

---

## Roadmap

- [ ] HTTPS/TLS built-in (self-signed cert option)
- [ ] Role-based file organization templates
- [ ] Multi-host parallel run progress view
- [ ] Report comparison (diff between two inventory runs)
- [ ] Playbook import from Git repository (connected mode)
- [ ] Ansible Vault integration
- [ ] Email notifications on scheduled run completion
