# MAC Ops RPM Installation Guide

## Overview

This guide covers installation of Maytag Admin Console (MAC) on Rocky Linux 9.x systems using the RPM package.

## Prerequisites

- Rocky Linux 9.3 or later
- 2+ vCPU, 2GB RAM (4GB recommended)
- 10GB free disk space (20GB recommended)
- Root or sudo access
- Internet access (for initial setup)

## Installation Steps

### 1. Install the RPM Package

```bash
# Transfer the RPM to your target system
scp mac-ops-2.0.0-1.el9.noarch.rpm root@your-server:/tmp/

# On the target system, install with dependencies
sudo dnf install -y /tmp/mac-ops-2.0.0-1.el9.noarch.rpm

# Verify installation
rpm -ql mac-ops | head -20
```

### 2. Post-Installation Setup

The RPM automatically:
- Creates the `macops` service user
- Creates required directories
- Sets correct permissions
- Installs the systemd service

#### Install Python dependencies

```bash
# The RPM includes a post-install hook that installs Python packages
# Monitor progress
sudo tail -f /opt/mac-ops/logs/mac-ops.log

# Manual install (if needed)
sudo -u macops /home/macops/.venv/bin/pip install -r /opt/mac-ops/backend/requirements.txt
```

#### Deploy SSH Key for Ansible

```bash
# Generate SSH key for automation (if not already present)
sudo -u macops ssh-keygen -t ed25519 -f /home/macops/.ssh/ansible_key -N ""

# Add to managed hosts
cat /home/macops/.ssh/ansible_key.pub
# Add this key to ~/.ssh/authorized_keys on all managed hosts
```

### 3. Enable and Start the Service

```bash
# Enable on boot
sudo systemctl enable mac-ops

# Start the service
sudo systemctl start mac-ops

# Check status
sudo systemctl status mac-ops

# View logs
sudo journalctl -u mac-ops -f
```

### 4. Verify Installation

```bash
# Check if service is running
sudo systemctl is-active mac-ops
# Output: active

# Test web interface
curl -k https://localhost:5000/ | grep -o '<title>.*</title>'
# Output: <title>mac-ops — Maytag Ansible Console v1.1.0</title>

# Check listening port
sudo ss -tlnp | grep 5000
# Output: LISTEN  0  128  0.0.0.0:5000  0.0.0.0:*  users:(("python",pid=XXXX,fd=X))
```

### 5. Access the Web Console

Open your browser and navigate to:
```
http://your-server-ip:5000/
```

Default paths:
- **Dashboard**: `http://your-server:5000/`
- **SSH Console**: `http://your-server:5000/ssh-console`
- **Ad-hoc Runner**: `http://your-server:5000/adhoc`
- **Host Checker**: `http://your-server:5000/hostcheck`

## File Locations

| Path | Purpose |
|------|---------|
| `/opt/mac-ops/` | Application root |
| `/opt/mac-ops/backend/` | Flask API server |
| `/opt/mac-ops/frontend/` | Web UI assets |
| `/opt/mac-ops/ansible/playbooks/` | Ansible playbooks |
| `/opt/mac-ops/ansible/inventory/` | Host inventory files |
| `/var/lib/mac-ops/` | Runtime data (DB, schedules) |
| `/opt/mac-ops/reports/` | Generated reports |
| `/opt/mac-ops/logs/` | Application logs |
| `/home/macops/.ssh/` | Ansible SSH keys |
| `/home/macops/.venv/` | Python virtual environment |
| `/usr/lib/systemd/system/mac-ops.service` | Systemd service file |

## Service Management

```bash
# Start
sudo systemctl start mac-ops

# Stop
sudo systemctl stop mac-ops

# Restart
sudo systemctl restart mac-ops

# Check status
sudo systemctl status mac-ops

# View logs (last 50 lines)
sudo journalctl -u mac-ops -n 50

# Watch logs in real-time
sudo journalctl -u mac-ops -f

# View app logs directly
sudo tail -f /opt/mac-ops/logs/mac-ops.log
```

