---
name: ssh
description: "SSH key generation, configuration, agent management, SCP, port forwarding, and remote server operations."
version: 1.0.0
author: Hermes Agent (adapted from OpenHands ssh)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ssh, remote, server, scp, port-forwarding, key-management, deployment]
    related_skills: [docker, github-auth]
---

# SSH Operations

Comprehensive SSH management — key generation, config, agent, SCP, tunneling, and server operations.

## Key Generation

### Standard RSA Key (widely compatible)
```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com" -f ~/.ssh/id_rsa
```

### Ed25519 (recommended — faster, smaller, more secure)
```bash
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/id_ed25519
```

### Options explained:
- `-t rsa|ed25519|ecdsa` — key type
- `-b 4096` — bits (RSA only)
- `-C "comment"` — usually email or description
- `-f ~/.ssh/id_name` — output file path
- `-N "passphrase"` — set passphrase (empty for none)

## Key Management

### View public key
```bash
cat ~/.ssh/id_ed25519.pub
# Copy this to server's authorized_keys or GitHub SSH keys
```

### View key fingerprint
```bash
ssh-keygen -lf ~/.ssh/id_ed25519.pub
```

### Change passphrase
```bash
ssh-keygen -p -f ~/.ssh/id_ed25519
```

### Fix permissions (common error source)
```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
chmod 600 ~/.ssh/config
```

## SSH Config File

Create `~/.ssh/config` for easy host aliases:

```ssh-config
# ~/.ssh/config

# Personal server
Host myserver
    HostName 203.0.113.10
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3

# GitHub
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519
    AddKeysToAgent yes

# Work server with jump host
Host workserver
    HostName 10.0.1.50
    User admin
    ProxyJump bastion.example.com
    IdentityFile ~/.ssh/id_ed25519_work
```

### Use:
```bash
ssh myserver          # Instead of ssh -i ~/.ssh/id_ed25519 deploy@203.0.113.10
scp file myserver:~/  # Use the alias
```

## SSH Agent

### Start agent and add key
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### List loaded keys
```bash
ssh-add -l
```

### Add with macOS Keychain (persists across reboots)
```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

### Auto-load in ~/.zshrc or ~/.bashrc
```bash
# Auto-start ssh agent
if [ -z "$SSH_AUTH_SOCK" ]; then
  eval "$(ssh-agent -s)" > /dev/null
  ssh-add ~/.ssh/id_ed25519 2>/dev/null
fi
```

## Connecting to Servers

### Basic connection
```bash
ssh user@hostname
ssh -p 2222 user@hostname        # Custom port
ssh -i ~/.ssh/custom_key user@hostname  # Specific key
```

### Run a command remotely
```bash
ssh myserver "ls -la /var/log"
ssh myserver "sudo systemctl restart nginx"
```

### Copy remote command output to local file
```bash
ssh myserver "cat /var/log/syslog" > local_syslog.txt
```

## SCP — File Transfer

### Upload file
```bash
scp local_file.txt myserver:~/
scp -r local_dir/ myserver:~/     # Recursive (directory)
scp -P 2222 file.txt myserver:~/  # Custom port
```

### Download file
```bash
scp myserver:~/remote_file.txt ./
scp -r myserver:~/logs/ ./        # Recursive
```

### Between two remote servers
```bash
scp server1:/path/file server2:/path/
```

## Rsync (Better than SCP for large transfers)

```bash
# Sync local to remote
rsync -avz --progress ./local_dir/ myserver:~/remote_dir/

# Sync remote to local
rsync -avz --progress myserver:~/remote_dir/ ./local_dir/

# Exclude files
rsync -avz --exclude='node_modules' --exclude='.git' ./ myserver:~/

# Dry run (see what would happen)
rsync -avz --dry-run ./ myserver:~/
```

## Port Forwarding

### Local forward (access remote service locally)
```bash
# Access remote PostgreSQL on local port 5433
ssh -L 5433:localhost:5432 myserver

# Now connect locally:
psql -h localhost -p 5432 -U dbuser
```

### Remote forward (expose local service to remote)
```bash
# Expose local port 3000 on remote's port 8080
ssh -R 8080:localhost:3000 myserver
```

### Dynamic SOCKS proxy
```bash
# Full tunnel through remote server
ssh -D 1080 myserver
# Configure browser to use SOCKS5 proxy localhost:1080
```

### Background forwarding (run and detach)
```bash
ssh -fNL 5433:localhost:5432 myserver
# -f = background, -N = no command, -L = local forward
```

## Server Administration

### Check disk space
```bash
ssh myserver "df -h"
```

### Check memory
```bash
ssh myserver "free -h"
```

### Check running services
```bash
ssh myserver "sudo systemctl status nginx"
```

### Tail remote logs
```bash
ssh myserver "tail -f /var/log/syslog"
```

### Edit remote file
```bash
# Stream to local editor
ssh myserver "cat /etc/nginx/nginx.conf" > /tmp/nginx.conf
# Edit locally, then upload back
scp /tmp/nginx.conf myserver:/tmp/
ssh myserver "sudo mv /tmp/nginx.conf /etc/nginx/ && sudo nginx -t && sudo systemctl reload nginx"
```

## Troubleshooting

### Verbose connection debug
```bash
ssh -vvv user@hostname
```

### Common issues:
| Problem | Fix |
|---|---|
| "Permission denied (publickey)" | Check: `ssh-add -l`, key is in server's `~/.ssh/authorized_keys`, correct permissions (600) |
| "Connection timed out" | Check: firewall, port, SSH service running on server |
| "Host key verification failed" | `ssh-keygen -R hostname` to remove old key |
| "Too many authentication failures" | Add `IdentitiesOnly yes` to SSH config for that host |
| Slow connection | Add `GSSAPIAuthentication no` to config |

### Fix "Too many auth failures" in config:
```ssh-config
Host myserver
    HostName server.example.com
    User deploy
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    GSSAPIAuthentication no
```
