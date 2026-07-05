# 🧠 AG-KIT Deep Rules (v3.2)

> Loaded ON-DEMAND from root GEMINI.md. Contains UNIQUE rules not in root pointer.
> DO NOT duplicate content from root GEMINI.md here.

---

## 🧠 LAZY SKILL ACTIVATION (MANDATORY)

```
❌ WRONG: Session start → Read 70 SKILL.md files (60K tokens wasted)
✅ CORRECT: Read skills_registry.json (~3K tokens)
           → User request → Match 2-3 skills → Read those SKILL.md only
```

**Priority:** P0 (GEMINI.md) > P1 (Agent .md) > P2 (SKILL.md)

**Quick Route (bypass registry for common patterns):**

| Keywords in request | Agent | Primary Skills |
|:--|:--|:--|
| fix, bug, error, crash | `backend-specialist` | clean-code |
| UI, page, component, CSS | `frontend-specialist` | frontend-design |
| deploy, ship, release | `orchestrator` | deployment-procedures |
| test, spec, coverage | `orchestrator` | testing-patterns, tdd-workflow |
| security, auth, token | `security-auditor` | vulnerability-scanner |
| database, schema, migration | `backend-specialist` | database-design |
| mobile, iOS, Android, Flutter | `mobile-developer` | mobile-design |
| plan, design, architect | `project-planner` | plan-writing, architecture |

> If request matches Quick Route → load agent + skills directly, skip registry.
> If ambiguous → load `skills_registry.json` for full matching.

---

## 🧠 MEMORY DISAMBIGUATION

**Two distinct memory systems exist — never confuse them:**

1. **Agentic Memory** (AI's brain): `.agent/skills/`, `.agent/knowledge/`, Memory MCP, `decisions.jsonl`
2. **Domain Memory** (App's brain): SQLite, PostgreSQL, Product DB, User Facts, Cache

**Auto-Identify** which one user means. If ambiguous → ASK.

---

## ⏳ TEMPORAL MEMORY

- If code changes affect architecture/API → update `.agent/knowledge/` IN SAME TASK.
- Mark outdated rules as `deprecated` with timestamp — never silently delete.
- Rely on VFS for real-time code layout, `.agent/knowledge/` for intent/rules/history.
- Log durable decisions: `bash .agent/decisions/decision-log.sh log "..." "..."`
- Record **failed approaches** in session context — prevent repeating mistakes.
