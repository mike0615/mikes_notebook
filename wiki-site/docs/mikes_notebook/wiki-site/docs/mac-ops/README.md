# Maytag Admin Console (MAC)

**Author:** Mike Anderson
**Version:** 2.0.0
**License:** MIT
**Platform:** Rocky Linux 9.x

---

**Maytag Admin Console (MAC)** is a unified infrastructure management platform with enterprise-grade authentication and a pluggable tool architecture. Originally developed as mac-ops (Ansible console), it now provides a comprehensive admin interface with built-in tools for infrastructure automation, system administration, and cloud operations.

### Key Features

- **Enterprise Authentication** - Local user management, FreeIPA/LDAP integration, role-based access control (RBAC)
- **Secrets Vault** - Encrypted storage for API keys, passwords, tokens with fine-grained access control
- **Pluggable Tool Framework** - Extensible architecture for adding new admin tools
- **Audit Logging** - Comprehensive security event tracking with detailed audit trail
- **Beautiful Admin Dashboard** - Modern web interface for user and permission management
- **Ansible Integration** - Execute and schedule Ansible playbooks securely

### Tools Included

1. **Ansible** - Write, validate, execute, schedule, and report on automation playbooks
2. **PXE Boot** - Network boot server integration (LRN-PXE)
3. **Future Tools** - DHCP manager, DNS manager (Bind), monitoring dashboard, Netbox links

**Designed for airgapped environments.** All frontend assets are bundled locally. No external dependencies at runtime.

---

## Getting Started

### Quick Installation

```bash
# Install
pip install -r backend/requirements.txt

# Initialize
python backend/manage.py init-db
python backend/manage.py create-admin

# Run
python backend/app.py
```

Visit `https://localhost:5000/auth/login`

### Docker Deployment

```bash
docker build -t mac-ops .
docker run -d \
  -p 5000:5000 \
  -v /var/lib/mac-ops:/var/lib/mac-ops \
  -v /etc/mac-ops:/etc/mac-ops \
  mac-ops
```

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

- **Dashboard** — At-a-glance counts for playbooks, inventory files, reports, schedules, and active schedules. Shows the 10 most recent run logs with pass/fail status and timestamps. Quick Action buttons for common tasks (New Playbook, View Reports, Schedule Job).
- **Playbook Editor** — Full-featured CodeMirror 5 YAML editor with syntax highlighting, live validation, and undo history isolation per file. Recursive sidebar file browser with expand/collapse folder tree and breadcrumb path bar. Create, edit, save, upload, and delete playbooks. New Folder button creates subdirectory structure directly from the UI (e.g. `linux/`, `networking/`, `docker/`).
- **New Playbook Templates** — Five starter templates when creating a new playbook: Blank, Gather Facts, Package Install, Service Management, and File Copy.
- **Inventory Manager** — Browse, create, edit, save, and delete INI and YAML inventory files. In-place editor with breadcrumb path bar.
- **Cron Scheduler** — Schedule any playbook against any inventory file using cron syntax (APScheduler). Schedules persist across service restarts via `schedules.json`. Each schedule can be paused, resumed, or deleted from the UI. All enabled schedules are restored automatically on service start.
- **Reports Viewer** — Structured collapsible viewer for System Inventory and Security Audit JSON reports. Reports are tagged by type, host, and generation time.
- **Run Logs** — Colorized, scrollable viewer for all `ansible-playbook` execution logs. PLAY RECAP is parsed and summarized. Displays the 60 most recent log files.
- **Light & Dark Mode** — Full theme toggle with browser preference persistence.
- **Mascot** — Contextual Bitmoji reactions that change based on the active view and idle state.

### SSH Console (`/ssh-console`)

Browser-based SSH terminal powered by xterm.js 5.3 and Socket.IO over WebSocket. Opens in a separate popup window from the sidebar.

- Connect to any host by hostname or IP with configurable port (default 22)
- Username and password authentication
- Password show/hide toggle
- Full PTY emulation (`xterm-256color`, 220×50 default)
- Dynamic terminal resize — backend PTY is resized when the browser window changes
- 3,000-line scrollback buffer
- Connection status indicator (green/red dot) and session info bar (`user@host:port`)
- Disconnect button clears the session and returns to the connection form; password field is cleared on disconnect

