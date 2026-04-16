# Maytag Admin Console - Deployment Guide

## Production Deployment

### System Requirements

- **OS:** Rocky Linux 9.x or compatible
- **Python:** 3.9 or higher
- **Database:** SQLite (included) or PostgreSQL
- **Memory:** 2GB minimum
- **Disk:** 5GB minimum
- **Network:** HTTPS/TLS required

### Pre-deployment Checklist

- [ ] System meets requirements
- [ ] Firewall configured for port 443 (HTTPS)
- [ ] DNS records configured
- [ ] SSL/TLS certificates obtained
- [ ] Database backup strategy planned
- [ ] LDAP/FreeIPA configuration ready (if using)
- [ ] Secrets backup procedures documented
- [ ] Logging and monitoring configured

### Step 1: System Preparation

```bash
# Create service user
sudo useradd -m -s /bin/bash mac-ops

# Create directories
sudo mkdir -p /opt/mac-ops
sudo mkdir -p /var/lib/mac-ops
sudo mkdir -p /etc/mac-ops
sudo mkdir -p /var/log/mac-ops

# Set permissions
sudo chown -R mac-ops:mac-ops /opt/mac-ops
sudo chown -R mac-ops:mac-ops /var/lib/mac-ops
sudo chown -R mac-ops:mac-ops /etc/mac-ops
sudo chown -R mac-ops:mac-ops /var/log/mac-ops

sudo chmod 755 /opt/mac-ops
sudo chmod 700 /var/lib/mac-ops
sudo chmod 700 /etc/mac-ops
sudo chmod 700 /var/log/mac-ops
```

### Step 2: Install Dependencies

```bash
# Install system packages
sudo dnf install -y python3-pip python3-devel
sudo dnf install -y openldap-devel openldap-clients
sudo dnf install -y gcc libffi-devel

# Copy application
cd /opt/mac-ops
sudo -u mac-ops git clone <repo-url> .

# Install Python dependencies
sudo -u mac-ops python3 -m pip install -r backend/requirements.txt
```

### Step 3: Configuration

Create `/etc/mac-ops/mac.conf`:

```ini
[database]
url = sqlite:////var/lib/mac-ops/mac.db

[auth]
session_timeout = 1800

[ldap]
enabled = false
server = ldap.example.com
port = 389
use_tls = true
base_dn = dc=example,dc=com
user_dn_template = uid={username},cn=users,cn=accounts,dc=example,dc=com
```

Set permissions:
```bash
sudo chmod 600 /etc/mac-ops/mac.conf
sudo chown mac-ops:mac-ops /etc/mac-ops/mac.conf
```

### Step 4: Initialize Database

```bash
sudo -u mac-ops python3 backend/manage.py init-db
sudo -u mac-ops python3 backend/manage.py create-admin
```

### Step 5: SSL/TLS Configuration

```bash
# Copy certificates
sudo cp /path/to/cert.pem /etc/mac-ops/cert.pem
sudo cp /path/to/key.pem /etc/mac-ops/key.pem

# Set permissions
sudo chmod 600 /etc/mac-ops/key.pem
sudo chown mac-ops:mac-ops /etc/mac-ops/cert.pem
sudo chown mac-ops:mac-ops /etc/mac-ops/key.pem
```

### Step 6: Nginx Reverse Proxy

Install Nginx:
```bash
sudo dnf install -y nginx
```

Create `/etc/nginx/conf.d/mac-ops.conf`:

```nginx
upstream mac_app {
    server 127.0.0.1:5000;
}

server {
    listen 443 ssl http2;
    server_name mac-ops.example.com;

    ssl_certificate /etc/mac-ops/cert.pem;
    ssl_certificate_key /etc/mac-ops/key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://mac_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name mac-ops.example.com;
    return 301 https://$server_name$request_uri;
}
```

Enable Nginx:
```bash
sudo systemctl enable nginx
sudo systemctl start nginx
```

### Step 7: Systemd Service

Create `/etc/systemd/system/mac-ops.service`:

```ini
[Unit]
Description=Maytag Admin Console
After=network.target

[Service]
Type=simple
User=mac-ops
WorkingDirectory=/opt/mac-ops
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 backend/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mac-ops
sudo systemctl start mac-ops
```

### Step 8: Logging Configuration

Create `/etc/rsyslog.d/mac-ops.conf`:

```
# MAC logging
:programname, isequal, "mac-ops" /var/log/mac-ops/app.log
& stop
```

Restart rsyslog:
```bash
sudo systemctl restart rsyslog
```

### Step 9: Backup Configuration

Create `/opt/mac-ops/scripts/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR=/opt/backups/mac-ops
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp /var/lib/mac-ops/mac.db $BACKUP_DIR/mac.db.$TIMESTAMP

# Backup configuration
tar czf $BACKUP_DIR/etc_mac-ops.$TIMESTAMP.tar.gz /etc/mac-ops/

# Backup encryption key
cp /etc/mac-ops/.secrets_key $BACKUP_DIR/.secrets_key.$TIMESTAMP

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
```