## Security Hardening

### 1. TLS/HTTPS Setup (Recommended)

Place MAC Ops behind Nginx with TLS:

```bash
# Install Nginx and certbot
sudo dnf install -y nginx python3-certbot-nginx

# Create Nginx config
sudo tee /etc/nginx/conf.d/mac-ops.conf > /dev/null <<EOF
upstream mac_ops_backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://mac_ops_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Generate TLS certificate
sudo certbot --nginx -d your-domain.com

# Enable Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Disable direct access on port 5000
sudo firewall-cmd --permanent --remove-port=5000/tcp
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. Firewall Configuration

```bash
# Allow HTTP/HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Restrict SSH access if needed
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.0.0.0/8" service name="ssh" accept'
```

### 3. SELinux (if enabled)

```bash
# Label port 5000 as HTTP
sudo semanage port -a -t http_port_t -p tcp 5000

# Or allow MAC Ops context
sudo semanage fcontext -a -t httpd_exec_t '/opt/mac-ops(/.*)?'
sudo restorecon -Rv /opt/mac-ops
```

## Upgrading

```bash
# Stop the service
sudo systemctl stop mac-ops

# Backup current installation
sudo cp -r /opt/mac-ops /opt/mac-ops.backup

# Backup data
sudo cp -r /var/lib/mac-ops /var/lib/mac-ops.backup

# Install new RPM
sudo dnf install -y /tmp/mac-ops-2.0.0-1.el9.noarch.rpm

# Restart service
sudo systemctl restart mac-ops

# Verify
sudo systemctl status mac-ops
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u mac-ops -n 50 --no-pager

# Check Python errors
/home/macops/.venv/bin/python /opt/mac-ops/backend/app.py

# Verify permissions
ls -la /opt/mac-ops
ls -la /var/lib/mac-ops
```

### Cannot Connect to Web UI

```bash
# Verify port is listening
sudo ss -tlnp | grep 5000

# Check firewall
sudo firewall-cmd --list-all

# Check if process is running
ps aux | grep "[p]ython.*app.py"
```

### Permission Errors

```bash
# Reset ownership
sudo chown -R macops:macops /opt/mac-ops
sudo chown -R macops:macops /var/lib/mac-ops
sudo chown -R macops:macops /home/macops

# Reset permissions
sudo chmod -R 755 /opt/mac-ops
sudo chmod -R 700 /var/lib/mac-ops
```

### Database Issues

```bash
# Backup existing DB
sudo -u macops cp /var/lib/mac-ops/mac.db /var/lib/mac-ops/mac.db.backup

# Reinitialize DB (if safe to do)
sudo systemctl stop mac-ops
sudo -u macops rm /var/lib/mac-ops/mac.db
sudo systemctl start mac-ops
```

## Uninstallation

```bash
# Stop service
sudo systemctl stop mac-ops

# Remove package
sudo dnf remove -y mac-ops

# Clean up data (optional)
sudo rm -rf /opt/mac-ops
sudo rm -rf /var/lib/mac-ops
sudo rm -rf /home/macops
```

## Building from Source

To rebuild the RPM:

```bash
# Install rpmbuild
sudo dnf install -y rpm-build

# Setup build environment
mkdir -p ~/rpmbuild/{SPECS,SOURCES,BUILD,RPMS,SRPMS}

# Copy spec file
cp mac-ops.spec ~/rpmbuild/SPECS/

# Create source tarball
tar -czf ~/rpmbuild/SOURCES/mac-ops-2.0.0.tar.gz mac-ops/

# Build RPM
rpmbuild -bb ~/rpmbuild/SPECS/mac-ops.spec

# Result will be in ~/rpmbuild/RPMS/noarch/
```

## Support

For issues, documentation, and support:
- See `/opt/mac-ops/README.md`
- See `/opt/mac-ops/DEPLOYMENT.md`
- Check logs: `sudo journalctl -u mac-ops -f`

