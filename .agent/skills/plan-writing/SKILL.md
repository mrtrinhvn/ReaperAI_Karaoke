---
name: plan-writing
description: Structured task planning with clear breakdowns, dependencies, and verification criteria. Use when implementing features, refactoring, or any multi-step work.
allowed-tools: Read, Glob, Grep
---

# Plan Writing

> Source: obra/superpowers

## Overview
This skill provides a framework for breaking down work into clear, actionable tasks with verification criteria.

## Task Breakdown Principles

### 1. Kỷ Luật Micro-Tasking (Hành động 5 phút)
 - Each task should take 2-5 minutes MAXIMUM.
 - Tên Task KHÔNG PHẢI LÀ "Làm tính năng X". Tên Task phải là **hành động cụ thể trên 1 file cụ thể**.
 - VD Sai: `[ ] Thêm logic phân quyền`
 - VD Đúng: `[ ] Taọ file auth.middleware.ts, đọc token từ header và trả về role.`
 
 ### 2. Clear Verification & TDD (Nếu có thể)
 - How do you know it's done?
 - What exact command to run? (e.g. `npm run test auth.test.ts`)
 - What's the expected output?

### 3. Logical Ordering
- Dependencies identified
- Parallel work where possible
- Critical path highlighted
- **Phase X: Verification is always LAST**

### 4. Dynamic Naming in Project Root
- Plan files are saved as `{task-slug}.md` in the PROJECT ROOT
- Name derived from task (e.g., "add auth" → `auth-feature.md`)
- **NEVER** inside `.claude/`, `docs/`, or temp folders

## Planning Principles (NOT Templates!)

> 🔴 **NO fixed templates. Each plan is UNIQUE to the task.**

### Principle 1: Keep It SHORT

| ❌ Wrong | ✅ Right |
|----------|----------|
| 50 tasks with sub-sub-tasks | 5-10 clear tasks max |
| Every micro-step listed | Only actionable items |
| Verbose descriptions | One-line per task |

> **Rule:** If plan is longer than 1 page, it's too long. Simplify.

---

### Principle 2: Be STRICTLY SPECIFIC (File-Level)
 
 | ❌ Wrong (Cấm Tuyệt Đối) | ✅ Right (Chuẩn Superpowers) |
 |----------|----------|
 | "Set up project" | "Run `npx create-next-app`" |
 | "Add authentication" | "Tạo `api/auth.ts`, code hàm verify JWT và trả 401" |
 | "Style the UI" | "Mở `Header.tsx`, đổi bg-white thành bg-slate-900" |
 
 > **Rule:** Mỗi task là một phát súng bắn tỉa chính xác vào 1 file. Không viết task bắn tỉa mù.

---

### Principle 3: Dynamic Content Based on Project Type

**For NEW PROJECT:**
- What tech stack? (decide first)
- What's the MVP? (minimal features)
- What's the file structure?

**For FEATURE ADDITION:**
- Which files are affected?
- What dependencies needed?
- How to verify it works?

**For BUG FIX:**
- What's the root cause?
- What file/line to change?
- How to test the fix?

---

### Principle 4: Scripts Are Project-Specific

> 🔴 **DO NOT copy-paste script commands. Choose based on project type.**

| Project Type | Relevant Scripts |
|--------------|------------------|
| Frontend/React | `ux_audit.py`, `accessibility_checker.py` |
| Backend/API | `api_validator.py`, `security_scan.py` |
| Mobile | `mobile_audit.py` |
| Database | `schema_validator.py` |
| Full-stack | Mix of above based on what you touched |

**Wrong:** Adding all scripts to every plan
**Right:** Only scripts relevant to THIS task

---

### Principle 5: Verification is Simple

| ❌ Wrong | ✅ Right |
|----------|----------|
| "Verify the component works correctly" | "Run `npm run dev`, click button, see toast" |
| "Test the API" | "curl localhost:3000/api/users returns 200" |
| "Check styles" | "Open browser, verify dark mode toggle works" |

---

## Plan Structure (Flexible, Not Fixed!)

```markdown
 # [Tên tính năng ngắn gọn]
 
 > **MANDATORY STEP BEFORE PLAN:** Đã đọc `.agent/knowledge/architecture_decisions.md` (ADR) để không lập kế hoạch sai luồng công nghệ chưa?
 
 ## Tasks 
 - [ ] `path/to/file1.py`: [Chính xác hàm gì cần thêm/sửa, tốn bao nhiêu phút?]
   -> Verify: Chạy `pytest file1`, output X.
 - [ ] `path/to/file2.ts`: [Chỉnh sửa dòng nào thành dòng nào?]
   -> Verify: Bật browser check console log.
 
 ## Done When
 - [ ] [Main success criteria]
```

> **That's it.** No phases, no sub-sections unless truly needed.
> Keep it minimal. Add complexity only when required.

## Notes
[Any important considerations]
```

---

## Best Practices (Quick Reference)

1. **Start with goal** - What are we building/fixing?
2. **Max 10 tasks** - If more, break into multiple plans
3. **Each task verifiable** - Clear "done" criteria
4. **Project-specific** - No copy-paste templates
5. **Update as you go** - Mark `[x]` when complete

---

## When to Use

- New project from scratch
- Adding a feature
- Fixing a bug (if complex)
- Refactoring multiple files
