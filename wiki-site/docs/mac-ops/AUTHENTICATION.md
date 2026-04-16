# Maytag Admin Console - Authentication Setup Guide

## Overview

Maytag Admin Console (MAC) is a unified infrastructure management platform with enterprise-grade authentication. This guide covers setup, configuration, and administration.

## Quick Start

### 1. Installation

```bash
cd /opt/mac-ops
pip install -r backend/requirements.txt
```

### 2. Initialize Database

```bash
mkdir -p /var/lib/mac-ops
python backend/manage.py init-db
```

### 3. Create Admin User

```bash
python backend/manage.py create-admin
```

This will prompt you to create the first administrator account.

### 4. Start Application

```bash
cd backend
python app.py
```

Visit `http://localhost:5000/auth/login`

## Authentication Methods

### Local Authentication

Users created in MAC database with password hashing.

**Advantages:**
- No external dependencies
- Offline access
- Quick setup

**Disadvantages:**
- Manual user management
- Limited to MAC system

**Creating Users:**

```bash
python backend/manage.py create-user
```

Or via admin API:

```bash
curl -X POST http://localhost:5000/admin/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123",
    "roles": ["operator"]
  }'
```

### LDAP/FreeIPA Authentication

Authenticate against existing LDAP/FreeIPA infrastructure.

**Advantages:**
- Centralized user management
- Group-based role assignment
- Enterprise integration

**Disadvantages:**
- Requires LDAP server
- Periodic syncing needed

### Setup LDAP/FreeIPA

1. **Configuration File** - Create `/etc/mac-ops/mac.conf`:

```ini
[ldap]
enabled = true
server = ldap.example.com
port = 389
use_tls = true
base_dn = dc=example,dc=com
user_dn_template = uid={username},cn=users,cn=accounts,dc=example,dc=com
group_dn_template = cn={groupname},cn=groups,cn=accounts,dc=example,dc=com
search_dn = uid=admin,cn=users,cn=accounts,dc=example,dc=com
search_password = SecurePassword
```

2. **Or Use Environment Variables:**

```bash
export MAC_LDAP_ENABLED=true
export MAC_LDAP_SERVER=ldap.example.com
export MAC_LDAP_PORT=389
export MAC_LDAP_USE_TLS=true
export MAC_LDAP_BASE_DN=dc=example,dc=com
```

3. **FreeIPA Group Mapping:**

MAC automatically maps FreeIPA groups to roles:
- `mac_admins` → admin role
- `mac_operators` → operator role
- `mac_viewers` → viewer role

Users get roles based on their group membership.

## User Management

### CLI Commands

```bash
# Create new user
python backend/manage.py create-user

# List all users
python backend/manage.py list-users

# Reset user password
python backend/manage.py reset-password

# Enable/disable user
python backend/manage.py enable-user
python backend/manage.py disable-user
```

### Web Admin Panel

1. Login as admin
2. Navigate to `/admin/`
3. Select "Users" tab
4. Click "+ New User"
5. Fill in user details and roles

### API Endpoints

**List users:**
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/admin/users
```

**Create user:**
```bash
curl -X POST http://localhost:5000/admin/users \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","email":"user1@example.com","password":"Pass123","roles":["viewer"]}'
```

**Disable user:**
```bash
curl -X POST http://localhost:5000/admin/users/1/disable
```

**Update roles:**
```bash
curl -X PUT http://localhost:5000/admin/users/1/roles \
  -d '{"roles":["admin","operator"]}'
