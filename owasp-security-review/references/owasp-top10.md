# OWASP Top 10 (2025) — Detection Guide

The 2025 edition introduces significant changes from 2021:

| 2021 Category | 2025 Category | Change |
|---|---|---|
| A01:2021 Broken Access Control | A01:2025 Broken Access Control | Expanded — now includes SSRF, path traversal, CSRF |
| A05:2021 Security Misconfiguration | A02:2025 Security Misconfiguration | Moved up from #5 |
| A06:2021 Vulnerable Components | A03:2025 Software Supply Chain Failures | Expanded — covers entire supply chain |
| A02:2021 Cryptographic Failures | A04:2025 Cryptographic Failures | — |
| A03:2021 Injection | A05:2025 Injection | Moved down from #3 |
| A04:2021 Insecure Design | A06:2025 Insecure Design | — |
| A07:2021 Identification and Auth | A07:2025 Authentication Failures | Renamed, same scope |
| A08:2021 Software and Data Integrity | A08:2025 Software and Data Integrity Failures | — |
| A09:2021 Security Logging | A09:2025 Security Logging and Alerting Failures | Added alerting emphasis |
| A10:2021 SSRF | A10:2025 Mishandling of Exceptional Conditions | **NEW** — SSRF moved under A01 |

---

## A01:2025 — Broken Access Control

Still #1. 100% of tested apps had some form of broken access control. Now includes SSRF, CSRF, path traversal, forced browsing.

### What to Look For
- Missing authorization checks on endpoints
- IDOR — sequential/integer IDs without ownership validation
- Path traversal in file paths: `../`, absolute paths, symlink following
- SSRF — user-supplied URLs used in server requests (moved from A10:2021)
- CSRF — missing anti-CSRF tokens on state-changing requests
- CORS misconfiguration: `Access-Control-Allow-Origin: *` with credentials
- JWT without signature verification, `alg: none`, long-lived tokens without refresh
- Force browsing to privileged/admin pages
- Elevation of privilege via parameter tampering

### Detection Patterns
```python
# IDOR
@app.get("/api/accounts/{acct}")
def get_account(acct: str):
    return db.accounts.find(acct)  # No ownership check

# SSRF (now in A01)
url = request.args.get('url')
response = requests.get(url)  # Attacker: http://169.254.169.254/

# Path traversal
file_path = f"/uploads/{request.args['file']}"  # ../../../etc/passwd
```

### Validation Questions
- Does every endpoint check the user owns the resource?
- Are admin-only operations restricted to admin roles?
- Are file paths validated against a base directory?
- Is SSRF blocked (whitelist protocols, block internal IPs)?

---

## A02:2025 — Security Misconfiguration

Moved up from #5 to #2. Includes missing security hardening, unnecessary features, default accounts, verbose errors.

### What to Look For
- Missing security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- Verbose error pages revealing stack traces, framework versions, DB errors
- Default credentials or admin panels accessible
- Unnecessary HTTP methods enabled (PUT, DELETE, TRACE)
- Directory listing enabled
- Debug mode enabled in production (`DEBUG=True`, `debug: true`)
- Cloud storage (S3, GCS) with public access
- Outdated or missing patches on OS, web server, DBMS
- CORS allowing all origins

### Detection
```bash
grep -r "DEBUG\s*=\s*True" --include="*.py"
grep -r "debug:\s*true" --include="*.js" --include="*.json"
grep -r "Access-Control-Allow-Origin.*\*"
```

### Validation Questions
- Is debug/verbose error mode disabled in production?
- Are security headers present on all responses?
- Are unnecessary features, ports, and services disabled?

---

## A03:2025 — Software Supply Chain Failures

**New category replacing A06:2021 (Vulnerable and Outdated Components).** Covers the full software supply chain: dependencies, build tools, CI/CD, IDE plugins, artifact repositories.

### What to Look For
- Unpinned dependency versions in `package.json`, `requirements.txt`, `pom.xml`
- Unmaintained or deprecated packages
- No SBOM (Software Bill of Materials) generated or tracked
- Components from untrusted sources (random GitHub repos, unverified npm packages)
- CI/CD pipeline with weaker security than production
- No separation of duty — same person can write and deploy code
- IDE extensions or build plugins from untrusted vendors
- No regular vulnerability scanning of dependencies

