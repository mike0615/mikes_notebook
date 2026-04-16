# LDAP/FreeIPA Authentication Setup

This document describes how to configure LDAP/FreeIPA authentication for mac-ops.

## Overview

mac-ops supports two authentication methods:
1. **Local**: User credentials stored in the mac-ops database
2. **LDAP/FreeIPA**: User credentials verified against an LDAP server, with automatic user provisioning

The application can use either method exclusively or both together (with LDAP taking precedence when enabled).

## Configuration

Configuration is loaded from environment variables and/or `/etc/mac-ops/mac.conf`.

### Environment Variables

Set these environment variables before starting mac-ops:

```bash
# Enable LDAP authentication
export MAC_LDAP_ENABLED=true

# LDAP server connection details
export MAC_LDAP_SERVER=ldap.example.com
export MAC_LDAP_PORT=389
export MAC_LDAP_USE_TLS=true

# LDAP directory structure
export MAC_LDAP_BASE_DN="dc=example,dc=com"
export MAC_LDAP_USER_DN_TEMPLATE="uid={username},cn=users,cn=accounts,dc=example,dc=com"
export MAC_LDAP_GROUP_DN_TEMPLATE="cn={groupname},cn=groups,cn=accounts,dc=example,dc=com"

# Optional: Credentials for LDAP searches (if your server requires auth)
export MAC_LDAP_SEARCH_DN="cn=admin,dc=example,dc=com"
export MAC_LDAP_SEARCH_PASSWORD="admin_password"
```

### Configuration File

Alternatively, create `/etc/mac-ops/mac.conf`:

```ini
[ldap]
enabled = true
server = ldap.example.com
port = 389
use_tls = true
base_dn = dc=example,dc=com
user_dn_template = uid={username},cn=users,cn=accounts,dc=example,dc=com
group_dn_template = cn={groupname},cn=groups,cn=accounts,dc=example,dc=com
search_dn = cn=admin,dc=example,dc=com
search_password = admin_password
```

## Group-to-Role Mapping

LDAP groups are automatically mapped to application roles:

| LDAP Group | Application Role | Permissions |
|-----------|------------------|-------------|
| `mac_admins` | `admin` | Full access to all features |
| `mac_operators` | `operator` | Can execute playbooks and manage infrastructure |
| `mac_viewers` | `viewer` | Read-only access to dashboard and logs |

If a user is not a member of any mapped group, they receive the `viewer` role by default.

## User Provisioning

When an LDAP user logs in for the first time:

1. mac-ops connects to the LDAP server and verifies credentials
2. User details (username, email) are fetched from LDAP
3. A local user account is created in the mac-ops database (with `auth_method='ldap'`)
4. User's LDAP group memberships are mapped to application roles
5. User can now access the application

On subsequent logins:
- Credentials are verified against LDAP
- LDAP group memberships are synced (role assignments may change)
- `last_login` timestamp is updated

## Authentication Methods

When logging in via the API, you can specify the authentication method:

```bash
# Auto-detect (LDAP if enabled, then local)
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "password123"
  }'

# Force LDAP authentication
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "password123",
    "auth_method": "ldap"
  }'

# Force local authentication
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "localuser",
    "password": "localpassword",
    "auth_method": "local"
  }'
```

## Checking LDAP Status

You can check if LDAP is configured and connected:

```bash
curl http://localhost:5000/auth/status
```

Response:
```json
{
  "ldap_enabled": true,
  "ldap_connected": true,
  "ldap_error": null
}
```

## FreeIPA Specific Configuration

FreeIPA is a comprehensive identity management solution built on LDAP. Here's a FreeIPA-specific example:

```ini
[ldap]
enabled = true
server = ipa.example.com
port = 389
use_tls = true
base_dn = cn=accounts,dc=example,dc=com
user_dn_template = uid={username},cn=users,cn=accounts,dc=example,dc=com
group_dn_template = cn={groupname},cn=groups,cn=accounts,dc=example,dc=com
```