### Ad-hoc Runner (`/adhoc`)

Run any Ansible module against any host pattern directly from the browser without writing a playbook. Opens in a separate popup window.

- Host pattern field accepts group names, hostnames, IPs, or `all`
- Inventory file selector populated from the live inventory list
- 12 built-in modules: `ping`, `shell`, `command`, `setup`, `service`, `dnf`, `copy`, `file`, `user`, `group`, `stat`, `raw`
- Context-sensitive argument hints and placeholders that update per selected module
- Quick-reference table showing common module argument syntax
- Colorized ANSI output with pass/fail status indicator and executed-command display
- 60-second execution timeout

### Host Checker (`/hostcheck`)

Reachability and inventory audit tool for any set of hosts. Opens in a separate popup window.

- Enter hosts manually (one per line) or click **Load all inventory hosts** to auto-populate from all inventory files (parses `ansible_host=` overrides)
- Three checks per host: ICMP ping with latency (ms), TCP port 22 reachability, and inventory membership
- Results table with color-coded badges — green (pass), red (fail), amber (not in inventory)
- Summary bar shows total reachable, unreachable, SSH-open, and in-inventory counts
- Progress bar with skeleton rows for immediate visual feedback during check
- **Copy CSV** button exports results to clipboard as comma-separated values

---

## Built-In Playbooks

| Playbook | Purpose |
|---|---|
| `system_inventory.yml` | Full HW, network, software, Docker, users, services, and performance snapshot → JSON report |
| `security_audit.yml` | Auth logs, SSH keys, SUID/SGID files, firewall, SELinux, open ports, user accounts, cron jobs, RPM integrity → JSON report (mode 600) |
| `system_maintenance.yml` | dnf update all packages, remove old kernels (keep 2), clean dnf cache, vacuum journal logs (30d), compress old logs, report disk usage and failed services |
| `add_local_user.yml` | Create a local user with specified UID, shell, and groups; set initial password; optionally grant passwordless sudo; optionally deploy an SSH authorized key; force password change on first login |
| `change_local_user_password.yml` | Change the password for an existing local user; verifies the user exists before acting; reads new hashed password from Ansible Vault; optionally forces password change on next login; reports per-host success/skip/failure |
| `deploy_ssh_key.yml` | Add or remove an SSH public key from a user's `authorized_keys`; verifies target user exists; idempotent (safe to re-run); fixes `~/.ssh` directory permissions after changes |
| `disk_space_report.yml` | Report disk and inode usage across all hosts; flags filesystems over configurable warning/critical thresholds; identifies top directories by size; fetches a JSON summary report back to the controller |
| `freeipa_client_enroll.yml` | Enroll Rocky 9 hosts as FreeIPA clients (domain: `lrn.sys`, realm: `LRN.SYS`, server: `ipa01-main.lrn.sys`) |
| `reboot_hosts.yml` | Safely reboot hosts one at a time (serial: 1); pre-reboot checks (disk space, failed services); graceful reboot with configurable timeout; waits for SSH to respond; post-reboot verification (uptime, failed systemd units) |
| `service_control.yml` | Start, stop, restart, reload, or check the status of a systemd service across all hosts; verifies the unit file exists before acting; optionally enables or disables the service; reports current state after action |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.9+, Flask 3.x, Flask-CORS, Flask-SocketIO 5.x |
| Scheduler | APScheduler 3.x (BackgroundScheduler, CronTrigger) |
| SSH transport | Paramiko 3.x |
| YAML parsing | PyYAML 6.x |
| Ansible | ansible-core 2.15+ (installed into venv) |
| Editor | CodeMirror 5 (bundled locally — airgap-safe) |
| SSH terminal | xterm.js 5.3 + xterm-addon-fit 0.8 (CDN), Socket.IO 4.7 (CDN) |
| Frontend | Vanilla JavaScript, system font stack (no Google Fonts) |

---

## Quick Start