### Detection Patterns
```python
# Unpinned dependencies
# requirements.txt:
requests>=2.0   # Unpinned — could pull vulnerable version
flask==*        # Wildcard

# Untrusted model source (also LLM supply chain)
model = AutoModel.from_pretrained(user_supplied_repo)
```

### Dependency Scanning Commands
```bash
npm audit                    # Node.js
pip-audit                    # Python
safety check                 # Python
trivy fs .                   # Docker/container/filesystem
snyk test                    # Multi-language
```

### Validation Questions
- Are all dependencies pinned to specific versions with hashes?
- Is there an SBOM generated and reviewed regularly?
- Is the CI/CD pipeline hardened (MFA, access control, signed builds)?
- Are dependencies from official/trusted sources only?

---

## A04:2025 — Cryptographic Failures

Sensitive data must be protected in transit and at rest.

### What to Look For
- Plain HTTP for pages handling credentials/tokens/PII
- Weak hashing: MD5, SHA1 for passwords
- Hardcoded cryptographic keys, IVs, salts
- ECB cipher mode, CBC without HMAC
- `random` module for security-critical randomness
- Missing `secure`, `httpOnly`, `SameSite` on cookies
- Weak TLS configuration (TLS 1.0/1.1, weak ciphers)

### Detection Patterns
```python
# Weak hash
hashlib.md5(password.encode()).hexdigest()

# Hardcoded key
ENCRYPTION_KEY = "my-secret-123"  # Hardcoded

# Weak randomness
import random
reset_token = ''.join(random.choices(string.ascii_letters, k=32))
```

### Validation Questions
- Passwords hashed with bcrypt/scrypt/argon2 (≥12 salt rounds)?
- Keys loaded from environment/secret store, never in code?
- All pages served over HTTPS?

---

## A05:2025 — Injection

Moved from #3 to #5. User-supplied data interpreted as commands by an interpreter.

### What to Look For
- SQL: String concatenation/f-strings in queries
- NoSQL: Unsanitized input in `$where`, `$regex`
- OS Command: `shell=True`, `os.system()`, `exec()` with user input
- LDAP, XPath, XXE injection
- SSTI: user input reaching template engines (Jinja2, Twig, ERB)
- Log injection via unsanitized user input containing `\n`

### Detection Patterns
```python
# SQL Injection
cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")
db.query("SELECT * FROM users WHERE email = '" + email + "'")

# Command Injection
os.system(f"ping {user_input}")
subprocess.call(user_input, shell=True)

# SSTI
render_template_string(f"Hello {user_input}")
```

### Validation Questions
- All database queries parameterized (prepared statements, ORM bindings)?
- Is `shell=True` ever used with user-supplied data?
- Are template variables auto-escaped?

---

## A06:2025 — Insecure Design

Missing or ineffective security controls designed into the architecture.

### What to Look For
- Client-side-only validation
- Predictable token generation (timestamps, sequential values)
- Missing threat models for critical flows
- Security questions as sole recovery mechanism
- Unlimited login attempts without lockout or CAPTCHA
- Missing MFA on sensitive operations

### Detection
```javascript
// Client-only validation
<input required pattern="[0-9]+">  // No server check

// Predictable token
const resetToken = Date.now().toString(36);
```

### Validation Questions
- Is input validated on both client and server?
- Are business logic constraints enforced server-side?
- Are sensitive flows rate-limited and require MFA?

---

## A07:2025 — Authentication Failures

Weaknesses in authentication and session management.

### What to Look For
- Weak password policies (no minimum length)
- No brute-force protection on login
- Session tokens in URLs
- Sessions not invalidated on logout or password change
- Auth bypass via parameter pollution (`?admin=true`)
- Weak "remember me" implementation
- User identity from untrusted source (query params, custom headers)

### Detection
```javascript
// Session in URL
res.redirect(`/dashboard?token=${sessionId}`);

// Auth bypass
if (req.query.isAdmin === "true") { grantAccess(); }
```

### Validation Questions
- Sessions invalidated server-side on logout?
- Rate limiting on login attempts?
- MFA available for sensitive operations?

---

## A08:2025 — Software and Data Integrity Failures

Insecure deserialization, CI/CD integrity, untrusted updates.