```

## Role-Based Access Control (RBAC)

### Default Roles

| Role | Permissions |
|------|-------------|
| **admin** | All permissions - full system access |
| **operator** | Execute playbooks, manage resources |
| **viewer** | Read-only access |

### Permission Model

Permissions are resource + action pairs:
- `resource`: Component (e.g., 'ansible', 'admin', 'pxe')
- `action`: Operation (e.g., 'execute', 'view', 'manage')

**Example permissions:**
- `ansible:view_playbooks`
- `ansible:execute_playbook`
- `admin:manage_users`
- `admin:manage_secrets`

### Managing Permissions

**Via Admin Panel:**
1. Go to Admin → Roles
2. Select role
3. Assign/remove permissions

**Via API:**
```bash
curl -X PUT http://localhost:5000/admin/roles/1/permissions \
  -H "Content-Type: application/json" \
  -d '{
    "permissions": [
      "ansible:view_playbooks",
      "ansible:execute_playbook"
    ]
  }'
```

## Secrets Vault

### Create Secrets

**Via CLI:**
```bash
# Interactive
python backend/manage.py create-secret

# Note: Use admin API or panel instead
```

**Via Web Admin:**
1. Go to Admin → Secrets
2. Click "+ New Secret"
3. Enter secret name, value, type, description
4. Click Create

**Via API:**
```bash
curl -X POST http://localhost:5000/admin/secrets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "api_key_prod",
    "value": "sk_live_...",
    "secret_type": "api_key",
    "description": "Production API key"
  }'
```

### Secret Types

- **password** - Passwords for services
- **api_key** - API keys and tokens
- **token** - OAuth tokens, JWT, etc.
- **ssh_key** - SSH private keys

### Using Secrets in Playbooks

In your Ansible playbooks, retrieve secrets using the `secret()` filter:

```yaml
- name: Example task
  debug:
    msg: "{{ secret('api_key_prod') }}"
```

### Secret Security

- **Encryption:** Secrets are encrypted at rest using Fernet (symmetric encryption)
- **Access Control:** Only users with `admin:manage_secrets` permission can view/edit
- **Audit Logging:** All secret access is logged
- **Key Management:** Encryption key stored in `/etc/mac-ops/.secrets_key` with 0600 permissions

## Session Management

### Session Configuration

Edit `/etc/mac-ops/mac.conf`:

```ini
[auth]
session_timeout = 1800  # 30 minutes in seconds
```

Or environment variable:
```bash
export MAC_SESSION_TIMEOUT=1800
```

### Session Features

- **Auto Timeout:** Sessions expire after 30 minutes of inactivity
- **Remember Me:** 7-day persistent login with checkbox
- **Security:** HttpOnly, Secure (HTTPS) flags on cookies
- **Per-Device:** Each login creates independent session

## Audit Logging

All authentication and admin actions are logged to audit trail:

- User logins (success/failure)
- User creation/deletion
- Role changes
- Secret access
- Permission changes
- Admin actions

**View audit logs:**
1. Admin → Audit Logs
2. Or via API: `GET /admin/audit-logs`

**Audit Log Fields:**
- Timestamp
- User who performed action
- Action type
- Resource affected
- IP address
- Detailed description

## Security Best Practices

1. **Password Policy**
   - Minimum 8 characters
   - Require uppercase, lowercase, digits
   - No common patterns or dictionary words

2. **LDAP/FreeIPA**
   - Enable TLS for LDAP connections
   - Use dedicated service account for searches
   - Implement group-based access control

3. **Secrets Management**
   - Regularly rotate secrets
   - Limit access with permissions
   - Use strong encryption keys
   - Review audit logs for access patterns

4. **Session Security**
   - Always use HTTPS in production
   - Set appropriate session timeouts
   - Disable remember-me for sensitive operations
   - Log out unattended sessions

5. **Admin Account**
   - Don't use for daily operations
   - Enable MFA when available
   - Restrict IP addresses if possible
   - Monitor audit logs regularly

## Troubleshooting

### Login Issues

**"Invalid username or password"**
- Verify credentials
- Check if user account is enabled
- If LDAP, verify LDAP configuration

**"LDAP server connection failed"**
```bash
# Test LDAP connection
python -c "from backend.ldap_auth import test_ldap_connection; print(test_ldap_connection())"
```

Check LDAP config: server, port, TLS settings

**"Session expired"**
- Session timeout reached
- Clear browser cookies
- Login again

### Database Issues

**Database locked**
```bash
# Reinitialize database
rm -f /var/lib/mac-ops/mac.db
python backend/manage.py init-db
```

**Corrupted database**
```bash
# Backup and reset
cp /var/lib/mac-ops/mac.db /var/lib/mac-ops/mac.db.backup
python backend/manage.py init-db
```

### Permission Denied

**"Permission denied" on admin operations**
- Verify user has admin role
- Check permissions are assigned to role
- Review audit logs for details

**API returns 403 Forbidden**
- User lacks required permission
- Login with higher privilege account
- Contact admin to add permissions

## Deployment

### Production Setup

1. **Directory Structure:**
```bash
mkdir -p /opt/mac-ops
mkdir -p /var/lib/mac-ops
mkdir -p /etc/mac-ops
mkdir -p /var/log/mac-ops
```

2. **Permissions:**
```bash
chmod 755 /opt/mac-ops
chmod 700 /var/lib/mac-ops
chmod 700 /etc/mac-ops
chmod 700 /var/log/mac-ops
```

3. **Configuration:**
```bash
cp backend/config.example.conf /etc/mac-ops/mac.conf
chmod 600 /etc/mac-ops/mac.conf
# Edit with your settings
```

4. **Database Initialization:**
```bash
python backend/manage.py init-db
python backend/manage.py create-admin
```

5. **Start Service:**
```bash
# Via systemd
systemctl start mac-ops