### Standard Install (requires internet)

```bash
# Transfer to Rocky 9.x server
scp -r mac-ops/ root@YOUR_VM_IP:/tmp/

# On the server
cd /tmp/mac-ops
sudo bash install.sh

# Open browser
http://YOUR_VM_IP:5000
```

### Airgapped Install

```bash
# Step 1: On a connected machine with the same OS/arch as the target, bundle dependencies
bash prep-airgap.sh

# Step 2: Transfer the entire mac-ops/ folder (including pip-packages/) to the airgapped server

# Step 3: On the airgapped server
sudo bash install.sh --airgap
```

---

## Requirements

| Item | Minimum | Recommended |
|---|---|---|
| OS | Rocky Linux 9.3+ | Rocky Linux 9.7 |
| CPU | 2 vCPU | 4 vCPU |
| RAM | 2 GB | 4 GB |
| Disk | 10 GB free | 20 GB free |

---

## URLs

| URL | Description |
|---|---|
| `http://HOST:5000/` | Main console (Dashboard, Playbooks, Inventory, Schedules, Reports, Logs) |
| `http://HOST:5000/ssh-console` | Web SSH terminal |
| `http://HOST:5000/adhoc` | Ad-hoc module runner |
| `http://HOST:5000/hostcheck` | Host reachability checker |

---

## Directory Layout

```
/opt/mac-ops/
├── frontend/                  # Web UI
│   ├── index.html             # Single-page main console
│   ├── adhoc.html             # Ad-hoc runner page
│   ├── hostcheck.html         # Host checker page
│   ├── ssh_console.html       # SSH terminal page
│   └── vendor/codemirror/     # Bundled editor assets (airgap-safe)
├── backend/
│   ├── app.py                 # Flask REST API + Socket.IO server
│   └── schedules.json         # Persisted schedule definitions
├── ansible/
│   ├── playbooks/             # YAML playbooks (subdirectories supported)
│   └── inventory/             # Host inventory files (INI and YAML)
├── reports/                   # Generated JSON reports (mode 700)
├── logs/                      # Execution logs (run_*.log) + mac-ops.log
└── venv/                      # Python virtual environment
```

---

## Service Management

```bash
systemctl status  mac-ops
systemctl restart mac-ops
systemctl stop    mac-ops
journalctl -u mac-ops -f           # live log stream
journalctl -u mac-ops -n 50        # last 50 lines
```

---

## Post-Install: Add SSH Key to Managed Hosts

After installation, the installer prints the generated public key. Add it to every host you want to manage:

```bash
# View the key on the mac-ops server
cat /home/macops/.ssh/ansible_key.pub

# On each target host
echo 'PASTE_KEY_HERE' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

---

## Troubleshooting

**Cannot save playbooks or inventory files**

The `macops` service user has lost write access to the data directories. This can happen after a `restorecon`, git pull, or file copy that resets ownership. Run on the server:

```bash
sudo chown -R macops:macops /opt/mac-ops/ansible
sudo chown -R macops:macops /opt/mac-ops/backend
sudo chown -R macops:macops /opt/mac-ops/reports
sudo chown -R macops:macops /opt/mac-ops/logs
```

No service restart is needed — saves will work immediately.

**Service fails to start (SELinux)**

Port 5000 may not be labeled correctly. Run:

```bash
sudo semanage port -a -t http_port_t -p tcp 5000
sudo systemctl restart mac-ops
```

**Check the application log**

```bash
tail -100 /opt/mac-ops/logs/mac-ops.log
```

---

## Security Hardening (Production)

For production deployments, place mac-ops behind Nginx with TLS:

```bash
dnf install -y nginx python3-certbot-nginx
# Configure /etc/nginx/conf.d/mac-ops.conf
certbot --nginx -d mac-ops.yourdomain.com
firewall-cmd --remove-port=5000/tcp --permanent
firewall-cmd --add-service=https --permanent && firewall-cmd --reload
```

---

## Changelog

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for full version history.

---

## License

MIT License — Copyright (c) 2025 Mike Anderson
See [LICENSE](LICENSE) for details.
