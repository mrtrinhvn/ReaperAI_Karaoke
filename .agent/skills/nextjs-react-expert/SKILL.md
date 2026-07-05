---
name: nextjs-react-expert
description: React & Next.js performance optimization rules. 57 rules from Vercel Engineering, organized by impact.
priority: P2
---

## When to Activate

- Building React/Next.js components
- Performance optimization or review
- Bundle size reduction

# Next.js & React Performance Rules

> 57 rules from Vercel Engineering, organized by impact.
> SKILL.md = routing. Deep rules in sub-files.

---

## Quick Decision Tree

| Symptom | Read file | Impact |
|---|---|---|
| Slow page loads / TTI | [1-async-eliminating-waterfalls.md](1-async-eliminating-waterfalls.md) | 🔴 CRITICAL |
| Large bundle (>200KB) | [2-bundle-bundle-size-optimization.md](2-bundle-bundle-size-optimization.md) | 🔴 CRITICAL |
| Slow SSR / API routes | [3-server-server-side-performance.md](3-server-server-side-performance.md) | 🟠 HIGH |
| Client data fetching | [4-client-client-side-data-fetching.md](4-client-client-side-data-fetching.md) | 🟡 MEDIUM |
| Excessive re-renders | [5-rerender-re-render-optimization.md](5-rerender-re-render-optimization.md) | 🟡 MEDIUM |
| Rendering bottlenecks | [6-rendering-rendering-performance.md](6-rendering-rendering-performance.md) | 🟡 MEDIUM |
| Micro-optimizations | [7-js-javascript-performance.md](7-js-javascript-performance.md) | ⚪ LOW |
| Advanced patterns | [8-advanced-advanced-patterns.md](8-advanced-advanced-patterns.md) | 🔵 VARIABLE |

> ⚠️ KHÔNG đọc tất cả. Chỉ đọc file theo symptom.

## Hard Rules (Luôn Áp Dụng)

### Critical (Must)
- ✅ `Promise.all()` for independent data fetching. CẤM sequential await
- ✅ Dynamic imports for large components: `dynamic(() => import('./Heavy'))`
- ✅ Direct imports: `import { x } from 'lib/x'`. CẤM barrel imports in app code
- ✅ Bundle main < 200KB
- ✅ Server Components by default. Client Components only khi cần interactivity

### High
- ✅ Suspense boundaries for data fetching
- ✅ Static generation (SSG) where possible
- ✅ No N+1 queries in API routes
- ✅ `next/image` for all images, `next/font` for fonts

### Anti-Patterns
- ❌ `useEffect` for data fetching without deduplication (dùng SWR/TanStack Query)
- ❌ Client components when server components work
- ❌ Memoize everything (only expensive computations)
- ❌ Optimize before measuring (React DevTools Profiler first)

## Performance Review Checklist

```
Critical:
[ ] No sequential await for independent ops?
[ ] Bundle < 200KB? No barrel imports?
[ ] Dynamic imports for heavy components?
[ ] Parallel data fetching?

High:
[ ] Server components where appropriate?
[ ] No N+1 queries? Suspense boundaries?
[ ] Static generation used?

Medium:
[ ] Expensive computations memoized?
[ ] Lists >100 items virtualized?
[ ] Images via next/image?
```

## Scripts

| Script | Usage |
|---|---|
| `scripts/react_performance_checker.py` | `python scripts/react_performance_checker.py <path>` |
