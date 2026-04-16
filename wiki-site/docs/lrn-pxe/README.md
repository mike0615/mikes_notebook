# LRN_PXE — Network Boot Server

A complete, self-hosted PXE boot environment for Rocky Linux 9/10. Deploy operating systems to any machine on your network — no USB drives, no DVDs — through a modern web interface.

---

## Features

- **Web Management UI** — Add ISOs, create kickstarts, and build boot menus from your browser
- **BIOS + UEFI support** — Automatically serves the right iPXE binary to any client
- **Kickstart automation** — Link kickstart files to boot entries for fully unattended installs
- **Dynamic menu** — Boot menu updates instantly when you make changes
- **CLI tool** — Full `lrn-pxe` command for server-side management
- **iPXE from source** — Built from the bundled iPXE source (commit bd13697)

---

## Quick Start

**1. Copy to your Rocky Linux 9/10 server and run:**
```bash
sudo bash install.sh
```

**2. Follow the prompts** (network interface, DHCP range, server IP)

**3. Open the web interface:**
```
http://<your-server-ip>/
```

**4. Add a boot image** → Extract boot files → Add to menu → Boot a client

---

## Documentation

| Document | Description |
|----------|-------------|
| [USER_GUIDE.md](docs/USER_GUIDE.md) | Complete walkthrough for all features |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common problems and fixes |
| [SPEC_SHEET.md](docs/SPEC_SHEET.md) | Technical specifications and API reference |

---

## Project Structure

```
lrn_pxe/
├── install.sh              # Main installer
├── configs/                # Config templates
│   └── ipxe/              # iPXE boot scripts
├── scripts/
│   └── lrn-pxe-cli.sh     # CLI management tool
├── web/
│   ├── app.py              # Flask web application
│   ├── run_dev.py          # Local development runner
│   ├── templates/          # HTML templates (Bootstrap 5)
│   └── static/             # CSS and JavaScript
├── systemd/
│   └── lrn-pxe.service    # systemd service unit
└── docs/
    ├── USER_GUIDE.md
    ├── TROUBLESHOOTING.md
    └── SPEC_SHEET.md
```

---

## Architecture

```
PXE Client  ──DHCP──►  dnsmasq  (port 67/UDP)
            ◄─IP+Boot─
            ──TFTP──►  dnsmasq  (port 69/UDP)  →  /var/lib/tftpboot/ipxe/
            ◄─iPXE──
            ──HTTP──►  nginx    (port 80/TCP)   →  Flask (port 8080)
            ◄─menu──                            →  /opt/lrn_pxe/
```

---

## Service Management

```bash
lrn-pxe status         # Check all services
lrn-pxe restart        # Restart everything
lrn-pxe logs           # Tail web UI logs
lrn-pxe logs dhcp      # Tail DHCP/TFTP logs

systemctl status lrn-pxe    # Web UI service
systemctl status dnsmasq    # DHCP + TFTP
systemctl status nginx      # HTTP server
```

---

## Requirements

- Rocky Linux 9.x or 10.x (x86_64)
- Root / sudo access
- Static IP address
- 50 GB+ disk space (for ISOs)
- No other DHCP server on the same network segment

---

## iPXE Source

The bundled iPXE source (`iPXE/ipxe-bd13697/`) is used to build custom BIOS and UEFI boot images with an embedded chainload URL pointing to the LRN_PXE menu endpoint. iPXE is licensed under GPL v2 / UBDL.
