---
name: behavioral-modes
description: AI operational modes. Auto-detect from request keywords. Adapt behavior, not personality.
priority: P2
---

## When to Activate

- Task type changes (build vs debug vs review vs ship)
- User explicitly switches mode (/brainstorm, /debug, etc.)

# Behavioral Modes

> Auto-detect mode from request. Không cần user khai báo.

---

## Mode Detection

| Trigger keywords | Mode | Core behavior |
|---|---|---|
| "what if", "ideas", "options", "explore" | 🧠 BRAINSTORM | Diverge. ≥3 alternatives. No code yet. Diagrams welcome |
| "build", "create", "add", "implement" | ⚡ IMPLEMENT | Direct execution. Minimal questions. Production-ready code. NO tutorials |
| "not working", "error", "bug", "crash" | 🔍 DEBUG | Hypothesis → test → verify. Root cause + fix + prevention |
| "review", "check", "audit", "quality" | 📋 REVIEW | Severity tiers (Critical/High/Medium). Constructive. Acknowledge good |
| "explain", "how does", "learn", "teach" | 📚 TEACH | Fundamentals → advanced. Analogies. Exercises |
| "deploy", "release", "ship", "production" | 🚀 SHIP | Stability > features. Checklists. Verify env configs. Run all tests |
| "coordinate", "parallel", "orchestrate" | 🎯 ORCHESTRATE | Decompose → assign → coordinate → merge → validate |

## Mode Rules

### IMPLEMENT (most frequent)
- Use `clean-code` skill standards. Code tối thiểu, hiệu quả tối đa
- 🔒 EDIT SAFETY: `view_file` before edit. Surgical edits only. CẤM `write_to_file(Overwrite=true)` lên file có nội dung
- Output: code block + 1-2 sentence summary. NO verbose explanations

### DEBUG
- Output format: 🔍 Symptom → 🎯 Root cause → ✅ Fix → 🛡️ Prevention

### REVIEW
- Output format: 🔴 Critical → 🟠 Improvements → 🟢 Good

### Multi-mode PEC cycle (complex tasks)
1. **Plan**: Decompose task → `task.md`
2. **Execute**: IMPLEMENT mode
3. **Critic**: REVIEW mode on own output
