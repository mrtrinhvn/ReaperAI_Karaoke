# Red Team Review Specialist Checklist

> Scope: Khi PR chứa user-facing features, payment logic, hoặc data access patterns.
> Output: Structured findings với severity, confidence, path, category, summary, fix.

---

## Categories

### Adversarial Input
- What happens with 10MB request body?
- What happens with 100K items in array parameter?
- What happens with Unicode control characters in text fields?
- What happens with SQL/NoSQL operators in filter parameters?
- What happens with deeply nested JSON (100 levels)?

### Race Conditions
- Double-submit on payment/transfer endpoint
- TOCTOU (time-of-check-to-time-of-use) on authorization checks
- Concurrent updates to same resource without optimistic locking
- Race between delete and read on cached data
- Parallel requests that each create "unique" resource

### Business Logic Abuse
- Can user set their own price/discount?
- Can user reference another user's resources by changing ID?
- Can user skip required steps in a multi-step flow?
- Can user replay a one-time action (coupon, free trial)?
- Can user access admin functionality via direct API call?

### Information Leakage
- Error messages revealing internal paths, versions, or stack traces
- Timing attacks on authentication (different response time for valid/invalid user)
- Enumeration attacks (different response for existing/non-existing resource)
- Debug endpoints or verbose logging left in production code
- Metadata in API responses revealing internal IDs or implementation details

### Denial of Service
- Endpoint without rate limiting that does heavy computation
- Regex with catastrophic backtracking on user input (ReDoS)
- Unbounded file upload without size limit
- Recursive operation without depth limit
- Cache poisoning via manipulated cache keys
