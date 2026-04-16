# LRN_PXE Troubleshooting Guide

---

## Quick Diagnostics

Run this first to see what's wrong:

```bash
lrn-pxe status
journalctl -u lrn-pxe --no-pager -n 30
tail -20 /var/log/dnsmasq.log
```

---

## Problem: Client Gets No DHCP Address

**Symptoms:** Client shows "No boot filename received" or "PXE-E16: No offer received"

**Checks:**
```bash
# Is dnsmasq running?
systemctl status dnsmasq

# Is dnsmasq listening on the right interface?
ss -ulnp | grep :67

# Check for DHCP conflicts (other DHCP servers on the network)
nmap --script broadcast-dhcp-discover -e eth0

# View DHCP log for errors
tail -50 /var/log/dnsmasq.log
```

**Common fixes:**
1. Verify the network interface in Settings matches your actual NIC (`ip link show`)
2. Ensure no other DHCP server is on the same subnet
3. Check that `firewall-cmd --list-services` includes `dhcp`
4. If the interface name changed, update `/etc/dnsmasq.d/lrn_pxe.conf` and restart dnsmasq

---

## Problem: Client Gets IP But Can't Download iPXE

**Symptoms:** Client shows "PXE-E32: TFTP open timeout" or "TFTP error"

**Checks:**
```bash
# Is TFTP available?
systemctl status dnsmasq  # dnsmasq provides TFTP
ls /var/lib/tftpboot/ipxe/  # Should show undionly.kpxe and ipxe.efi

# Test TFTP from another machine on the network
tftp 192.168.1.10
get ipxe/undionly.kpxe
```

**Common fixes:**
1. Verify iPXE binaries exist in `/var/lib/tftpboot/ipxe/`
2. Rebuild if missing: `sudo lrn-pxe build-ipxe`
3. Check firewall: `firewall-cmd --list-services` — should include `tftp`
4. Check SELinux: `ausearch -m avc -ts recent | grep tftp`

---

## Problem: iPXE Loads But Can't Fetch Menu

**Symptoms:** iPXE loads, shows version string, then "Could not boot" or HTTP error

**Checks:**
```bash
# Is nginx running?
systemctl status nginx

# Can the server reach itself?
curl -s http://localhost/menu.ipxe | head -5

# Is Flask running?
systemctl status lrn-pxe
curl -s http://localhost:8080/menu.ipxe | head -5

# Check nginx error log
tail -20 /var/log/nginx/lrn_pxe_error.log
```

**Common fixes:**
1. Restart Flask: `systemctl restart lrn-pxe`
2. Check Flask logs: `journalctl -u lrn-pxe -n 50`
3. Verify port 80 is open: `firewall-cmd --list-ports`
4. Check that the server IP in `settings.json` matches the actual IP clients use

---

## Problem: Menu Shows But Kernel Download Fails

**Symptoms:** Menu appears, user selects option, then "Could not fetch kernel" or HTTP 404

**Checks:**
```bash
# Do boot files exist for the image?
ls /opt/lrn_pxe/boot/<iso-id>/
# Should show: vmlinuz  initrd.img

# Can nginx serve the boot file?
curl -I http://localhost/boot/<iso-id>/vmlinuz

# Is the ISO mounted?
ls /opt/lrn_pxe/mounts/<iso-id>/
mountpoint /opt/lrn_pxe/mounts/<iso-id>
```

**Common fixes:**
1. Re-extract boot files: go to **Boot Images** in the web UI and click **Extract Boot Files**
2. Re-mount the ISO:
   ```bash
   mount -o loop,ro /opt/lrn_pxe/isos/<name>.iso /opt/lrn_pxe/mounts/<id>/
   ```
3. Add a persistent mount to `/etc/fstab`:
   ```
   /opt/lrn_pxe/isos/Rocky-9.4-x86_64-dvd.iso /opt/lrn_pxe/mounts/Rocky-9.4-x86_64-dvd iso9660 loop,ro 0 0
   ```

---

## Problem: Installer Can't Find Repo / inst.repo Error

**Symptoms:** Installer starts but fails with "Unable to find install media" or "Couldn't find repository"

**Checks:**
```bash
# Is the ISO mounted and accessible?
curl -I http://192.168.1.10/mounts/<iso-id>/.treeinfo
# Should return HTTP 200

# Check nginx can list the directory
curl http://192.168.1.10/mounts/<iso-id>/ | head -20
```

