# FreeIPA Authentication Integration Guide

## Overview

This guide explains how to integrate LRN_PXE with FreeIPA/LDAP authentication for centralized user management and access control.

## Architecture

```
LRN_PXE Web UI (Port 80/443)
        ↓
  Flask + Auth Middleware
        ↓
  LDAP queries (Port 389/636)
        ↓
  FreeIPA Server
        ↓
  User Database
```

## Prerequisites

1. **FreeIPA Server** running and accessible
2. **Administrator credentials** for LDAP queries
3. **FreeIPA group** for LRN_PXE admins (recommended: `lrn-pxe-admins`)
4. **Network connectivity** between LRN_PXE and FreeIPA servers

## Setup Instructions

### Step 1: Configure FreeIPA (on IPA server)

Create the admin group:
```bash
ipa group-add lrn-pxe-admins --desc="LRN_PXE Administrators"
```

Add admin users:
```bash
ipa group-add-member lrn-pxe-admins --users=admin,john,sarah
```

Create optional operator group:
```bash
ipa group-add lrn-pxe-operators --desc="LRN_PXE Operators"
ipa group-add-member lrn-pxe-operators --users=operator1,operator2
```

### Step 2: Update Settings

Edit `/opt/lrn_pxe/config/settings.json`:

```json
{
  "auth_enabled": true,
  "ldap_server": "ipa.example.com",
  "ldap_port": 389,
  "ldap_base_dn": "dc=example,dc=com",
  "ldap_admin_dn": "uid=admin,cn=users,cn=accounts,dc=example,dc=com",
  "ldap_admin_password": "${LDAP_ADMIN_PASSWORD}",
  "ldap_admin_group": "lrn-pxe-admins",
  "ldap_timeout": 10,
  "session_timeout": 3600,
  "require_https": false,
  "server_ip": "192.168.1.100",
  "web_port": 8080
}
```

**Important:** Set `ldap_admin_password` via environment variable:
```bash
export LDAP_ADMIN_PASSWORD="your-admin-password"
lrn-pxe restart
```

### Step 3: Install Dependencies

Update requirements.txt:
```bash
pip install python-ldap>=3.4.0
```

### Step 4: Enable Authentication

Set environment variable:
```bash
export LRN_PXE_AUTH_ENABLED=true
systemctl restart lrn-pxe
```

## Usage

### For End Users

1. Navigate to `http://your-server/`
2. You'll be redirected to login page
3. Enter your FreeIPA username and password
4. After successful auth, you'll see the dashboard

**Permissions:**
- **Admins** (members of `lrn-pxe-admins`): Full access to all features
- **Others**: Read-only access to boot menu (coming in future releases)

### For Administrators

#### Add New Admin User
```bash
ipa group-add-member lrn-pxe-admins --users=newuser
```

#### Remove Admin User
```bash
ipa group-remove-member lrn-pxe-admins --users=olduser
```

#### View All Admin Users
```bash
ipa group-show lrn-pxe-admins
```

#### Check User Group Membership
```bash
ipa user-show --all someuser | grep "Member of"
```

## Security Features

✅ **Authentication**
- LDAP bind with user credentials
- No passwords stored locally
- Centralized credential management

✅ **Authorization**
- RBAC based on FreeIPA groups
- Admin-only operations protected
- Audit logging of all changes

✅ **Session Management**
- Secure session cookies (HttpOnly, SameSite)
- Configurable session timeout
- Automatic logout on inactivity

✅ **Security Headers**
- CSRF protection (when HTTPS enabled)
- Security headers (CSP, X-Frame-Options, etc.)
- HTTPS enforcement in production

## Troubleshooting

### Can't Connect to LDAP Server

**Symptom:** "LDAP connection error" in logs

**Solutions:**
1. Verify network connectivity:
   ```bash
   ping ipa.example.com
   nc -zv ipa.example.com 389
   ```

2. Check firewall rules:
   ```bash
   sudo firewall-cmd --list-all | grep 389
   ```

3. Verify LDAP server is running:
   ```bash
   systemctl status dirsrv@example-com
   ```

### Authentication Fails

**Symptom:** "Invalid credentials" error

**Solutions:**
1. Verify user exists in FreeIPA:
   ```bash
   ipa user-show username
   ```

