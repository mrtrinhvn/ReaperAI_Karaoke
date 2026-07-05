---
name: "Cognitive Session Manager"
description: "Quản lý Session Context cho cả App Code (file-based isolation) và AI Agent (checkpoint giữa các hội thoại). Đọc skill này khi cần lưu/khôi phục context làm việc."
---

# THE COGNITIVE SESSION MANAGER

Hai loại session cần quản lý trong project này:

## TẦNG 1: App Sessions (cho code của phần mềm)

Các LLM-Agent trong app KHÔNG được dùng chung `ChatHistory` tĩnh trên RAM.
Tuân thủ **Fission Memory Architecture**:

1. **File-Based Isolation** — Mỗi luồng chat/sự cố gán ID duy nhất:
   - Customer thread: `topic-<threadId>` → `.data/sessions/topic-123.json`
   - Internal heal: `doc-heal-<target>-<timestamp>`

2. **Ephemeral Injection** — Mỗi lần gọi LLM, chỉ nạp **6-10 tin nhắn gần nhất** vào ContextWindow. Nạp quá nhiều → local model (Nvidia/Groq) bị đuối token, sinh ảo giác.

3. **Garbage Collection** — Khi nhận `/close`, `/end`, `/forget` hoặc Unit Test pass:
   - Gọi `SessionManager.destroySession(sessionId)` → `fs.unlink()` xóa file JSON.
   - Quy tắc: "Cấp ID → Ghi Disk → Giới hạn RAM → Hoàn tất → Đốt hồ sơ."

---

## TẦNG 2: Agent Session Context (cho AI giữa các hội thoại)

AI không có ký ức xuyên conversation. Giải pháp: **checkpoint file đơn giản**.

### Workflow `/save-context`

Khi Sếp nói "lưu progress", "save context", "checkpoint":
1. Tạo file `.agent/state/session-<YYYYMMDD-HHMM>.md` với nội dung:
```markdown

## When to Activate

- Quản lý Session Context cho cả App Code (file-based isolation) và AI Agent (checkpoint giữa các hội thoại). Đọc skill nà
- Working on session-related tasks
- Need guidance on: TẦNG 1: App Sessions (cho code của phần mềm)
- Need guidance on: TẦNG 2: Agent Session Context (cho AI giữa các hội thoại)
- Need guidance on: Branch/Task hiện tại


# Session Checkpoint — <timestamp>
## Branch/Task hiện tại
<gì đang làm>
## Đã hoàn thành
- <item 1>
## Còn lại
- <item 2>
## Quyết định quan trọng đã đưa ra
- <decision>
- (Also logged to `.agent/decisions/decisions.jsonl` via `decision-log.sh`)
## Failed Approaches (những gì ĐÃ THỬ nhưng KHÔNG hoạt động)
- <approach>: <tại sao fail> → <bài học>
- (Quan trọng: giúp session tiếp theo KHÔNG lặp lại sai lầm)
## Quirks/Gotchas phát hiện
- <nếu có>
```
2. Xác nhận: "Đã lưu checkpoint tại `.agent/state/session-<timestamp>.md`"

### Workflow `/restore-context`

Khi Sếp nói "restore", "tiếp tục từ đâu", "where was I":
1. `ls -t .agent/state/session-*.md | head -3` — lấy file gần nhất
2. Đọc file đó
3. Tóm tắt ngắn: "Session trước đang làm X, đã xong A/B, còn lại C."
4. Hỏi: "Tiếp tục từ đây không?"

### Quy tắc giữ state nhẹ
- Mỗi checkpoint < 50 dòng. Chỉ ghi essential decisions, không ghi chi tiết code.
- Xóa checkpoint cũ hơn 7 ngày: `find .agent/state -name "session-*.md" -mtime +7 -delete`
- Pointer đến task.md nếu đang có task dang dở.

---

## TẦNG 3: Persistent Memory (xuyên session, xuyên ngày)

Cho các quyết định và context sống lâu hơn một session. Lưu vào `.agent/memory/`.

```
.agent/memory/
├── MEMORY.md              ← Index tổng (< 200 dòng)
├── user-preferences.md   ← Style làm việc, tools ưa thích
├── tech-decisions.md      ← Quyết định kỹ thuật, API quirks
└── [topic].md             ← Thêm theo nhu cầu
```

### Trigger lưu
User nói: "nhớ", "lưu lại", "remember", "don't forget"

**Protocol:**
1. Phân loại: `[user]` | `[project]` | `[feedback]` | `[reference]`
2. Ghi vào topic file phù hợp (tạo nếu chưa có)
3. Cập nhật 1 dòng vào `MEMORY.md` index
4. Confirm: "Đã lưu: [tóm tắt]"

### Trigger đọc
Đầu session mới hoặc khi cần context:
- Đọc `MEMORY.md` index → chỉ load topic files **liên quan đến task hiện tại**
- Apply **im lặng** — không recite lại trừ khi được hỏi

### Không lưu
- Secrets, tokens, credentials
- Thông tin có thể derive từ code
- Debug context tạm thời
- Code snippet (code thay đổi, memory stale)
