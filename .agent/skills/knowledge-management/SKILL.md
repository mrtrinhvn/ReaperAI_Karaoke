---
name: knowledge-management
description: Systems thinking and knowledge retention protocol. MANDATORY for maintaining architectural consistency, recording integration knowledge (API characteristics), and ensuring complete, holistic code updates.
allowed-tools: Read, Write, Glob, Grep
---



## When to Activate

- Systems thinking and knowledge retention protocol. MANDATORY for maintaining architectural consistency, recording integr
- Need guidance on: 1. 🧠 THE KNOWLEDGE BACKBONE (`.agent/knowledge/`)
- Need guidance on: 2. 🕸️ SYSTEMS THINKING (HOLISTIC UPDATES)
- Need guidance on: 3. 🗺️ HIERARCHICAL CONTEXT ROUTING (Local Memory)
- Need guidance on: 4. 🔭 EXTERNAL LEARNING PROTOCOL

# Knowledge Management & Systems Thinking

> **MANDATORY:** Use this protocol to ensure the AI acts as a long-term technical partner with memory, rather than a stateless coder.

---

## 1. 🧠 THE KNOWLEDGE BACKBONE (`.agent/knowledge/`)

**PRINCIPLE:** Never rely on assumptions or ephemeral conversation memory for project characteristics. Store them permanently.

### Mandatory Read Before Action (Text vs Vector Search)
Before interacting with any third-party API, database schema, or core system component, you **MUST** actively seek out existing documentation using the CORRECT tool for the data type:
- If retrieving explicit Markdown documentation (e.g., API schemas, strict rules), use `grep_search` or open the file directly in `.agent/knowledge/`.
- If retrieving historical experience, bug fixes, or unstructured project configurations, you **MUST** use the MCP tool `mcp_ag-kit-memory_memory_search` (Semantic Cosine Vector Search) to scan the memory graphs.
*Example: Use grep/file reader for reading schema in `stripe_api.md`, but strictly use `memory_search` for "how did we handle the stripe CORS error last time?".*

### Mandatory Proactive Updates (Zero Prompting Rule)
When you successfully:
- Connect to an API and figure out its exact endpoints/payloads.
- Discover a system limitation or quirky behavior.
- Understand how a specific module works after debugging.
- **Refactor, rewire, or change the core architecture/logic of the system.**

You **MUST** proactively document or update this into a structured markdown file in `.agent/knowledge/` **IMMEDIATELY IN THE SAME TASK**. 
*Do NOT wait for the user to remind you. Waiting for the user to say "update the knowledge base" is considered a FAILURE of this protocol. You must ensure the AI brain is synced before you declare the task complete.*
*Do not just solve the problem for the current session. Build the skeleton for the next session.*

---

## 2. 🕸️ SYSTEMS THINKING (HOLISTIC UPDATES)

**PRINCIPLE:** A codebase is an interconnected web. Changing one node without checking its dependencies is unacceptable.

### The "No Orphaned Code" Rule
When you are asked to:
- Rename a feature (e.g., "Audit" -> "Validation").
- Remove a feature.
- Change the structure of an API response.

You **MUST NOT** just edit the immediate file and stop. You must:
1. Use `grep_search` to find every instance of the old name/concept across the entire codebase (`Frontend`, `Backend`, `Titles`, `UI Text`).
2. Update **ALL** related instances. 
*Example Anti-Pattern: Removing the backend logic for an 'Audit Report' but leaving a blank UI Panel with the title "Audit Report" on the frontend.*

### Context Boundaries & The Ripple Effect
When modifying a feature or fixing a bug, ask yourself:
1. Who calls this function?
2. What UI component relies on this data?
3. **Does this change make the current Knowledge Base outdated?** 
   - If YES, you **MUST** pause and update the relevant `.md` files in `.agent/knowledge/` right then and there. A working codebase with an outdated AI brain is a broken project.

---

## 3. 🗺️ HIERARCHICAL CONTEXT ROUTING (Local Memory)

**PRINCIPLE:** Context should be scoped locally to reduce token bloat and prevent the AI from hallucinating across unrelated domains. Do not stuff all documentation into a monolithic global file.

### Sub-Directory Contexts
When working within a specific module (e.g., `packages/core/services/` or `apps/web/components/`), you should:
1. **Check for Local Context:** Look for a `CONTEXT.md` or `README.md` file *within that specific directory* before starting work.
2. **Context Routing:** Leave pointers in central documentation (like `.agent/knowledge/architecture.md`) that route the AI to these deep local files. (e.g., `-> For payment processing logic, see packages/core/billing/CONTEXT.md`).
3. **Local Updates:** When making fundamental changes to a localized component, create or update its local `CONTEXT.md` instead of polluting the global knowledge base. Keep local context files under 100 lines.

---

## 4. 🔭 EXTERNAL LEARNING PROTOCOL

**PRINCIPLE:** Học từ bên ngoài (GitHub repo, blog, framework khác) là tốt. Nhưng copy nguyên si là sai. Chỉ trích xuất ý tưởng cốt lõi và adapt vào thế mạnh hiện có.

### Quy trình học hỏi có chọn lọc

Khi Sếp yêu cầu "học từ X" hoặc "xem Y có gì hay":

1. **Đọc -> Distill**: Xác định 3-5 ý tưởng giá trị nhất. Bỏ qua những gì đã có hoặc không phù hợp.

2. **Đánh giá khả năng áp dụng**:
   - YES: Hoạt động với infra/stack hiện tại, không cần refactor lớn
   - ADAPT: Tốt nhưng cần điều chỉnh cho phù hợp đặc thù project
   - NO: Đòi hỏi tool/infra không có, hoặc chống pattern hiện tại

3. **Ghi condensed principle**: Mỗi ý tưởng học được -> tối đa **10 dòng** trong file `.md` phù hợp. Không copy nguyên lý thuyết, chỉ ghi *cách áp dụng cụ thể vào dự án này*.

4. **Anti-pattern cần tránh**:
   - WRONG: Copy nguyên boilerplate vào SKILL.md (bloat, tốn token)
   - WRONG: Nhồi nhét mọi ý tưởng vào một file duy nhất
   - RIGHT: Một ý tưởng -> một section nhỏ trong đúng SKILL.md liên quan
   - RIGHT: Bootstrap theo mạch — mỗi file chỉ load khi thực sự cần

### Skill Loading Contract (v2 — BẮT BUỘC)

**Kích thước SKILL.md (hard limits):**
- Boot-critical (P0): ≤ 150 dòng
- Domain skills (P1-P2): ≤ 100 dòng. Không ngoại lệ
- Nếu cần > 100 dòng → PHẢI tách sub-files (L2)

**3 câu hỏi trước khi thêm nội dung vào SKILL.md:**
1. **AI model đã biết chưa?** (JWT, SQL injection, CSS grid, React hooks...) → KHÔNG nhồi. Chỉ ghi rules đặc thù
2. **Áp dụng MỌI LẦN hay đôi khi?** → Mọi lần → SKILL.md. Đôi khi → sub-file
3. **Đây là RULE hay TUTORIAL?** → Rule = "CẤM dùng Date.now() trực tiếp". Tutorial = "Đây là cách viết JWT..." → Tutorial KHÔNG thuộc SKILL.md

**Content taxonomy:**
- SKILL.md: When to Activate + Routing + Hard Rules (≤15) + Pointers
- Sub-files: Detailed checklists, protocols, advanced patterns
- Memory MCP: Lookup tables, historical decisions, framework mappings
- ❌ NEVER in SKILL.md: Code tutorials, code examples, boilerplate templates
