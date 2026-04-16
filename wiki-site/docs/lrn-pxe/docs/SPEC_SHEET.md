# LRN_PXE Technical Specification Sheet

**Product:** LRN_PXE — Network PXE Boot Server
**Version:** 1.0.0
**Date:** 2026-03-22
**Platform:** Rocky Linux 9 / Rocky Linux 10

---

## Executive Summary

LRN_PXE is a turnkey, self-hosted PXE (Pre-boot eXecution Environment) server built for enterprise and lab environments. It provides a complete network boot infrastructure — DHCP, TFTP, HTTP, and a modern web management interface — allowing administrators to deploy operating systems to unlimited machines simultaneously, with or without user interaction.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    LRN_PXE Server                           │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   dnsmasq    │  │    nginx     │  │   Flask (lrn-pxe)│  │
│  │  DHCP + TFTP │  │  HTTP Server │  │  Web UI + Menu   │  │
│  │  Port 67/UDP │  │  Port 80/TCP │  │  Port 8080/TCP   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         │                 │                   │             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              /opt/lrn_pxe/                          │   │
│  │  isos/  kickstarts/  boot/  mounts/  config/        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         /var/lib/tftpboot/ipxe/                      │   │
│  │         undionly.kpxe  (BIOS)   ipxe.efi  (UEFI)    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
          │               │               │
    ┌─────┘         ┌─────┘         ┌─────┘
    ▼               ▼               ▼
 BIOS Client    UEFI Client    Browser (Admin)
```

---

## Component Specifications

### 1. Boot Firmware — iPXE

| Property | Value |
|----------|-------|
| Source | Bundled (commit bd13697) |
| License | GPL v2 / UBDL |
| BIOS binary | `undionly.kpxe` |
| UEFI binary | `ipxe.efi` (x86_64) |
| Build system | GNU Make + GCC |
| Embedded script | HTTP chainload to Flask menu endpoint |
| Protocol support | HTTP, HTTPS, TFTP, iSCSI, FCoE, NFS |
| Architecture | x86_64 (BIOS + UEFI) |

### 2. DHCP / TFTP Server — dnsmasq

| Property | Value |
|----------|-------|
| Package | dnsmasq (Rocky Linux default repo) |
| DHCP version | DHCPv4 |
| TFTP | Built-in, root at `/var/lib/tftpboot` |
| UEFI detection | Client architecture option 7/9 |
| iPXE detection | DHCP option 175 |
| Boot logic | Tag-based conditional (UEFI/BIOS/iPXE) |
| Log facility | `/var/log/dnsmasq.log` |

**Boot decision tree:**

```
Client sends DHCP request
├─ Option 175 present (already iPXE)  → serve http://<ip>/menu.ipxe
├─ Arch option = 7 or 9 (UEFI)       → serve ipxe/ipxe.efi via TFTP
└─ Other (BIOS/Legacy)                → serve ipxe/undionly.kpxe via TFTP
```

### 3. HTTP Server — nginx

| Property | Value |
|----------|-------|
| Package | nginx (EPEL) |
| Listen port | 80 (TCP) |
| ISO serving | Direct file serving with autoindex |
| Range requests | Enabled (required for large ISO serving) |
| Max upload size | 50 GB (configurable) |
| Proxy | Forwards `/` to Flask on port 8080 |
| Static paths | `/isos/`, `/boot/`, `/kickstarts/`, `/mounts/` |
| Log | `/var/log/nginx/lrn_pxe_access.log` |

### 4. Web Management Interface — Flask

| Property | Value |
|----------|-------|
| Framework | Flask 3.x (Python 3.x) |
| Runtime | CPython, virtualenv at `/opt/lrn_pxe/venv/` |
| Listen | `0.0.0.0:8080` (proxied through nginx) |
| Authentication | None (network-level — restrict via firewall) |
| Config format | JSON (`menu.json`, `settings.json`) |
| ISO extraction | Python `subprocess` → `mount`, `cp` |
| Menu generation | Dynamic iPXE script, generated on-request |
| API style | REST (JSON) |

### 5. Web UI — Frontend

| Property | Value |
|----------|-------|
| Framework | Bootstrap 5.3 (CDN) |
| Icons | Bootstrap Icons 1.11 (CDN) |
| Theme | Dark (GitHub-inspired) |
| JavaScript | Vanilla ES2020+ (no build step) |
| Upload | XMLHttpRequest with progress tracking |
| Drag & drop | Native HTML5 Drag and Drop API |
| Responsive | Sidebar collapses on mobile (<768px) |

---

## Data Storage

### Directory Structure (Server)

```
/opt/lrn_pxe/
├── config/
│   ├── menu.json           # PXE menu entries (JSON)
│   └── settings.json       # Server & DHCP settings (JSON)
├── isos/                   # ISO files (*.iso)
├── kickstarts/             # Kickstart/preseed files (*.ks, *.cfg)
├── boot/
│   └── <iso-id>/
│       ├── vmlinuz         # Extracted kernel
│       └── initrd.img      # Extracted initial RAM disk
├── mounts/
│   └── <iso-id>/           # Loop-mounted ISO (install repo)
├── web/                    # Flask application
│   ├── app.py
│   ├── templates/
│   └── static/
├── venv/                   # Python virtual environment
└── logs/
    ├── web.log
    └── web_error.log

