# 🚀 AG-KIT Core Rules (v3.2 — Post-GStack)

> Boot pointer only. AI reads this → then loads on-demand.
> Token budget: ~1,200 tokens (was ~6,300 in v1, ~4,500 in v2).

---

## 🌌 IDENTITY

Read `.agent/skills/ag-kit-core/SKILL.md` before complex actions.

---

## 🛠️ TOKEN SAVING PROTOCOL (5 LAYERS)

| Layer | Tool | When |
|:--|:--|:--|
| 1 | `.agent/brain/summary.md` | Session start |
| 2 | `.agent/skills_registry.json` | Skill/Agent discovery |
| 3 | VFS (`vfs search`, `graph.db`) | Code lookup |
| 4 | Memory MCP (`memory_search`) | Recalling past decisions |
| 5 | These rules (GEMINI.md) | Always loaded |

**Critical:** VFS before grep. Registry before SKILL.md. Memory before re-researching.

---

## 🔒 EDIT SAFETY LOCK

> 🔴 **CẤM GHI FILE MÀ KHÔNG ĐỌC TRƯỚC.**

1. ✅ Confirm file tồn tại (`view_file`)
2. ✅ Confirm target function/class còn tồn tại
3. ✅ File mới → `write_to_file` | File có nội dung → `replace_file_content` / `multi_replace_file_content`
4. ❌ **CẤM** `write_to_file(Overwrite=true)` lên file có nội dung

---

## 🤖 MODEL SELECTION

- **Simple Tasks**: Prefer local Ollama models (e.g., `nemotron`, `llama3`) to save cloud budget.
- **Complex Tasks**: Use high-tier models (e.g., `Gemini 2.5 Pro`).
- **Delegation Logic**: See `@[skills/intelligent-routing]` for Cloud/Local routing rules.
- **Cross-IDE**: See `.agent/adapters/` for IDE-specific rule generation.

---

## 🧠 MEMORY-FIRST PROTOCOL

**Before researching any topic, ALWAYS check memory first:**

```
1. memory_search(keyword) → Check if past decision/pattern exists
2. decisions/decisions.jsonl → Check if already decided
3. If found → Use it (verify against current code if stale)
4. If not found → Research normally → memory_save() the result
```

**After completing any significant task:**
- `memory_save()` key decisions, patterns, errors with tags
- Log durable decisions: `bash .agent/decisions/decision-log.sh log "..." "..."`
- Update `.agent/knowledge/` if architecture/API changed

**Disambiguate memory types:**
1. **Agentic Memory** (Não Agent): `.agent/skills/`, `.agent/knowledge/`, Memory MCP
2. **Domain Memory** (Não App): SQLite, Product DB, User Facts

---

## 🌐 UNIVERSAL RULES

- **Language:** Respond in user's language. Code in English.
- **Clean Code:** Follow `@[skills/clean-code]`. No over-engineering.
- **File Dependencies:** Check before modifying. Update ALL affected files.
- **Project Boundary:** Stay in CWD.
- **Completeness:** Always choose the FULL implementation over shortcuts ("Boil the Ocean").

---

## 🏭 REVIEW SPECIALISTS

**Before shipping code**, load relevant checklists from `.agent/review-specialists/`:

| Specialist | When |
|:--|:--|
| `security.md` | Auth, input handling, backend >100 lines |
| `performance.md` | DB queries, API, frontend rendering |
| `api-contract.md` | API endpoints, request/response schemas |
| `data-migration.md` | Schema changes, migration files |
| `testing.md` | Any logic change |
| `maintainability.md` | PRs >200 lines or new modules |
| `red-team.md` | User-facing features, payment, data access |

---

## 📋 ON-DEMAND RULES (read when needed)

| Rule File | When to Read |
|:--|:--|
| `.agent/rules/agent-routing.md` | Before choosing an agent |
| `.agent/rules/code-workflow.md` | Before writing code (Socratic Gate, scripts) |
| `.agent/rules/security-baseline.md` | Before handling auth, secrets |
| `.agent/skills_registry.json` | For skill/agent discovery |
| `.agent/review-specialists/*.md` | Before code review (load by scope) |
| `.agent/decisions/decisions.jsonl` | Before re-deciding something |
| `.agent/workflows/sprint.md` | For connected pipeline: Think → Plan → Build → Review → Test → Ship → Reflect |
| `.agent/adapters/` | When setting up ag-kit for non-Antigravity IDEs |