### What to Look For
- `pickle.loads()`, `yaml.load()`, `eval()` with user data
- Auto-update over HTTP without signature verification
- CI/CD modifiable by PR contributors
- CDN scripts without Subresource Integrity (SRI) hashes
- Container images without provenance/signing

### Detection Patterns
```python
# Unsafe deserialization
data = pickle.loads(request.body)
user = yaml.load(request.data)  # Not safe_load!

# Missing SRI
<script src="https://cdn.example.com/lib.js"></script>  # No integrity attr
```

### Validation Questions
- Is user-controllable data ever deserialized?
- Are CDN scripts loaded with integrity hashes?
- Are update/dependency pipelines protected from tampering?

---

## A09:2025 — Security Logging and Alerting Failures

Insufficient logging, detection, monitoring, and active response.

### What to Look For
- No logging of auth events (login success/failure, password changes)
- No logging of authorization failures (403 events)
- No alerting for suspicious patterns (brute force, unusual hours)
- Logs stored only locally without centralized aggregation
- Sensitive data in logs (passwords, tokens, PII)
- Log injection via unsanitized input with `\n` or `\r`

### Detection
```java
// Log injection
logger.info("User " + username + " logged in");  // username="admin\nLogin successful"

// Logging sensitive data
log.error("Auth failed: password=" + password);
```

### Validation Questions
- Are login attempts (success/failure) logged?
- Are logs forwarded to a central system with alerting?
- Is sensitive data excluded from log entries?

---

## A10:2025 — Mishandling of Exceptional Conditions

**New category for 2025.** Focuses on improper error handling, failing open, logic bugs from unhandled exceptions, and resource leaks.

### What to Look For
- Uncaught exceptions in critical paths (payment, auth, data mutations)
- Failing open — defaulting to granting access on error
- Generic `catch (Exception e)` with no recovery or rollback
- Resource leaks — file handles, connections not released on exception
- Sensitive data in error messages (stack traces, SQL queries, paths)
- Transaction rollback not performed on partial failure
- Null pointer dereference not checked
- Missing error handling in async/await chains

### Detection Patterns
```python
# Failing open
try:
    user = authenticate(credentials)
except Exception:
    user = User(role="admin")  # Default to admin on error!

# Uncaught exception in transaction
def transfer(from_acct, to_acct, amount):
    debit(from_acct, amount)        # Succeeds
    credit(to_acct, amount)         # May throw!
    # No rollback if credit() fails

# Sensitive data in error
try:
    db.query(user_input)
except Exception as e:
    return {"error": str(e)}  # Exposes SQL details
```

```javascript
// Unhandled promise
async function processPayment(order) {
    await chargeCustomer(order);     // May throw
    await updateInventory(order);    // Never runs if above throws
    // No catch block -> inventory inconsistency
}

// Generic catch swallowing errors
try {
    riskyOperation();
} catch (e) {
    // Silent — no log, no rollback, no user feedback
}
```

### Validation Questions
- Do error handlers fail closed (deny by default on unexpected errors)?
- Are transactions rolled back completely on any failure?
- Are resources (connections, file handles) released in `finally` blocks?
- Do error messages avoid exposing internal details (stack traces, SQL)?
- Is there a global exception handler as safety net?

---

## Quick Reference: Grep Patterns for 2025

| Category | Keyword Pattern |
|----------|----------------|
| A01 Access Control | `@app.route` / `@router` without auth decorator; `requests.get(` with user input; `path.join` with user input |
| A02 Misconfig | `debug=True` / `DEBUG = True` / `CORS(*` / missing security headers |
| A03 Supply Chain | Unpinned versions in lockfiles; `from_pretrained(`; `npm audit` / `pip-audit` results |
| A04 Crypto | `md5(` / `sha1(` / hardcoded `KEY` / `SECRET` / `random.randint` for tokens |
| A05 Injection | f-string in SQL / `shell=True` / `system(` with concat / `innerHTML` / `eval(` |
| A06 Insecure Design | Client-only validation / `Date.now()` for tokens / no server check on required fields |
| A07 Auth Failures | session in URL / `?admin=true` / `jwt.decode` without verify / no rate limit |
| A08 Integrity | `pickle.loads` / `yaml.load` (not safe) / `eval(` with user data / no SRI |
| A09 Logging | no login logging / `password` in log statements / log injection |
| A10 Exceptions | Generic `catch (Exception)` / no `finally` / no rollback / sensitive `str(e)` returned |
