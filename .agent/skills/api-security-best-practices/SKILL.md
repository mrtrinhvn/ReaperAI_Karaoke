---
name: api-security-best-practices
description: "API security rules: auth, validation, rate limiting, OWASP Top 10 compliance."
priority: P2
---

## When to Activate

- Designing new API endpoints
- Securing existing APIs
- Implementing auth/authz
- Security reviews or audits

# API Security Rules

> AI models đã biết viết JWT, Zod validation, Helmet, rate limiting.
> File này chỉ chứa RULES đặc thù — không tutorials, không code examples.

---

## Hard Rules (Luôn Áp Dụng)

### Authentication
- ✅ JWT access tokens: max 1h expiry. Refresh tokens: max 7d, stored in DB (revocable)
- ✅ JWT secret: ≥ 256-bit, from env var. CẤM hardcode
- ❌ CẤM reveal user existence on login failure. Dùng generic "Invalid credentials"
- ✅ Auth endpoints: strict rate limit (5 attempts / 15 min)

### Authorization
- ✅ Kiểm tra ownership/role TRƯỚC KHI thao tác (not just authentication)
- ✅ RBAC: role check tại middleware, không inline trong handler
- ❌ CẤM trust client-side role claims

### Input Validation
- ✅ Schema validation (Zod/Joi/class-validator) tại API boundary — trước business logic
- ✅ Parameterized queries hoặc ORM. CẤM string concatenation cho SQL
- ✅ Sanitize HTML output (DOMPurify). Allowlist tags, không blocklist
- ✅ File uploads: validate type + size + content. Max 10MB default

### Rate Limiting
- ✅ General API: 100 req / 15 min per user/IP
- ✅ Auth endpoints: 5 req / 15 min, skip successful
- ✅ Expensive operations: 10 req / hour
- ✅ Return standard headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### Data Protection
- ✅ HTTPS only. HSTS enabled (max-age 31536000)
- ✅ Security headers via Helmet: CSP, X-Frame-Options DENY, noSniff, hidePoweredBy
- ❌ CẤM expose stack traces in production. Generic error messages only
- ❌ CẤM log passwords, tokens, PII
- ✅ Select fields explicitly (no `SELECT *`). CẤM return passwordHash

### CORS
- ✅ Explicit allowlist origins. CẤM `Access-Control-Allow-Origin: *` cho authenticated endpoints

---

## OWASP API Top 10 Quick Reference

| # | Risk | Prevention Rule |
|---|---|---|
| 1 | Broken Object Level Auth | Check ownership every endpoint |
| 2 | Broken Authentication | Strong JWT + rate limit auth |
| 3 | Broken Object Property Level Auth | Allowlist fields in response |
| 4 | Unrestricted Resource Consumption | Rate limiting + pagination |
| 5 | Broken Function Level Auth | RBAC middleware, not inline |
| 6 | Unrestricted Access to Sensitive Flows | Rate limit + CAPTCHA |
| 7 | Server Side Request Forgery | Validate URLs, block internal IPs |
| 8 | Security Misconfiguration | Helmet + env vars + audit deps |
| 9 | Improper Inventory Management | Document all endpoints, deprecate properly |
| 10 | Unsafe Consumption of APIs | Validate all third-party API responses |
