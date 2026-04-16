# Mac-ops Deployment Quick Start

## Pre-Deployment Checklist

- [ ] RPM package built: `/home/mike/rpmbuild/RPMS/noarch/mac-ops-2.0.0-1.el9.noarch.rpm`
- [ ] Target server: Rocky Linux 9.x
- [ ] SSH access to server with sudo privileges
- [ ] LDAP server details (if using LDAP authentication)

## Basic Installation (Local Auth Only)

```bash
# Copy RPM to server
scp /home/mike/rpmbuild/RPMS/noarch/mac-ops-2.0.0-1.el9.noarch.rpm user@server:

# On server: Install RPM
sudo rpm -i mac-ops-2.0.0-1.el9.noarch.rpm

# Create admin user
sudo python3 /usr/local/macops/backend/manage.py create-admin
# Follow prompts for username, email, password

# Start service
sudo systemctl start mac-ops
sudo systemctl enable mac-ops  # Auto-start on reboot

# Verify
curl http://localhost:5000
```

Access at: `http://<server-ip>:5000`

## Installation with LDAP Authentication

### 1. Configure LDAP

```bash
# Option A: Environment variables (recommended for containerization)
export MAC_LDAP_ENABLED=true
export MAC_LDAP_SERVER=ldap.example.com
export MAC_LDAP_PORT=389
export MAC_LDAP_USE_TLS=true
export MAC_LDAP_BASE_DN="dc=example,dc=com"
export MAC_LDAP_USER_DN_TEMPLATE="uid={username},cn=users,cn=accounts,dc=example,dc=com"

# Option B: Configuration file
sudo cat > /etc/mac-ops/mac.conf << EOF
[ldap]
enabled = true
server = ldap.example.com
port = 389
use_tls = true
base_dn = dc=example,dc=com
user_dn_template = uid={username},cn=users,cn=accounts,dc=example,dc=com
group_dn_template = cn={groupname},cn=groups,cn=accounts,dc=example,dc=com
EOF

sudo chmod 600 /etc/mac-ops/mac.conf
```

### 2. Prepare LDAP Directory

```bash
# On FreeIPA/LDAP server, create groups (example for FreeIPA):
kinit admin

ipa group-add mac_admins --desc="mac-ops Administrators"
ipa group-add mac_operators --desc="mac-ops Operators"
ipa group-add mac_viewers --desc="mac-ops Viewers"

# Add users to appropriate groups
ipa group-add-member mac_admins --users=admin@example.com
```

### 3. Install and Start Service

```bash
# On server: Install RPM
sudo rpm -i mac-ops-2.0.0-1.el9.noarch.rpm

# Verify LDAP configuration
curl http://localhost:5000/auth/status

# Create an optional local admin (backup access)
sudo python3 /usr/local/macops/backend/manage.py create-admin

# Start service
sudo systemctl start mac-ops
sudo systemctl enable mac-ops
```

## Managing Users

### Create Local User

```bash
sudo python3 /usr/local/macops/backend/manage.py create-user
# Follow prompts for:
# - Username
# - Email
# - Password
# - Optional role assignment
```

### Create Admin User

```bash
sudo python3 /usr/local/macops/backend/manage.py create-admin
```

### List Users

```bash
sudo python3 /usr/local/macops/backend/manage.py list-users
```

### Reset User Password

```bash
sudo python3 /usr/local/macops/backend/manage.py reset-password <user_id>
```

### Disable/Enable User

```bash
sudo python3 /usr/local/macops/backend/manage.py disable-user <user_id>
sudo python3 /usr/local/macops/backend/manage.py enable-user <user_id>
```

## Service Management

```bash
# Start service
sudo systemctl start mac-ops

# Stop service
sudo systemctl stop mac-ops

# Restart service
sudo systemctl restart mac-ops

# Check status
sudo systemctl status mac-ops

# View logs
sudo journalctl -u mac-ops -n 100 --no-pager
sudo journalctl -u mac-ops -f  # Follow logs

# Enable auto-start on reboot
sudo systemctl enable mac-ops

# Disable auto-start
sudo systemctl disable mac-ops
```

## Login Methods

### Local Authentication
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "localuser",
    "password": "password123",
    "auth_method": "local"
  }'
```

### LDAP Authentication
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ldapuser",
    "password": "ldappassword",
    "auth_method": "ldap"
  }'
```

### Auto (Try LDAP, Fall Back to Local)
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "anyuser",
    "password": "anypassword"
  }'
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u mac-ops -n 50 --no-pager

# Verify configuration
env | grep MAC_

# Test Python app directly
sudo python3 /opt/mac-ops/backend/app.py
```

### LDAP Connection Failing

```bash
# Check LDAP server reachability
telnet ldap.example.com 389

# Test with ldapsearch
ldapsearch -H ldap://ldap.example.com:389 \
  -b "dc=example,dc=com" \
  "(uid=testuser)"

# Check LDAP config
curl http://localhost:5000/auth/status
```

### Users Can't Login

```bash
# Check audit logs
sudo journalctl -u mac-ops -g "login"

# Verify user exists
sudo python3 /usr/local/macops/backend/manage.py list-users

# Check user is enabled
# (LDAP users auto-created on first login)
```

## Performance Tuning

### Adjust Worker Processes

Edit `/opt/mac-ops/mac-ops.service`:
```ini
[Service]
ExecStart=/usr/bin/python3 /opt/mac-ops/backend/app.py
Environment="FLASK_ENV=production"
Environment="WORKERS=4"  # Number of worker processes
```

### Configure Session Timeout

```bash
export MAC_SESSION_TIMEOUT=1800  # 30 minutes in seconds
```

## Backup and Restore

### Backup Database

```bash
# Local SQLite database
sudo cp /var/lib/mac-ops/mac.db /backup/mac.db.backup
sudo chown $USER:$USER /backup/mac.db.backup
```

### Backup Configuration

```bash
sudo cp /etc/mac-ops/mac.conf /backup/mac.conf.backup
```

## Security Hardening

1. **Use HTTPS**:
   - Deploy behind reverse proxy (nginx/Apache)
   - Enable SSL/TLS termination
   - Set `SESSION_COOKIE_SECURE=true`

2. **Firewall Rules**:
   ```bash
   sudo firewall-cmd --add-port=5000/tcp --permanent
   sudo firewall-cmd --reload
   ```

3. **LDAP Security**:
   - Always use TLS for LDAP connections
   - Restrict LDAP search credentials
   - Monitor LDAP authentication failures

4. **Application Security**:
   - Regularly update the RPM
   - Monitor audit logs
   - Disable unused accounts
   - Use strong passwords for local users

## Updating

```bash
# Stop service
sudo systemctl stop mac-ops

# Backup current version
sudo cp /opt/mac-ops /opt/mac-ops.backup

# Install new RPM (will update in place)
sudo rpm -U mac-ops-2.0.0-1.el9.noarch.rpm

# Restart service
sudo systemctl start mac-ops

# Verify
curl http://localhost:5000
```

## Support & Documentation

- **Setup Guide**: See `LDAP_SETUP.md`
- **Implementation Details**: See `LDAP_IMPLEMENTATION_SUMMARY.md`
- **GitHub Repository**: https://github.com/mike0615/mac-ops
- **Issues/Support**: Submit GitHub issues

---

**Last Updated**: April 11, 2026
**Version**: 2.0.0
**Status**: Production Ready ✅