# Or direct
python backend/app.py
```

### Systemd Service File

Create `/etc/systemd/system/mac-ops.service`:

```ini
[Unit]
Description=Maytag Admin Console
After=network.target

[Service]
Type=simple
User=mac-ops
WorkingDirectory=/opt/mac-ops
ExecStart=/usr/bin/python3 backend/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl enable mac-ops
systemctl start mac-ops
```

## API Documentation

### Authentication

**Login:**
```
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123",
  "remember_me": false,
  "auth_method": "local"
}

Response 200:
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "email": "user@example.com",
    "roles": ["operator"],
    "permissions": ["ansible:view_playbooks", "ansible:execute_playbook"]
  }
}
```

**Logout:**
```
POST /auth/logout

Response 200:
{
  "message": "Logged out successfully"
}
```

**Get current user:**
```
GET /auth/me

Response 200:
{
  "id": 1,
  "username": "user@example.com",
  "roles": ["operator"],
  "permissions": ["ansible:view_playbooks"],
  "last_login": "2026-03-29T00:00:00"
}
```

### Admin Users

```
GET    /admin/users                  # List all users
POST   /admin/users                  # Create user
GET    /admin/users/<id>             # Get user details
PUT    /admin/users/<id>/roles       # Update user roles
POST   /admin/users/<id>/disable     # Disable user
POST   /admin/users/<id>/enable      # Enable user
POST   /admin/users/<id>/reset-password  # Reset password
```

### Admin Roles

```
GET    /admin/roles                  # List all roles
PUT    /admin/roles/<id>/permissions # Update role permissions
```

### Secrets

```
GET    /admin/secrets                # List secrets (no values)
POST   /admin/secrets                # Create secret
GET    /admin/secrets/<id>           # Get secret value
PUT    /admin/secrets/<id>           # Update secret
DELETE /admin/secrets/<id>           # Delete secret
GET    /admin/secrets/by-name/<name> # Get secret by name
```

### Audit Logs

```
GET    /admin/audit-logs             # List audit logs
```

## Support

For issues, questions, or contributions:
1. Check troubleshooting section
2. Review audit logs for clues
3. Contact system administrator
4. Report bugs with details to development team

## Additional Resources

- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [LDAP Configuration](https://www.openldap.org/)
- [FreeIPA Project](https://www.freeipa.org/)
