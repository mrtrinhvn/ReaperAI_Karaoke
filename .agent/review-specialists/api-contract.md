# API Contract Review Specialist Checklist

> Scope: Khi diff chứa API endpoints, request/response schemas, hoặc API documentation.
> Output: Structured findings với severity, confidence, path, category, summary, fix.

---

## Categories

### Breaking Changes
- Removed or renamed fields in response payloads
- Changed field types (string→number, nullable→required)
- Removed or renamed endpoints
- Changed HTTP methods for existing endpoints
- Modified authentication requirements without migration path

### Versioning & Compatibility
- Missing API version in URL or headers
- No deprecation notice for removed features
- Breaking changes without version bump
- Inconsistent versioning across related endpoints

### Request/Response Contract
- Missing required field validation (400 vs silent null)
- Inconsistent error response format across endpoints
- Missing Content-Type headers
- Undocumented query parameters or request body fields
- Response shape changes based on user role without documentation

### Pagination & Filtering
- List endpoints without consistent pagination format
- Missing total count in paginated responses
- Inconsistent sort parameter naming
- Filter parameters that allow injection

### Rate Limiting & Quotas
- Missing rate limit headers (X-RateLimit-*)
- Inconsistent rate limiting across related endpoints
- No retry-after header on 429 responses
- Missing documentation for rate limits
