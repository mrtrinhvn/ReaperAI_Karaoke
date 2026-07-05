# Testing Review Specialist Checklist

> Scope: Mọi code change có logic mới hoặc thay đổi behavior.
> Output: Structured findings với severity, confidence, path, category, summary, fix.

---

## Categories

### Coverage Gaps
- New public function/method without corresponding test
- New error path without test (catch block, error handler)
- New conditional branch without test for both true/false
- Edge cases: empty array, null input, boundary values untested
- Integration point (API call, DB query) without integration test

### Test Quality
- Test that always passes regardless of implementation (tautological)
- Assert on implementation detail instead of behavior
- Missing assertion (test runs code but doesn't verify result)
- Brittle test: depends on execution order, timing, or external state
- Copy-pasted test with only minor value changes (use parameterized)

### Test Isolation
- Test that modifies global/shared state without cleanup
- Test that depends on another test running first
- Test that makes real network calls (should be mocked)
- Test that reads/writes real files without temp directory

### Error Path Testing
- Happy path tested but error path untested
- Exception type verified but message/context not checked
- Retry logic without test for max-retries exceeded
- Timeout behavior untested
- Graceful degradation path untested

### Regression Prevention
- Bug fix without regression test that would catch recurrence
- Refactor without verifying all existing tests still pass
- Behavior change without updating affected tests
