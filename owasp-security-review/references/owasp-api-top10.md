# OWASP API Security Top 10 (2023) — Detection Guide

API-specific vulnerabilities beyond the standard OWASP Top 10. Focuses on authorization, resource management, and API lifecycle risks.

## API1:2023 — Broken Object Level Authorization (BOLA)

Attackers manipulate object IDs in API requests to access resources they shouldn't.

### What to Look For
- API endpoints using user-supplied IDs without ownership verification
- UUID/sequential IDs in URL paths (`/api/orders/{id}`) with no authorization check
- Array of IDs in request body bypassable by modifying one ID

### Detection Patterns
```python
# VULNERABLE — no ownership check
@router.get("/api/users/{user_id}/invoices/{invoice_id}")
def get_invoice(user_id: str, invoice_id: str):
    return db.invoices.find(invoice_id)  # Doesn't verify invoice belongs to user_id

# SAFE
@router.get("/api/invoices/{invoice_id}")
def get_invoice(invoice_id: str, current_user=Depends(get_current_user)):
    invoice = db.invoices.find(invoice_id)
    if invoice.user_id != current_user.id:
        raise HTTPException(403)
    return invoice
```

### Validation Questions
- Does every API endpoint that accepts resource IDs verify ownership?
- Are authorization checks consistent across GET, POST, PUT, DELETE?

---

## API2:2023 — Broken Authentication

Weak or missing authentication on API endpoints.

### What to Look For
- API endpoints without any authentication requirement
- Weak JWT configuration (`alg: none`, no signature verification, long expiry)
- API keys in URLs or query strings
- Token validation that only checks signature, not expiration

### Detection
```bash
# Find endpoints without auth decorators
grep -r "@router\.(get|post|put|delete)" --include="*.py" \
  | grep -v "Depends(get_current_user)" | grep -v "require_auth"
```

---

## API3:2023 — Broken Object Property Level Authorization

Mass assignment / excessive data exposure in API responses or requests.

### What to Look For
- API endpoints accepting or returning entire objects without field filtering
- Users able to set `role=admin` or `isAdmin=true` via request body
- Responses leaking internal fields (`password_hash`, `internal_notes`, `ssn`)

### Detection Patterns
```javascript
// VULNERABLE — mass assignment
app.patch('/api/users/:id', (req, res) => {
  db.users.update(req.params.id, req.body);  // Attacker: {"role": "admin"}
});

// VULNERABLE — excessive exposure
app.get('/api/users/:id', (req, res) => {
  res.json(db.users.find(req.params.id));  // Returns password_hash, token, etc.
});

// SAFE — whitelist fields
const allowed = ['name', 'email', 'bio'];
const updates = pick(req.body, allowed);
res.json(sanitizeUser(user));  // Explicit field selection
```

### Validation Questions
- Are API responses filtered to expose only necessary fields?
- Are request bodies validated against a whitelist of allowed properties?

---

## API4:2023 — Unrestricted Resource Consumption

No limits on API resource usage leading to DoS or cost spikes.

### What to Look For
- Missing pagination on list endpoints (returns all records)
- No request size limits (accepts arbitrarily large payloads)
- No rate limiting on any endpoint
- Expensive queries without timeouts (graphQL without depth/complexity limits)

### Detection Patterns
```python
# VULNERABLE — no pagination
@router.get("/api/users")
def list_users():
    return db.users.all()  # Returns 1M records

# VULNERABLE — no payload limit
@router.post("/api/upload")
async def upload(file: UploadFile):  # No size check
    contents = await file.read()  # Could be 10GB

# SAFE
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.get("/api/users")
@limiter.limit("100/minute")
def list_users(page: int = 1, size: int = 50):
    return db.users.paginate(page, size)
```

### Validation Questions
- Do all list endpoints have pagination with reasonable max page sizes?
- Are upload endpoints size-limited?
- Is rate limiting applied to all public API endpoints?

---

## API5:2023 — Broken Function Level Authorization

Users accessing administrative functions due to missing role checks.

### What to Look For
- Admin endpoints without `@require_admin` or role middleware
- Role checks performed only on the frontend
- HTTP method confusion (GET on admin-only POST still executes)

### Detection
```bash
# Find routes with "admin" in path lacking admin decorators
grep -r "admin" --include="*.py" | grep "@router" \
  | grep -v "require_admin\|has_role\|is_admin"
```

---

## API6:2023 — Unrestricted Access to Sensitive Business Flows