2. Test LDAP credentials manually:
   ```bash
   ldapwhoami -H ldap://ipa.example.com \
     -D "uid=username,cn=users,cn=accounts,dc=example,dc=com" \
     -W
   ```

3. Check admin credentials in settings:
   ```bash
   ldapwhoami -H ldap://ipa.example.com \
     -D "uid=admin,cn=users,cn=accounts,dc=example,dc=com" \
     -W
   ```

### Admin User Can't Perform Operations

**Symptom:** 403 Forbidden errors for admin operations

**Solutions:**
1. Verify user is in admin group:
   ```bash
   ipa user-show username --all | grep memberOf
   ```

2. Restart application after adding to group:
   ```bash
   systemctl restart lrn-pxe
   ```

3. Clear browser cookies and log back in

### Session Timeout Issues

**Symptom:** Logged out unexpectedly

**Solutions:**
1. Increase session timeout in settings.json:
   ```json
   "session_timeout": 7200  // 2 hours instead of 1 hour
   ```

2. Restart service:
   ```bash
   systemctl restart lrn-pxe
   ```

## API Authentication

All REST API endpoints now require authentication. Include session cookie in requests:

```bash
# Login and capture session cookie
curl -c cookies.txt -d "username=admin&password=secret" \
  http://your-server/login

# Use cookie in subsequent requests
curl -b cookies.txt http://your-server/api/images
curl -b cookies.txt -X POST http://your-server/api/menu \
  -H "Content-Type: application/json" \
  -d '{"title": "New Menu"}'
```

## Advanced Configuration

### Using HTTPS (Recommended)

```json
{
  "require_https": true,
  "session_cookie_secure": true,
  "session_cookie_httponly": true,
  "session_cookie_samesite": "Lax"
}
```

Then configure nginx with SSL certificates.

### Custom LDAP Schema

If using non-standard LDAP attributes:

```python
# In web/auth.py, modify FreeIPAAuth class
LDAP_USER_ATTRIBUTES = [
    'uid', 'mail', 'displayName', 'customAttribute'
]
```

### Multiple Admin Groups

```python
# Support multiple admin groups (modify auth.py)
admin_groups = ['lrn-pxe-admins', 'infrastructure-team']
is_admin = any(group in user_groups for group in admin_groups)
```

### Rate Limiting

```python
# Add rate limiting to login endpoint
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # ... login code
```

## Monitoring & Auditing

### Check Authentication Logs

```bash
# View recent logins
tail -50 /opt/lrn_pxe/logs/auth.log

# Filter successful logins
grep "Authentication successful" /opt/lrn_pxe/logs/auth.log

# Filter failed attempts
grep "Authentication failed" /opt/lrn_pxe/logs/auth.log
```

### Audit Trail

All administrative actions are logged:
```bash
grep "admin action" /opt/lrn_pxe/logs/app.log
```

### Monitor Failed Logins

```bash
# Recent failed attempts
tail -100 /opt/lrn_pxe/logs/auth.log | grep "failed"

# Count failed attempts by user
grep "failed" /opt/lrn_pxe/logs/auth.log | awk -F: '{print $NF}' | sort | uniq -c
```

## Migration Path

### From No Authentication to FreeIPA

1. Deploy current version with auth disabled
2. Verify all functionality works
3. Create FreeIPA admin group and add users
4. Enable auth in settings
5. Test login as regular user
6. Test login as admin user
7. Monitor logs for any issues
8. Inform users of new login requirement

### Rollback Plan

If issues occur, disable authentication:
```json
{
  "auth_enabled": false
}
```

Then restart service. Previous sessions will still be valid.

## Support & Resources

- **FreeIPA Documentation:** https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/installing_identity_management/index
- **LDAP RFC 4511:** https://tools.ietf.org/html/rfc4511
- **Flask-LDAP Documentation:** https://github.com/uxsolutions/flask-ldapconn
- **LRN_PXE Issues:** https://github.com/your-org/lrn-pxe/issues

## What's Next

Planned enhancements:
- [ ] Role-based access control (viewer, operator, admin)
- [ ] Two-factor authentication (2FA) support
- [ ] LDAP search filter customization
- [ ] Active Directory support
- [ ] SAML/SSO integration
- [ ] Token-based API authentication (JWT)
- [ ] Audit log export and analysis