Create the required groups in FreeIPA:

```bash
# Login to FreeIPA server
kinit admin

# Create groups
ipa group-add mac_admins --desc="mac-ops Administrators"
ipa group-add mac_operators --desc="mac-ops Operators"
ipa group-add mac_viewers --desc="mac-ops Viewers"

# Add users to groups
ipa group-add-member mac_admins --users=admin
ipa group-add-member mac_operators --users=operator1
ipa group-add-member mac_viewers --users=viewer1
```

## Troubleshooting

### LDAP Connection Fails

1. Verify network connectivity to LDAP server:
   ```bash
   telnet ldap.example.com 389
   ```

2. Check LDAP configuration:
   ```bash
   # View current config (from environment)
   env | grep MAC_LDAP
   ```

3. Test with ldapsearch:
   ```bash
   ldapsearch -H ldap://ldap.example.com:389 \
     -D "uid=testuser,cn=users,cn=accounts,dc=example,dc=com" \
     -w password \
     -b "dc=example,dc=com" \
     "(uid=testuser)"
   ```

### User Doesn't Get Expected Role

1. Check user's LDAP group membership:
   ```bash
   ldapsearch -H ldap://ldap.example.com:389 \
     -b "dc=example,dc=com" \
     "(memberuid=username)"
   ```

2. Verify group names match config (case-sensitive):
   - LDAP: `mac_admins`
   - Config: `mac_admins`

3. Try logging out and logging back in to trigger role sync

### LDAP Password Not Working

1. Verify the password is correct in your LDAP server
2. Check that the user DN template matches your LDAP structure
3. Try LDAP authentication with ldapsearch to confirm:
   ```bash
   ldapsearch -H ldap://ldap.example.com:389 \
     -D "uid=username,cn=users,cn=accounts,dc=example,dc=com" \
     -w yourpassword \
     -b "dc=example,dc=com" \
     "uid=username"
   ```

## Security Considerations

1. **Use TLS**: Always set `MAC_LDAP_USE_TLS=true` in production
2. **Credentials**: If your LDAP server requires search credentials, store them securely:
   - Use environment variables or configuration files with restricted permissions (600)
   - Never commit credentials to version control
3. **Session Security**: 
   - Set `SESSION_COOKIE_SECURE=true` for HTTPS deployments
   - Set `SESSION_COOKIE_HTTPONLY=true` to prevent JavaScript access
4. **Audit Logging**: All authentication attempts are logged to the audit trail

## Examples

### FreeIPA with TLS

```bash
export MAC_LDAP_ENABLED=true
export MAC_LDAP_SERVER=ipa.corp.com
export MAC_LDAP_PORT=636
export MAC_LDAP_USE_TLS=true
export MAC_LDAP_BASE_DN="cn=accounts,dc=corp,dc=com"
export MAC_LDAP_USER_DN_TEMPLATE="uid={username},cn=users,cn=accounts,dc=corp,dc=com"

# Start mac-ops
systemctl start mac-ops
```

### OpenLDAP Configuration

```ini
[ldap]
enabled = true
server = ldap.company.local
port = 389
use_tls = true
base_dn = o=company,c=us
user_dn_template = uid={username},ou=people,o=company,c=us
group_dn_template = cn={groupname},ou=groups,o=company,c=us
```

### Hybrid Setup (Local + LDAP)

Keep LDAP disabled initially, then enable it:

```bash
# Phase 1: Local auth only
export MAC_LDAP_ENABLED=false

# Later, when LDAP is ready:
export MAC_LDAP_ENABLED=true

# Users created locally can still use local auth (auth_method='local')
# LDAP users will have auth_method='ldap'
```

## Related Documentation

- [LDAP Authentication Source Code](ldap_auth.py)
- [Configuration Module](config.py)
- [User Model](models.py)
- [Authentication Module](auth.py)