**Common fixes:**
1. Ensure the ISO is mounted (not just the directory existing)
2. For RHEL-based ISOs, the `.treeinfo` file must be accessible at the repo root
3. Check SELinux contexts:
   ```bash
   chcon -Rt httpd_sys_content_t /opt/lrn_pxe/mounts/
   ```

---

## Problem: Kickstart Not Being Applied

**Symptoms:** Installer prompts for input even though kickstart is configured

**Checks:**
```bash
# Is the kickstart file accessible?
curl http://192.168.1.10/kickstarts/rocky9-auto.ks | head -10

# Check menu.json for correct kickstart entry
cat /opt/lrn_pxe/config/menu.json | python3 -m json.tool | grep kickstart

# View live iPXE menu to confirm ks= parameter is present
lrn-pxe menu-show | grep inst.ks
```

**Common fixes:**
1. Verify the kickstart filename in the Menu Builder matches exactly (case-sensitive)
2. Check kickstart file syntax:
   ```bash
   ksvalidator /opt/lrn_pxe/kickstarts/rocky9-auto.ks
   ```
3. Ensure the kickstart file ends with `reboot` or `poweroff`

---

## Problem: Web Interface Not Loading

**Symptoms:** Browser shows "Connection refused" or blank page

**Checks:**
```bash
# Is Flask running?
systemctl status lrn-pxe

# Is nginx running?
systemctl status nginx

# What's on port 80?
ss -tlnp | grep :80

# Flask logs
journalctl -u lrn-pxe -n 50 --no-pager
```

**Common fixes:**
```bash
# Restart everything
systemctl restart lrn-pxe nginx

# If Flask crashes on start, check for Python errors
/opt/lrn_pxe/venv/bin/python /opt/lrn_pxe/web/app.py
```

---

## Problem: Large ISO Upload Times Out

**Symptoms:** Upload progress stops at some percentage and fails

**Fix** — Increase nginx timeout:
```bash
# Edit nginx config
nano /etc/nginx/conf.d/lrn_pxe.conf

# Add inside the location / block:
proxy_read_timeout 3600;
proxy_send_timeout 3600;

# Also increase client_max_body_size if needed:
client_max_body_size 100G;

nginx -t && systemctl reload nginx
```

**Alternative** — Copy large ISOs directly via SCP/rsync:
```bash
rsync -avP Rocky-9.4-x86_64-dvd.iso admin@192.168.1.10:/opt/lrn_pxe/isos/
```

---

## Problem: UEFI Clients Boot BIOS Image (or vice versa)

**Symptoms:** UEFI machine gets `undionly.kpxe` and fails

**Check:**
```bash
tail -f /var/log/dnsmasq.log | grep -E "arch|DHCPACK"
```

**Fix** — Verify dnsmasq config has both arch matches:
```bash
grep -A2 "client-arch" /etc/dnsmasq.d/lrn_pxe.conf
```
Should show entries for arch 7 (UEFI) and the fallback (BIOS).

---

## Resetting to Factory Defaults

```bash
# Stop all services
systemctl stop lrn-pxe dnsmasq nginx

# Clear all data (DESTRUCTIVE)
rm -rf /opt/lrn_pxe/isos/*
rm -rf /opt/lrn_pxe/kickstarts/*
rm -rf /opt/lrn_pxe/boot/*
rm -rf /opt/lrn_pxe/mounts/*

# Reset config
cat > /opt/lrn_pxe/config/menu.json << 'EOF'
{"title":"LRN_PXE Boot Menu","timeout":60,"default":"","entries":[]}
EOF

# Restart
systemctl start lrn-pxe dnsmasq nginx
```

---

## Log File Reference

| Log | Location | What it shows |
|-----|---------|---------------|
| Web UI | `journalctl -u lrn-pxe` | Flask errors, API calls |
| Web UI (file) | `/opt/lrn_pxe/logs/web.log` | Application output |
| DHCP/TFTP | `/var/log/dnsmasq.log` | DHCP leases, TFTP transfers |
| nginx access | `/var/log/nginx/lrn_pxe_access.log` | All HTTP requests |
| nginx error | `/var/log/nginx/lrn_pxe_error.log` | nginx errors |
| Install log | `/var/log/lrn_pxe_install.log` | Installation output |

---

## Getting More Help

1. Check the logs first (see above)
2. View the live iPXE menu: `lrn-pxe menu-show`
3. Test HTTP reachability: `curl -v http://localhost/menu.ipxe`
4. File an issue at the repository with relevant log output
