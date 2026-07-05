# Agent Routing & Classification Rules

> Loaded on demand when AI needs routing guidance. NOT loaded at every session start.

## 📥 REQUEST CLASSIFIER

**Before ANY action, classify the request:**

| Request Type     | Trigger Keywords                           | Active Tiers                   | Result                      |
| ---------------- | ------------------------------------------ | ------------------------------ | --------------------------- |
| **QUESTION**     | "what is", "how does", "explain"           | TIER 0 only                    | Text Response               |
| **SURVEY/INTEL** | "analyze", "list files", "overview"        | TIER 0 + Explorer              | Session Intel (No File)     |
| **SIMPLE CODE**  | "fix", "add", "change" (single file)       | TIER 0 + TIER 1 (lite)         | Inline Edit                 |
| **COMPLEX CODE** | "build", "create", "implement", "refactor" | TIER 0 + TIER 1 (full) + Agent | **{task-slug}.md Required** |
| **DESIGN/UI**    | "design", "UI", "page", "dashboard"        | TIER 0 + TIER 1 + Agent        | **{task-slug}.md Required** |
| **SLASH CMD**    | /create, /orchestrate, /debug              | Command-specific flow          | Variable                    |

## 🤖 INTELLIGENT AGENT ROUTING

**ALWAYS ACTIVE: Before responding to ANY request, automatically analyze and select the best agent(s).**

> 🔴 **MANDATORY:** Use `skills_registry.json` agents section for selection.

### Auto-Selection Protocol

1. **Analyze (Silent)**: Detect domains from user request.
2. **Select Agent(s)**: Match against `agents` array in `skills_registry.json`.
3. **Inform User**: `🤖 Applying knowledge of @[agent-name]...`
4. **Apply**: Generate response using the selected agent's persona and rules.

### Project Type Routing

| Project Type                           | Primary Agent         | Skills                        |
| -------------------------------------- | --------------------- | ----------------------------- |
| **MOBILE** (iOS, Android, RN, Flutter) | `mobile-developer`    | mobile-design                 |
| **WEB** (Next.js, React web)           | `frontend-specialist` | frontend-design               |
| **BACKEND** (API, server, DB)          | `backend-specialist`  | api-patterns, database-design |

> 🔴 **Mobile + frontend-specialist = WRONG.** Mobile = mobile-developer ONLY.

### Agent Routing Checklist

Before ANY code or design work:

| Step | Check | If Unchecked |
|------|-------|--------------|
| 1 | Identified correct agent? | → STOP. Analyze request domain. |
| 2 | Read agent's `.md` file? | → STOP. Open `.agent/agents/{agent}.md` |
| 3 | Announced agent? | → Add `🤖 Applying knowledge of @[agent]...` |
| 4 | Loaded required skills? | → Check `skills:` field and read them. |
| 5 | Ran VFS scan? | → Run `vfs_parser.py` or `view_file` first. |

### 🎭 Mode Mapping

| Mode     | Agent             | Behavior                                     |
| -------- | ----------------- | -------------------------------------------- |
| **plan** | `project-planner` | 4-phase methodology. NO CODE before Phase 4. |
| **ask**  | -                 | Focus on understanding. Ask questions.       |
| **edit** | `orchestrator`    | Execute. Check `{task-slug}.md` first.       |

## TIER 2: DESIGN RULES

> **Design rules are in the specialist agents, NOT here.**

| Task         | Read                            |
| ------------ | ------------------------------- |
| Web UI/UX    | `.agent/frontend-specialist.md` |
| Mobile UI/UX | `.agent/mobile-developer.md`    |
