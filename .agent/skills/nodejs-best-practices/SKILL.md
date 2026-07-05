---
name: nodejs-best-practices
description: Node.js decision-making rules. Framework selection, architecture patterns, security mindset.
priority: P2
---

## When to Activate

- Building Node.js backend / API
- Choosing framework, runtime, or architecture pattern

# Node.js Decision Rules

> AI model đã biết Node.js, Express, async/await, event loop.
> File này chỉ chứa DECISION RULES — khi nào chọn gì, và hard rules cần tuân thủ.

---

## Framework Selection (2025)

| Building what? | Use | Why |
|---|---|---|
| Edge/Serverless (Cloudflare, Vercel) | **Hono** | Zero-dep, fastest cold starts |
| High Performance API | **Fastify** | 2-3x faster than Express |
| Enterprise / Team familiarity | **NestJS** | DI, decorators, structured |
| Legacy / Maximum ecosystem | **Express** | Mature, most middleware |
| Full-stack with frontend | **Next.js API Routes / tRPC** | Co-located |

**Rule:** Hỏi user preference trước. Không default Express cho project mới.

## Runtime Selection

| Runtime | Best for |
|---|---|
| **Node.js 22+** | General purpose. Native TS (--experimental-strip-types) |
| **Bun** | Performance, built-in bundler |
| **Deno** | Security-first, built-in TS |

**Rule:** New projects → ESM (import/export). CJS chỉ cho legacy compatibility.

## Architecture Rules

- ✅ ≥3 routes → layered: Controller (HTTP) → Service (business) → Repository (data)
- ✅ Business logic PHẢI framework-agnostic (testable, swappable)
- ✅ Validate at API boundary (Zod/Valibot), not in service layer
- ✅ Centralized error handler middleware. Custom error classes. No try-catch scatter
- ❌ CẤM sync methods in production (fs.readFileSync, etc.)
- ❌ CẤM CPU-bound work on main thread → worker_threads hoặc offload

## Validation Library Selection

| Library | Best for |
|---|---|
| **Zod** | TypeScript-first, inference |
| **Valibot** | Smaller bundle (tree-shakeable) |
| **ArkType** | Performance critical |

## Testing Strategy

| Type | Purpose | Tool |
|---|---|---|
| Unit | Business logic | `node:test` (built-in) or Vitest |
| Integration | API endpoints | Supertest |
| E2E | Full flows | Playwright |

**Priority:** Critical paths → Edge cases → Error handling. Skip trivial getters.

## Anti-Patterns

- ❌ Express for new edge projects. ❌ Business logic in controllers
- ❌ Hardcode secrets. ❌ Trust external data without validation
- ❌ Skip input validation. ❌ Block event loop with CPU work
