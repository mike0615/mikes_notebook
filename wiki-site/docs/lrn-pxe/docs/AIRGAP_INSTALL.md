# LRN_PXE Airgapped / Offline Installation Guide

This guide covers installing LRN_PXE on a **Rocky Linux 9/10 server with no internet access**.

---

## Overview

The offline install process has three phases:

```
PHASE 1 — Internet Machine      PHASE 2 — Transfer         PHASE 3 — Target Server
─────────────────────────       ──────────────             ─────────────────────────
fetch-bundle.sh                 SCP / USB / share          install-offline.sh
  ↓ downloads:                     tarball →                 ↓ installs from:
  • RPM packages                                             • bundle/rpms/
  • Python wheels                                            • bundle/pip-wheels/
  • iPXE binaries                                            • bundle/ipxe/
  • Bootstrap assets                                         • bundle/vendor/
  ↓
create-airgap-package.sh
  ↓
lrn_pxe_offline_v1.0.0.tar.gz
```

---

## Step 1 — Prepare the Bundle (Internet-Connected Machine)

You need a Rocky Linux 9 or 10 machine **with internet access** to build the bundle. This can be a laptop, VM, or any machine — it does not need to be the final PXE server.

### Install prerequisites

```bash
sudo dnf install -y createrepo_c python3-pip rsync
```

### Download the LRN_PXE repository

```bash
# If you have git:
git clone https://github.com/your-org/mac-ops.git
cd mac-ops/lrn_pxe

# Or copy the lrn_pxe/ folder to the machine by USB/share
```

### Run the bundle fetcher

```bash
sudo bash fetch-bundle.sh
```

This downloads and saves locally:
- All required RPM packages + their dependencies
- Python wheels (Flask, flask-cors, and all transitive deps)
- Pre-built iPXE BIOS and UEFI binaries
- Bootstrap 5 CSS/JS and Bootstrap Icons CSS/fonts

> This may take 5–15 minutes and will use approximately **300–600 MB** of disk space.

### Create the distributable package

```bash
bash create-airgap-package.sh
```

This produces `lrn_pxe_offline_v1.0.0.tar.gz` in the parent directory and a `.sha256` checksum file.

---

## Step 2 — Transfer to the Target Server

Transfer the tarball to your airgapped Rocky Linux server via any available method:

### Option A — SCP (if you have a jump host or brief network access)

```bash
scp lrn_pxe_offline_v1.0.0.tar.gz admin@192.168.1.10:/tmp/
scp lrn_pxe_offline_v1.0.0.tar.gz.sha256 admin@192.168.1.10:/tmp/
```

### Option B — USB drive

```bash
# Copy to USB (on internet machine)
cp lrn_pxe_offline_v1.0.0.tar.gz /media/usb/
cp lrn_pxe_offline_v1.0.0.tar.gz.sha256 /media/usb/

# Mount USB on target server and copy
mount /dev/sdb1 /mnt/usb
cp /mnt/usb/lrn_pxe_offline_v1.0.0.tar.gz /tmp/
```

### Option C — NFS / SMB share

Copy to a shared network drive accessible from the target server.

### Verify the checksum

On the target server, before installing:

```bash
cd /tmp
sha256sum -c lrn_pxe_offline_v1.0.0.tar.gz.sha256
# Should output: lrn_pxe_offline_v1.0.0.tar.gz: OK
```

---

## Step 3 — Install on the Target Server

On the **airgapped Rocky Linux 9/10 target**:

```bash
cd /tmp
tar -xzf lrn_pxe_offline_v1.0.0.tar.gz
cd lrn_pxe_offline_v1.0.0
sudo bash lrn_pxe/install-offline.sh
```

The installer will:
1. Validate the bundle directory is present and complete
2. Auto-detect your network interface and IP
3. Prompt for DHCP range and other settings
4. Install all RPMs from `bundle/rpms/` (no internet calls)
5. Install Flask from `bundle/pip-wheels/` (no internet calls)
6. Copy or build iPXE binaries
7. Install Bootstrap assets into the web app's static directory
8. Configure and start all services

---

## What Goes Into the Bundle

| Directory | Contents | Approximate Size |
|-----------|---------|-----------------|
| `bundle/rpms/` | dnsmasq, nginx, python3, gcc, make, perl, and all dependencies as RPMs | 150–300 MB |
| `bundle/pip-wheels/` | Flask, flask-cors, click, jinja2, werkzeug, and all dependencies | 5–10 MB |
| `bundle/ipxe/` | Pre-built `undionly.kpxe` (BIOS) and `ipxe.efi` (UEFI) | ~2 MB |
| `bundle/vendor/` | Bootstrap 5.3.3 CSS+JS, Bootstrap Icons 1.11.3 CSS+fonts | ~5 MB |

---

## Offline Web UI

After installing in offline mode, the web UI uses the **bundled Bootstrap and Bootstrap Icons** stored in `/opt/lrn_pxe/web/static/vendor/`. There are no external CDN requests at runtime.

The templates use a graceful fallback strategy:
- First, load from `/static/vendor/bootstrap.min.css`
- If that fails (file missing), fall back to the CDN

This means the system will work even if the vendor files are somehow missing — as long as the client browser has internet access.

---

## Updating the Bundle

If you need to update RPMs or Python packages after initial install:

```bash
# On the airgapped server — apply RPM updates from a new bundle
sudo dnf localinstall --disablerepo='*' /path/to/new/rpms/*.rpm

# Update Python packages from new wheels
sudo /opt/lrn_pxe/venv/bin/pip install \
  --no-index \
  --find-links=/path/to/new/wheels \
  flask flask-cors --upgrade
```

---

## Troubleshooting the Offline Install

### "bundle/rpms/ missing" or "bundle/ not found"

The bundle directory was not found alongside `install-offline.sh`. This means either:
- The tarball was extracted incorrectly — re-extract with `tar -xzf ...`
- The bundle fetcher wasn't run — you need to run `fetch-bundle.sh` on an internet machine first

### RPM install fails with "no package in repos"

Some packages may not have been captured in the bundle (dependency of a dependency).

**Fix:** On the internet machine, re-run `fetch-bundle.sh` which uses `--alldeps` to capture the full dependency tree. Then re-create and re-transfer the package.

### Flask install fails: "no matching distribution found"

The pip wheels may not be compatible with the Python version on the target system.

**Fix:** Run `fetch-bundle.sh` on a machine with the **same Python version** as the target (both should be Rocky 9 with Python 3.9, or Rocky 10 with Python 3.11).

### Web UI loads but CSS looks broken

The vendor assets may not have been copied correctly. Check:

```bash
ls /opt/lrn_pxe/web/static/vendor/
# Should show: bootstrap.min.css  bootstrap.bundle.min.js  bootstrap-icons.min.css  fonts/

# Fix by manually copying from bundle:
cp -r /path/to/bundle/vendor/. /opt/lrn_pxe/web/static/vendor/
systemctl restart lrn-pxe
```

---

## Security Notes

- The RPM bundle uses `gpgcheck=0` on the temporary local repo. This is safe because you are installing your own pre-downloaded packages — but re-enable GPG checking if your security policy requires it.
- The bundle does not include any credentials, secrets, or certificates.
- After installation, remove the bundle tarball from the target server if disk space is a concern — it is not needed for operation.

```bash
rm -f /tmp/lrn_pxe_offline_v1.0.0.tar.gz
```
