---
name: troubleshooting
description: "Systematic troubleshooting for unfamiliar projects — diagnose first, then fix. Covers logs, processes, network, disk, deps."
version: 1.0.0
author: Hermes Agent (adapted from OpenHands troubleshooting)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [troubleshooting, debugging, diagnose, investigate, unfamiliar-project, sysadmin]
    related_skills: [systematic-debugging, python-debugpy, node-inspect-debugger, ssh, docker]
---

# Troubleshooting

When facing an issue in an unfamiliar project — where you don't know the codebase, the stack, or the architecture — you need a systematic diagnosis approach. Don't guess. Gather data first.

## The Iron Law

```
GATHER EVIDENCE → FORM HYPOTHESIS → TEST → FIX
```

Never start editing code before you know what's actually broken.

## Phase 1: Gather Information

### Read the Error
```
What exactly does the error say?
What file/line triggered it?
Is it a crash, wrong output, hang, or silent failure?
```

### Check Logs
```bash
# Application logs
tail -f /var/log/app/error.log
tail -100 /var/log/syslog | grep -i error

# System logs
journalctl -xe --no-pager | tail -50
dmesg | tail -20

# Docker logs
docker logs <container> --tail 100
docker logs <container> --since 1h | grep -i "error\|fatal\|panic"
```

### Check Processes
```bash
# What's running?
ps aux | grep -i <process_name>
top -bn1 | head -20

# What's listening on ports?
ss -tlnp
netstat -tlnp 2>/dev/null

# Is the service actually running?
systemctl status <service>
```

### Check Resources
```bash
# Disk space (full disk = silent failures)
df -h

# Memory
free -h

# CPU load
uptime

# Open files
lsof -i :<port>
```

### Check Network
```bash
# Can you reach the service?
curl -v http://localhost:<port>/health
curl -v http://localhost:<port>/api/status

# DNS resolution
nslookup <hostname>
dig <hostname>

# Port connectivity
nc -zv <host> <port>
telnet <host> <port>
```

### Check Dependencies
```bash
# Python
pip list | grep <package>
pip show <package>

# Node
npm list <package>
node -e "console.log(require('<package>').version)"

# System
dpkg -l | grep <package>   # Debian/Ubuntu
rpm -qa | grep <package>   # RHEL

# Docker
docker ps -a                # All containers
docker images
docker network ls
```

### Check Configuration
```bash
# Config files
cat /etc/<app>/config.yml
cat .env
cat docker-compose.yml

# Environment variables
env | grep -i <app>
printenv <VAR>

# File permissions
ls -la /path/to/config
```

### Check Recent Changes
```bash
# What changed recently?
git log --oneline -10
git diff HEAD~5

# File modification times
ls -lt /etc/<app>/
find /var/log -name "*.log" -mtime -1
```

## Phase 2: Reproduce

```
Can you make the error happen again?
What are the exact steps?
Does it happen every time or intermittently?
Does it happen in dev, staging, production, or all?
```

Reproduce consistently before attempting a fix.

## Phase 3: Isolate

Narrow down the cause:

```
Does it happen with a clean config?
Does it happen with no data?
Does it happen with different input?
Does it work if you skip step N?
```

### Binary Search Debugging
```bash
# Comment out HALF the code
# Does it still fail?
#   YES → the cause is in the other half
#   NO  → the cause is in what you commented out
# Repeat until found
```

### Process of Elimination
```bash
# Try with minimal config
cp config.yml config.yml.bak
cat > config.yml << 'EOF'
# Absolute minimum config
debug: true
port: 8000
EOF

# Restart and test
systemctl restart <service>
# Still fails? → Not a config issue
```

## Phase 4: Fix and Verify

```bash
# Make ONE change at a time
# Apply fix
# Restart/reload
systemctl restart <service>
# Verify fix
curl http://localhost:<port>/health
# Check logs for new errors
tail -f /var/log/app/error.log
```

## Common Issues Checklist

| Symptom | Check |
|---|---|
| "Connection refused" | Service running? Correct port? Firewall? |
| "Permission denied" | File perms? User? SELinux/AppArmor? |
| "No space left on device" | `df -h` — disk full? |
| "Out of memory" | `free -h` — OOM killer? Memory leak? |
| "Address already in service" | `lsof -i :<port>` — old process still running? |
| "Module not found" | Virtualenv activated? Package installed? PYTHONPATH? |
| Slow response | CPU load? Memory? Database locks? Network latency? |
| Intermittent failures | Race condition? Timeout too low? Resource exhaustion? |
| Works in dev, fails in prod | Config difference? Missing env var? Different dependency versions? |

## Tips

- **Don't guess** — gather data first, always
- **Read the full error** — the answer is usually in the traceback
- **Check the obvious** — is it plugged in? is it running? is there disk space?
- **One change at a time** — if you change 5 things and it works, you don't know which one fixed it
- **Document what you learned** — save to `.hermes/memory.md` for next time
- **When stuck, explain the problem** — rubber-duck debugging works