/var/lib/tftpboot/
└── ipxe/
    ├── undionly.kpxe       # iPXE BIOS binary
    └── ipxe.efi            # iPXE UEFI binary

/etc/dnsmasq.d/
└── lrn_pxe.conf            # DHCP + TFTP configuration

/etc/nginx/conf.d/
└── lrn_pxe.conf            # nginx virtual host

/etc/systemd/system/
└── lrn-pxe.service         # Flask service unit
```

### Configuration Schema

**menu.json:**
```json
{
  "title": "LRN_PXE Boot Menu",
  "timeout": 60,
  "default": "entry-id",
  "entries": [
    {
      "id":          "rocky9-auto",
      "iso_id":      "Rocky-9.4-x86_64-dvd",
      "label":       "Rocky Linux 9.4 (Auto Install)",
      "os_type":     "rhel",
      "kickstart":   "rocky9-auto.ks",
      "kernel_args": "",
      "enabled":     true
    }
  ]
}
```

**settings.json:**
```json
{
  "server_ip":       "192.168.1.10",
  "web_port":        8080,
  "dhcp_enabled":    true,
  "dhcp_interface":  "eth0",
  "dhcp_start":      "192.168.1.100",
  "dhcp_end":        "192.168.1.200",
  "dhcp_netmask":    "255.255.255.0",
  "dhcp_gateway":    "192.168.1.1",
  "dhcp_dns":        "192.168.1.10",
  "dhcp_lease_time": "12h",
  "version":         "1.0.0"
}
```

---

## REST API Reference

| Method | Endpoint | Description |
|--------|---------|-------------|
| GET | `/menu.ipxe` | Live iPXE boot menu script |
| GET | `/api/status` | Service + disk status |
| GET | `/api/images` | List ISO images |
| POST | `/api/images/upload` | Upload ISO (multipart) |
| DELETE | `/api/images/<id>` | Delete ISO + boot files |
| POST | `/api/images/<id>/extract` | Start boot file extraction |
| GET | `/api/images/<id>/extract/status` | Poll extraction progress |
| GET | `/api/kickstarts` | List kickstart files |
| POST | `/api/kickstarts/upload` | Upload or create kickstart |
| GET | `/api/kickstarts/<name>` | Read kickstart content |
| PUT | `/api/kickstarts/<name>` | Update kickstart content |
| DELETE | `/api/kickstarts/<name>` | Delete kickstart |
| GET | `/api/menu` | Get full menu config |
| PUT | `/api/menu` | Save menu config |
| POST | `/api/menu/entries` | Add menu entry |
| PUT | `/api/menu/entries/<id>` | Update menu entry |
| DELETE | `/api/menu/entries/<id>` | Remove menu entry |
| POST | `/api/menu/reorder` | Reorder entries (JSON array of IDs) |
| GET | `/api/settings` | Get settings |
| PUT | `/api/settings` | Save settings |
| POST | `/api/service/<name>/restart` | Restart a service |

---

## Network Port Requirements

| Port | Proto | Direction | Service | Required |
|------|-------|-----------|---------|---------|
| 67 | UDP | Inbound | DHCP server | Yes |
| 68 | UDP | Outbound | DHCP client responses | Yes |
| 69 | UDP | Inbound | TFTP | Yes |
| 80 | TCP | Inbound | HTTP (nginx) | Yes |
| 8080 | TCP | Inbound | Flask (internal/admin) | Optional |

---

## Supported OS Types for Network Boot

| OS Family | `os_type` Value | Kernel Path | Initrd Path | Boot Param |
|-----------|----------------|-------------|-------------|-----------|
| Rocky / RHEL / AlmaLinux | `rhel` | `images/pxeboot/vmlinuz` | `images/pxeboot/initrd.img` | `inst.repo=` |
| CentOS Stream | `rhel` | `images/pxeboot/vmlinuz` | `images/pxeboot/initrd.img` | `inst.repo=` |
| Fedora | `fedora` | `images/pxeboot/vmlinuz` | `images/pxeboot/initrd.img` | `inst.repo=` |
| Ubuntu | `ubuntu` | `casper/vmlinuz` | `casper/initrd` | `url=` |
| Debian | `debian` | `install.amd/vmlinuz` | `install.amd/initrd.gz` | `url=` |

---

## System Requirements

### Minimum (Lab / Small Environment)

| Resource | Minimum |
|----------|---------|
| OS | Rocky Linux 9.x or 10.x (x86_64) |
| CPU | 2 cores |
| RAM | 2 GB |
| Disk | 50 GB |
| Network | 1 Gbps NIC, static IP |

### Recommended (Production)

| Resource | Recommended |
|----------|-------------|
| OS | Rocky Linux 9.x or 10.x (x86_64) |
| CPU | 4 cores |
| RAM | 8 GB |
| Disk | 500 GB+ (depending on number of ISOs) |
| Network | 10 Gbps NIC for fast deployments |

### Software Dependencies (installed automatically)

```
dnsmasq          # DHCP + TFTP
nginx            # HTTP server
python3          # Runtime for Flask
python3-pip      # Python package manager
python3-venv     # Python virtual environments
gcc / make / perl # iPXE build toolchain
genisoimage       # ISO utilities
curl / wget / rsync # Download tools
firewalld         # Firewall management
```

---

## Security Considerations

| Area | Behavior | Recommendation |
|------|---------|----------------|
| Web UI auth | None (by default) | Restrict port 80/8080 to admin VLAN |
| DHCP scope | Open within configured range | Segment PXE network from production |
| ISO serving | Public (no auth) | Firewall to PXE VLAN only |
| Kickstarts | Public URLs | Avoid storing credentials in kickstarts |
| SELinux | Configured automatically | Leave enforcing |
| Root password in kickstarts | Stored as hash | Use `--iscrypted` and a strong hash |

---

## Performance

| Metric | Value | Notes |
|--------|-------|-------|
| Concurrent PXE clients | 50+ | Limited by DHCP range and network |
| ISO file serving | ~1 Gbps | Limited by NIC and disk I/O |
| Menu generation | < 10 ms | In-memory JSON read |
| TFTP throughput | ~100 MB/s | iPXE binary is ~1 MB |
| Boot time (kernel load) | 5–15 sec | Depends on network speed |

---

## CLI Reference

```
lrn-pxe status              Show service status
lrn-pxe start               Start all services
lrn-pxe stop                Stop all services
lrn-pxe restart             Restart all services
lrn-pxe logs [web|dhcp|http] Tail service logs

lrn-pxe add-iso <path>      Add and extract ISO
lrn-pxe list-isos           List registered ISOs
lrn-pxe remove-iso <id>     Remove ISO and files

lrn-pxe add-kickstart <path> Copy kickstart file
lrn-pxe list-kickstarts     List kickstart files
lrn-pxe edit-kickstart <name> Edit kickstart in $EDITOR

lrn-pxe menu-show           Print live iPXE script
lrn-pxe menu-enable <id>    Enable menu entry
lrn-pxe menu-disable <id>   Disable menu entry

lrn-pxe build-ipxe          Rebuild iPXE binaries
lrn-pxe update-dhcp         Apply DHCP settings
lrn-pxe info                Show configuration
lrn-pxe version             Show version
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-22 | Initial release — BIOS/UEFI boot, web UI, kickstart support, CLI tool |

---

*LRN_PXE is built on iPXE (bd13697), dnsmasq, nginx, Flask, and Bootstrap 5.*
