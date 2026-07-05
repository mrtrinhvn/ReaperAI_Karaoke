---
name: documentation-templates
description: Documentation structure rules. README, API docs, ADR, AI-friendly docs.
priority: P2
---

## When to Activate

- Writing README, API docs, changelogs, ADRs
- Structuring project documentation

# Documentation Rules

> AI model đã biết markdown, JSDoc, changelog format.
> File này = structure rules + khi nào dùng gì.

---

## README Structure (Priority Order)

| Section | Purpose | Required? |
|---|---|---|
| Title + One-liner | What is this? | ✅ |
| Quick Start | Running in <5 min | ✅ |
| Features | What can I do? | ✅ |
| Configuration | Env vars, options | ✅ if configurable |
| API Reference | Link to detailed docs | ✅ if API |
| Contributing | How to help | Optional |
| License | Legal | ✅ |

## Code Comment Rules

| ✅ Comment | ❌ Don't Comment |
|---|---|
| WHY (business logic, non-obvious) | WHAT (obvious from code) |
| Complex algorithms | Every line |
| API contracts, edge cases | Self-explanatory code |

## ADR Template

```
# ADR-NNN: [Title]
## Status: Accepted / Deprecated / Superseded
## Context: Why?
## Decision: What?
## Consequences: Trade-offs?
```

## Changelog (Keep a Changelog)

```
## [Unreleased]
### Added / Changed / Fixed / Removed

## [1.0.0] - YYYY-MM-DD
### Added
- Initial release
```

## AI-Friendly Documentation (llms.txt)

```markdown
# Project Name
> One-line objective.

## Core Files
- [src/index.ts]: Main entry
- [src/api/]: API routes

## Key Concepts
- Concept 1: Brief explanation
```

**MCP-Ready rules:**
- Clear H1-H3 hierarchy
- JSON/YAML examples for data structures
- Mermaid diagrams for flows
- Self-contained sections

## Structure Principles

- **Scannable**: Headers, lists, tables over paragraphs
- **Examples first**: Show, don't just tell
- **Progressive detail**: Simple → Complex
- **Up to date**: Outdated docs = misleading. Delete stale docs
