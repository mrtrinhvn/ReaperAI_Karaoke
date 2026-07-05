# Maintainability Review Specialist Checklist

> Scope: Mọi PR có >200 dòng code thay đổi hoặc thêm module mới.
> Output: Structured findings với severity, confidence, path, category, summary, fix.

---

## Categories

### Code Organization
- God class/module (>500 lines, >10 responsibilities)
- Circular dependencies between modules
- Business logic in controller/handler layer (should be in service)
- Duplicated logic across files (DRY violation >10 lines)
- Mixed abstraction levels in same function

### Naming & Readability
- Variable/function names that don't describe purpose
- Boolean parameters without named argument (fn(true, false, true))
- Magic numbers without named constants
- Inconsistent naming convention within module
- Abbreviations that aren't universally understood

### Error Handling
- Generic catch-all without specific error types
- Swallowed exceptions (empty catch block) on non-cleanup paths
- Error messages that don't help debugging (no context, no values)
- Missing error propagation (function silently returns null on failure)
- Inconsistent error handling pattern across related functions

### Dependencies
- New dependency for functionality achievable with stdlib
- Dependency without pinned version
- Dependency with known vulnerabilities (check CVE)
- Dependency that hasn't been updated in >2 years
- Multiple dependencies solving same problem

### Documentation Debt
- Public API without JSDoc/docstring
- Complex algorithm without explanation comment
- Non-obvious business rule without "why" comment
- README not updated after architectural change
- Missing CHANGELOG entry for user-facing change
