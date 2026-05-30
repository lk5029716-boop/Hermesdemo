---
name: security
description: "Security best practices for code review, development, and deployment — OWASP, input validation, secrets, crypto."
version: 1.0.0
author: Hermes Agent (adapted from OpenHands security)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, owasp, code-review, best-practices, hardening]
    related_skills: [github-code-review, requesting-code-review, systematic-debugging]
---

# Security Best Practices

Security is not a feature — it's a requirement. This skill covers the most common security issues found in code reviews and how to fix them.

## The Iron Law

```
TRUST NO INPUT. VALIDATE EVERYTHING. EXPOSE NOTHING.
```

## OWASP Top 10 — Quick Reference

### 1. Injection (SQL, Command, Template)
**Never** concatenate user input into queries or commands.

```python
# ❌ WRONG — SQL Injection
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# ✅ CORRECT — Parameterized query
cursor.execute("SELECT * FROM users WHERE name = %s", (user_input,))
```

```python
# ❌ WRONG — Command Injection
os.system(f"ping {user_input}")

# ✅ CORRECT — Use subprocess with list args
subprocess.run(["ping", "-c", "4", user_input], capture_output=True)
```

### 2. Broken Authentication
- Never store passwords in plaintext — use bcrypt/scrypt/argon2
- Never put secrets in code, config files, or git history
- Implement rate limiting on login endpoints
- Use secure session management (HTTP-only, Secure, SameSite cookies)

```python
# ❌ WRONG
password_hash = hashlib.md5(password.encode()).hexdigest()

# ✅ CORRECT
import bcrypt
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

### 3. Sensitive Data Exposure
- Encrypt data at rest and in transit (TLS everywhere)
- Never log secrets, tokens, or PII
- Use environment variables for secrets, never hardcode
- Mask sensitive data in error messages

```python
# ❌ WRONG — Hardcoded secret
API_KEY = "sk-1234567890abcdef"

# ✅ CORRECT — Environment variable
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable is required")
```

### 4. Cross-Site Scripting (XSS)
- Escape all user-generated content in HTML contexts
- Use Content Security Policy headers
- Sanitize HTML with allowlists, not denylists

### 5. Security Misconfiguration
- Disable debug mode in production
- Remove default credentials
- Keep dependencies updated
- Use security headers (HSTS, X-Frame-Options, CSP)

```nginx
# Security headers
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'" always;
```

## Secrets Management

### What Counts as a Secret
- API keys, tokens, passwords
- Database connection strings with credentials
- Private keys and certificates
- Encryption keys
- OAuth client secrets

### How to Handle Secrets

```bash
# ✅ Use environment variables
export DATABASE_URL="postgresql://user:pass@host/db"

# ✅ Use a .env file (gitignored)
echo ".env" >> .gitignore
echo "SECRET_KEY=abc123" >> .env

# ✅ Use secret management (production)
# - HashiCorp Vault
# - AWS Secrets Manager
# - GitHub Actions secrets
# - Docker secrets
```

### If You Accidentally Commit a Secret
1. **Rotate the secret immediately** — assume it's compromised
2. Remove from git history:
```bash
# Remove from all history
git filter-repo --path <file> --invert-paths

# Or for a specific secret string
git filter-repo --replace-text <(echo "OLD_SECRET==>REPLACED")
```
3. Force push: `git push --force`
4. Verify it's gone from remote

## Input Validation

Validate ALL input — from users, APIs, files, environment:

```python
from pydantic import BaseModel, validator

class UserCreate(BaseModel):
    email: str
    age: int
    
    @validator('email')
    def email_must_be_valid(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v.lower().strip()
    
    @validator('age')
    def age_must_be_reasonable(cls, v):
        if v < 0 or v > 150:
            raise ValueError('Invalid age')
        return v
```

## File Operations

```python
# ❌ WRONG — Path traversal
file_path = f"/uploads/{user_input}"
with open(file_path) as f: ...

# ✅ CORRECT — Sanitize path
import os
SAFE_DIR = "/uploads"
file_path = os.path.realpath(os.path.join(SAFE_DIR, user_input))
if not file_path.startswith(SAFE_DIR):
    raise ValueError("Path traversal detected")
```

## Cryptography

```python
# ❌ Wrong algorithms for passwords
hashlib.md5(password)      # Broken
hashlib.sha1(password)     # Weak

# ✅ Correct: Use bcrypt, scrypt, or argon2
bcrypt.hashpw(password, bcrypt.gensalt())

# ❌ Wrong: ECB mode, hardcoded IV
AES.new(key, AES.MODE_ECB)

# ✅ Correct: Use high-level libraries
from cryptography.fernet import Fernet
Fernet(key).encrypt(data)
```

## Security Checklist for Code Reviews

- [ ] No hardcoded secrets or credentials
- [ ] All user input is validated/sanitized
- [ ] SQL uses parameterized queries
- [ ] File operations check path traversal
- [ ] Authentication uses strong hashing
- [ ] Error messages don't leak sensitive info
- [ ] Security headers are set
- [ ] Dependencies are up-to-date (no known CVEs)
- [ ] CORS is properly configured
- [ ] Rate limiting on sensitive endpoints
