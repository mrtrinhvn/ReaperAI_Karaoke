# Security Review Specialist Checklist

> Scope: Khi diff chứa auth, API endpoints, user input handling, hoặc >100 dòng backend code.
> Output: Structured findings với severity, confidence, path, category, summary, fix.

---

## Categories

### Input Validation at Trust Boundaries
- User input accepted without validation at controller/handler level
- Query parameters used directly in database queries or file paths
- Request body fields accepted without type checking or schema validation
- File uploads without type/size/content validation
- Webhook payloads processed without signature verification

### Auth & Authorization Bypass
- Endpoints missing authentication middleware
- Authorization checks that default to "allow" instead of "deny"
- Role escalation paths (user can modify their own role/permissions)
- Direct object reference vulnerabilities (IDOR)
- Session fixation or session hijacking opportunities
- Token/API key validation that doesn't check expiration

### Injection Vectors
- SQL injection via string interpolation in queries
- Command injection via subprocess calls with user-controlled arguments
- Template injection (Jinja2, Handlebars) with user input
- SSRF via user-controlled URLs (fetch, redirect, webhook targets)
- Path traversal via user-controlled file paths (../../etc/passwd)
- XSS via dangerouslySetInnerHTML, v-html, innerHTML

### Cryptographic Misuse
- Weak hashing (MD5, SHA1) for security-sensitive operations
- Predictable randomness (Math.random) for tokens or secrets
- Non-constant-time comparisons on secrets/tokens
- Hardcoded encryption keys or IVs
- Missing salt in password hashing

### Secrets Exposure
- API keys, tokens, or passwords in source code
- Secrets logged in application logs or error messages
- Credentials in URLs or error responses
- PII stored in plaintext when encryption is expected
