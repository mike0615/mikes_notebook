# LRN_PXE User Guide

**Version 1.0.0 | Rocky Linux 9/10**

---

## Table of Contents

1. [What is LRN_PXE?](#1-what-is-lrn_pxe)
2. [How PXE Booting Works](#2-how-pxe-booting-works)
3. [Installation](#3-installation)
4. [Accessing the Web Interface](#4-accessing-the-web-interface)
5. [Adding a Boot Image (ISO)](#5-adding-a-boot-image-iso)
6. [Creating or Uploading Kickstart Files](#6-creating-or-uploading-kickstart-files)
7. [Building the Boot Menu](#7-building-the-boot-menu)
8. [PXE Booting a Client Machine](#8-pxe-booting-a-client-machine)
9. [Using the CLI Tool](#9-using-the-cli-tool)
10. [Managing Services](#10-managing-services)
11. [Network Configuration Reference](#11-network-configuration-reference)

---

## 1. What is LRN_PXE?

LRN_PXE is a self-contained network boot server that allows you to install operating systems on multiple machines over a network — without USB drives or DVDs.

**What you get:**
- A **web interface** to manage everything through your browser
- **DHCP server** to assign IP addresses to booting clients
- **TFTP server** to deliver the iPXE boot image
- **HTTP server** to serve ISO contents, kernels, and kickstart files
- **Automatic menu generation** — the PXE menu updates instantly when you make changes

**Supported OS types for network installation:**
- Rocky Linux 9 / 10
- RHEL 9 / 10
- AlmaLinux 9
- CentOS Stream 9
- Fedora (recent releases)
- Ubuntu 22.04 / 24.04
- Debian 12

---

## 2. How PXE Booting Works

Understanding the boot flow helps when troubleshooting:

```
Client powers on with PXE enabled
         │
         ▼
DHCP Request (broadcast)
         │
         ▼ LRN_PXE (dnsmasq)
DHCP Reply — IP address + "boot from TFTP at <server-ip>"
         │
         ▼
TFTP Download of iPXE binary
  • BIOS machines  → undionly.kpxe
  • UEFI machines  → ipxe.efi
         │
         ▼
iPXE starts, fetches menu from:
  http://<server-ip>/menu.ipxe
         │
         ▼
User selects a boot option
         │
         ▼
iPXE downloads kernel + initrd over HTTP
         │
         ▼
Installer starts — reads ISO from http://<server-ip>/mounts/<iso-id>/
  (Optionally reads kickstart from http://<server-ip>/kickstarts/<file>)
         │
         ▼
Installation completes — machine reboots
```

---

## 3. Installation

### Requirements

| Component | Minimum |
|-----------|---------|
| OS | Rocky Linux 9.x or 10.x |
| RAM | 2 GB |
| CPU | 2 cores |
| Disk | 50 GB (more for ISOs) |
| Network | Static IP on a dedicated PXE network segment |

> **Important:** The LRN_PXE DHCP server must be the **only** DHCP server on the network segment. Running two DHCP servers will cause conflicts.

### Step-by-Step Installation

**1. Copy or clone the files to your Rocky Linux server:**
```bash
scp -r lrn_pxe/ admin@192.168.1.10:/tmp/
```

**2. SSH into the server:**
```bash
ssh admin@192.168.1.10
cd /tmp/lrn_pxe
```

**3. Run the installer as root:**
```bash
sudo bash install.sh
```

**4. Answer the prompts:**

The installer will detect your network settings and show defaults. Press Enter to accept or type new values:

```
PXE Server IP Address [192.168.1.10]:
Network Interface [eth0]:
DHCP Range Start [192.168.1.100]:
DHCP Range End [192.168.1.200]:
Subnet Mask [255.255.255.0]:
Default Gateway [192.168.1.10]:
DNS Server [192.168.1.10]:
Management Web UI Port [8080]:
```

**5. Wait for installation to complete (~5-10 minutes for iPXE build)**

The installer will:
- Install required packages
- Build iPXE from the bundled source
- Configure dnsmasq, nginx, and Flask
- Start all services
- Open the firewall ports

**6. Access the web interface:**
```
http://192.168.1.10/
```

---

## 4. Accessing the Web Interface

Open a browser and navigate to your server's IP address:
```
http://<your-server-ip>/
```

The interface has five sections:

| Section | Purpose |
|---------|---------|
| **Dashboard** | Overview of services, statistics, and server info |
| **Boot Images** | Upload and manage ISO files |
| **Kickstarts** | Create and manage automated install scripts |
| **Menu Builder** | Configure what clients see when they PXE boot |
| **Settings** | Network and DHCP configuration |

---

## 5. Adding a Boot Image (ISO)

### Via Web Interface (Recommended)

1. Click **Boot Images** in the sidebar
2. Click **Add Image**
3. Drag and drop your ISO file, or click to browse
4. Wait for the upload to complete
5. Click **Extract Boot Files** — this pulls the kernel and initrd from the ISO
6. Once extraction is complete (green "Ready" badge), click **Add to Menu**

### Via CLI

```bash
sudo lrn-pxe add-iso /path/to/Rocky-9.4-x86_64-dvd.iso
```

### Via SSH (large files)

For very large ISOs, it's faster to copy directly to the server:
```bash
# From your workstation:
rsync -avP Rocky-9.4-x86_64-dvd.iso admin@192.168.1.10:/opt/lrn_pxe/isos/

# On the server:
sudo lrn-pxe add-iso /opt/lrn_pxe/isos/Rocky-9.4-x86_64-dvd.iso
```

> **Note:** After copying an ISO directly, you still need to extract boot files. Use the web interface or run `lrn-pxe add-iso <path>` to trigger extraction.

---

## 6. Creating or Uploading Kickstart Files

A kickstart file automates the entire OS installation — no prompts, no clicking.

### Create a New Kickstart

1. Click **Kickstarts** in the sidebar
2. Click **New Kickstart**
3. Enter a filename (e.g., `rocky9-webserver.ks`)
4. Type or paste your kickstart content
5. Click **Save**

Or use the built-in templates:
- Click **Load Rocky 9 Template** or **Load Ubuntu Template**
- Modify the template for your environment
- Save with a descriptive name

### Upload an Existing Kickstart

1. Click **Kickstarts → Upload**
2. Drop your `.ks` or `.cfg` file

### Kickstart Template Variables to Change

When using the provided templates, update at minimum:

```kickstart
# Change the root password hash
rootpw --iscrypted $6$CHANGEME

# Change the user and password
user --name=admin --groups=wheel --password=changeme

# Change timezone
timezone America/New_York --utc

# Update the repo URL to match your server IP
url --url="http://192.168.1.10/mounts/rocky9/"
```

---

## 7. Building the Boot Menu

The Menu Builder controls what clients see when they PXE boot.

### Adding a Menu Entry

1. Click **Menu Builder** in the sidebar
2. In the **Add Menu Entry** panel (left side):
   - Select a **Boot Image** from the dropdown
   - Enter a **Display Label** (this is what the user sees)
   - Optionally select a **Kickstart File**
   - Select the **OS Type**
3. Click **Add to Menu**

### Example Setup — Two Options for Rocky Linux 9

| Label | Image | Kickstart | What it does |
|-------|-------|-----------|-------------|
| Rocky Linux 9.4 (Auto Install) | Rocky-9.4-x86_64-dvd | rocky9-auto.ks | Fully automated, no user input |
| Rocky Linux 9.4 (Interactive) | Rocky-9.4-x86_64-dvd | (none) | Opens the graphical installer |

### Reordering Entries

Drag menu items by the grip handle (⠿) on the left to change their order.

### Enabling / Disabling Entries

Toggle the switch on the right of each entry to show or hide it in the boot menu.

### Setting a Default

In **Menu Settings**, set the **Default Selection** and **Auto-boot Timeout**. After the timeout, the default entry boots automatically.

---

## 8. PXE Booting a Client Machine

### Client Requirements

- Machine must support network booting (PXE or iPXE)
- Network card must be on the same network segment as the LRN_PXE server
- Boot order must have "Network" before "Hard Disk"

### Enabling PXE Boot in BIOS/UEFI

The exact steps vary by manufacturer, but generally:

1. Restart the client machine
2. Press **F2**, **F10**, **F12**, **Del**, or **Esc** to enter BIOS/UEFI
3. Navigate to **Boot** settings
4. Move **Network Boot** or **PXE Boot** to the top of the boot order
5. Save and exit

### What You'll See

1. Machine boots and gets a DHCP address from LRN_PXE
2. iPXE loads and fetches the menu
3. The **LRN_PXE Boot Menu** appears with your configured options
4. Select an option (or wait for the default to auto-boot)
5. Installation begins

### BIOS vs. UEFI

LRN_PXE supports both:
- **BIOS/Legacy** clients receive `undionly.kpxe`
- **UEFI** clients receive `ipxe.efi`

This detection is automatic — no configuration needed.

---

## 9. Using the CLI Tool

The `lrn-pxe` CLI tool is available on the server after installation:

```bash
lrn-pxe help                      # Show all commands
lrn-pxe status                    # Check service status
lrn-pxe add-iso /path/to/os.iso   # Add and process an ISO
lrn-pxe list-isos                 # List all images
lrn-pxe add-kickstart /path/to.ks # Add a kickstart
lrn-pxe list-kickstarts           # List kickstarts
lrn-pxe edit-kickstart rocky9.ks  # Edit a kickstart
lrn-pxe menu-enable rocky9-auto   # Enable a menu entry
lrn-pxe menu-disable rocky9-auto  # Disable a menu entry
lrn-pxe menu-show                 # View live iPXE script
lrn-pxe logs                      # Tail web UI logs
lrn-pxe logs dhcp                 # Tail DHCP logs
lrn-pxe restart                   # Restart all services
lrn-pxe info                      # Show configuration summary
```

---

## 10. Managing Services

Three services run as part of LRN_PXE:

| Service | Role | Manage with |
|---------|------|-------------|
| `lrn-pxe` | Flask web UI + iPXE menu API | `systemctl restart lrn-pxe` |
| `dnsmasq` | DHCP + TFTP server | `systemctl restart dnsmasq` |
| `nginx` | HTTP file server (ISOs, boot files) | `systemctl restart nginx` |

### Useful Commands

```bash
# Check all service status
lrn-pxe status

# View logs
journalctl -u lrn-pxe -f        # Web UI logs
tail -f /var/log/dnsmasq.log     # DHCP/TFTP activity
tail -f /var/log/nginx/lrn_pxe_access.log  # HTTP access

# Restart everything
lrn-pxe restart

# Check DHCP leases (clients that have received addresses)
cat /var/lib/dnsmasq/dnsmasq.leases
```

---

## 11. Network Configuration Reference

### Firewall Ports

The installer opens these ports automatically:

| Port | Protocol | Service | Purpose |
|------|----------|---------|---------|
| 67 | UDP | DHCP | IP address assignment |
| 69 | UDP | TFTP | iPXE binary delivery |
| 80 | TCP | HTTP | ISO, boot files, web UI |
| 8080 | TCP | HTTP | Flask direct (internal) |

### Directory Reference

| Path | Contents |
|------|---------|
| `/opt/lrn_pxe/isos/` | ISO files |
| `/opt/lrn_pxe/kickstarts/` | Kickstart files |
| `/opt/lrn_pxe/boot/<iso-id>/` | Extracted vmlinuz + initrd |
| `/opt/lrn_pxe/mounts/<iso-id>/` | Mounted ISO (served as install repo) |
| `/opt/lrn_pxe/config/menu.json` | Menu configuration |
| `/opt/lrn_pxe/config/settings.json` | Server settings |
| `/var/lib/tftpboot/ipxe/` | iPXE boot binaries |
| `/etc/dnsmasq.d/lrn_pxe.conf` | DHCP/TFTP config |
| `/etc/nginx/conf.d/lrn_pxe.conf` | HTTP server config |

### URL Reference

| URL | What it serves |
|-----|---------------|
| `http://<server>/` | Web management interface |
| `http://<server>/menu.ipxe` | Live iPXE boot menu script |
| `http://<server>/isos/` | Raw ISO file downloads |
| `http://<server>/boot/<id>/vmlinuz` | Kernel image |
| `http://<server>/boot/<id>/initrd.img` | Initial RAM disk |
| `http://<server>/mounts/<id>/` | ISO contents (install repo) |
| `http://<server>/kickstarts/<file>` | Kickstart file |