Add to crontab:
```bash
0 2 * * * /opt/mac-ops/scripts/backup.sh >> /var/log/mac-ops/backup.log 2>&1
```

### Step 10: Monitoring

Install monitoring agents and configure:

```bash
# Example: Prometheus node exporter
sudo dnf install -y node_exporter
sudo systemctl enable node_exporter
sudo systemctl start node_exporter
```

Configure health checks:

```bash
# Health endpoint
curl -f https://mac-ops.example.com/health || systemctl restart mac-ops
```

Add to crontab:
```bash
*/5 * * * * /opt/mac-ops/scripts/health-check.sh >> /var/log/mac-ops/health.log 2>&1
```

## Verification

After deployment, verify:

```bash
# Check service status
sudo systemctl status mac-ops

# Check Nginx
sudo systemctl status nginx

# Test HTTPS
curl -k https://localhost/auth/login

# Check logs
sudo journalctl -u mac-ops -n 50 -f

# Test database
sqlite3 /var/lib/mac-ops/mac.db "SELECT COUNT(*) FROM user;"
```

## Post-Deployment

1. **Change default admin password**
   ```bash
   python3 backend/manage.py reset-password
   ```

2. **Configure LDAP (if using)**
   - Edit `/etc/mac-ops/mac.conf`
   - Test connection: `python3 -c "from backend.ldap_auth import test_ldap_connection; print(test_ldap_connection())"`

3. **Create initial users**
   ```bash
   python3 backend/manage.py create-user
   ```

4. **Review audit logs**
   - Access admin panel at `https://mac-ops.example.com/admin/`
   - Check audit logs for any issues

5. **Set up backups**
   - Verify backup script runs successfully
   - Test backup restoration

6. **Configure monitoring**
   - Set up alerting for service failures
   - Monitor disk usage
   - Monitor database size

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u mac-ops -n 100

# Test manually
cd /opt/mac-ops
python3 backend/app.py
```

### Database issues

```bash
# Check database integrity
sqlite3 /var/lib/mac-ops/mac.db ".integrity_check"

# Rebuild if needed
rm /var/lib/mac-ops/mac.db
sudo -u mac-ops python3 backend/manage.py init-db
```

### LDAP connection failed

```bash
# Test LDAP connection
python3 -c "from backend.ldap_auth import test_ldap_connection; test_ldap_connection()"

# Check configuration
grep ldap /etc/mac-ops/mac.conf

# Test with ldapsearch
ldapsearch -H ldap://ldap.example.com -x -b "dc=example,dc=com" -s base
```

### Performance issues

```bash
# Check resource usage
top -u mac-ops

# Monitor connections
netstat -an | grep :5000

# Check logs for slow queries
grep "slow" /var/log/mac-ops/app.log
```

## Maintenance

### Regular Tasks

**Daily:**
- Check service health
- Review error logs
- Monitor disk usage

**Weekly:**
- Review audit logs
- Update packages (if available)
- Test backups

**Monthly:**
- Full security audit
- Review and rotate secrets
- Update documentation

### Upgrades

```bash
# Stop service
sudo systemctl stop mac-ops

# Backup database
cp /var/lib/mac-ops/mac.db /var/lib/mac-ops/mac.db.backup

# Update code
cd /opt/mac-ops
sudo -u mac-ops git pull origin main

# Update dependencies
sudo -u mac-ops pip install -r backend/requirements.txt --upgrade

# Run migrations
sudo -u mac-ops python3 backend/manage.py init-db

# Start service
sudo systemctl start mac-ops

# Verify
sudo systemctl status mac-ops
```

## Security Hardening

1. **Firewall**
   ```bash
   sudo firewall-cmd --add-service=https --permanent
   sudo firewall-cmd --reload
   ```

2. **SELinux** (if applicable)
   ```bash
   semanage fcontext -a -t httpd_t "/opt/mac-ops(/.*)?"
   restorecon -Rv /opt/mac-ops
   ```

3. **File permissions**
   ```bash
   sudo chmod 600 /etc/mac-ops/.secrets_key
   sudo chmod 600 /etc/mac-ops/mac.conf
   ```

4. **Regular backups**
   - Encrypted backups
   - Offsite storage
   - Regular restore tests

## Support

For issues:
1. Check logs: `sudo journalctl -u mac-ops -f`
2. Review troubleshooting section
3. Contact system administrator
4. File bug report with logs

## Additional Resources

- [Flask Deployment](https://flask.palletsprojects.com/deployment/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [SQLite Administration](https://www.sqlite.org/cli.html)
- [Linux Security](https://access.redhat.com/security/)