Abuse of legitimate business flows at scale (scalping, scraping, automated fraud).

### What to Look For
- Purchase/reservation endpoints without anti-automation controls
- No CAPTCHA or bot detection on critical flows
- Missing device fingerprinting or behavioral analysis
- Sequential/reserved identifiers that can be enumerated

### Detection Patterns
```python
# VULNERABLE — no abuse prevention
@router.post("/api/products/{id}/purchase")
def purchase(id: str, user=Depends(get_current_user)):
    return checkout_service.process(id, user)  # Bot can call 1000x/sec

# SAFE — rate limit + anti-bot
@router.post("/api/products/{id}/purchase")
@limiter.limit("5/minute")
@require_captcha
def purchase(id: str, user=Depends(get_current_user)):
    return checkout_service.process(id, user)
```

---

## API7:2023 — Server Side Request Forgery (SSRF)

See A10:2021 in the web app reference. Identical detection patterns apply.

Additional API-specific concerns:
- Webhook endpoints that follow user-supplied callback URLs
- File import from URL features in API processing pipelines

---

## API8:2023 — Security Misconfiguration

See A05:2021 in the web app reference. Additional API-specific concerns:

- Unnecessary HTTP methods enabled (OPTIONS, TRACE, HEAD unrestricted)
- Verbose error messages exposing stack traces in JSON responses
- CORS allowing all origins with credentials
- Missing `X-Content-Type-Options: nosniff`

### Detection
```bash
# Check for wildcard CORS
grep -r "Access-Control-Allow-Origin.*\*" --include="*.py" --include="*.js"
# Check for DEBUG mode
grep -r "DEBUG\s*=\s*True\|debug:\s*true" --include="*.py" --include="*.js"
```

---

## API9:2023 — Improper Inventory Management

Exposing old, deprecated, or debug API versions.

### What to Look For
- Old API versions still accessible (`/api/v1/`, `/api/beta/`)
- Debug/staging endpoints in production (`/api/debug/`, `/api/test/`)
- Exposed API documentation (Swagger UI, GraphQL introspection) in production
- Unused endpoints from previous versions without proper deprecation notices

### Detection
```bash
# Find old API version prefixes
grep -rE "(v1|beta|debug|test|staging|internal)" --include="*.py" | grep -i "route\|prefix"
# Check for Swagger/OpenAPI in production
grep -r "swagger\|openapi\|redoc" --include="*.py"
```

### Validation Questions
- Are old API versions retired with proper sunset headers?
- Is API documentation restricted in production?
- Is there a complete, up-to-date API inventory?

---

## API10:2023 — Unsafe Consumption of APIs

Trusting third-party API responses without validation.

### What to Look For
- API responses from third parties passed directly to downstream consumers
- No validation of third-party response schemas
- SQL injection via data from external API responses
- Blind trust in webhook payloads from external services

### Detection Patterns
```python
# VULNERABLE — trusting external API response
data = requests.get(f"https://partner-api.com/user/{user_id}").json()
db.execute(f"INSERT INTO users VALUES ('{data['name']}', '{data['email']}')")

# SAFE — validate then use parameterized query
response = requests.get(f"https://partner-api.com/user/{user_id}")
data = response.json()
validated = PartnerUserSchema.parse(data)  # Zod-like schema validation
db.execute("INSERT INTO users (name, email) VALUES (?, ?)", [validated.name, validated.email])
```

### Validation Questions
- Are all third-party API responses schema-validated before use?
- Are webhook payloads cryptographically verified?

---

## Quick Reference: API Security Grep Patterns

| Category | Grep Pattern |
|----------|-------------|
| API1 BOLA | Route with `{id}` but no `Depends(get_current_user)` / no ownership check |
| API2 Auth | `@router` without `require_auth` / `jwt.decode` instead of `jwt.verify` |
| API3 Mass Assignment | `req.body` passed directly to `update()` / no `pick` or whitelist |
| API4 Resources | Missing `page`/`limit` params / no `Content-Length` check |
| API5 Function Auth | `admin` in path without role middleware |
| API6 Business Flows | No rate limit on purchase/submit/reserve endpoints |
| API7 SSRF | `requests.get(user_url)` / `urlopen(user_input)` |
| API8 Misconfig | `Access-Control-Allow-Origin: *` / `DEBUG = True` |
| API9 Inventory | `v1`, `beta`, `debug`, `test` in API route prefixes |
| API10 Unsafe Consume | no schema validation on `requests.get().json()` results |
