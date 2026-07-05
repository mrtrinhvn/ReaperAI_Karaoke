# 🌌 AG-KIT ECOSYSTEM — Định Danh & Bản Đồ Hệ Sinh Thái

> **Đọc bắt buộc khi khởi động bất kỳ project nào thuộc hệ sinh thái ag-kit.**

---

## 1. AG-KIT LÀ GÌ?

**ag-kit** là framework tư nhân — bộ tiêu chuẩn vận hành AI Agents — được thiết kế bởi **một Owner duy nhất**.

```
ag-kit = CLI (Node.js) + Skills + Memory + Brain + Rules
         → Cấy vào mọi project để AI Agent làm việc chuyên nghiệp
```

**Runtime:** Node.js bắt buộc. Python tùy chọn (cho tính năng nâng cao).

---

## 2. CẤU TRÚC HỆ SINH THÁI

```
/home/tao/Projects/
├── ag-kit/                    ← 🌱 TEMPLATE GỐC + CLI
│   ├── bin/cli.js             ← CLI duy nhất (100% Node.js cho core)
│   └── template/.agent/       ← Bản mẫu copy vào projects
│
├── MoneyHunter/               ← Project A (57 skills: core+python+web+bot)
├── Tongdailyve/               ← Project B (51 skills: core+web+python)
├── <project-N>/               ← Mỗi project có .agent/ riêng
│
└── ~/.config/ag-kit/
    └── projects.json          ← Registry toàn bộ projects
```

---

## 3. BỘ NHỚ 3 TẦNG (Universal Memory Stack)

```
TẦNG 3 — KNOWLEDGE BASE (.agent/knowledge/*.md)
  Sự thật vĩnh cửu — Git-tracked — AI đọc tự động
  Nội dung: kiến trúc, quy tắc, patterns đã phê duyệt

TẦNG 2 — WORKING MEMORY GRAPH (.agent/memory/graph.db)
  Hot nodes → Cold nodes (tổng hợp định kỳ)
  AI truy cập qua MCP tools. .gitignore — Local only.

TẦNG 1 — CODEBASE INDEX (symbols + routes trong graph.db)
  AST-parsed signatures. Auto-rebuild khi code đổi.
  .gitignore — Local only.

AUTO-BRAIN (.agent/brain/summary.md)
  Tổng hợp từ 3 tầng — Auto-rebuild khi init/update/commit.
```

---

## 4. PACK SYSTEM — Cài đúng thứ cần

Không phải project nào cũng cần tất cả skills. Pack system đảm bảo gọn nhẹ:

```bash
ag-kit init                    # core (31 skills) — mặc định
ag-kit init --pack web         # + 15 web skills
ag-kit init --pack python      # + 5 Python skills
ag-kit init --pack bot         # + 6 bot/automation skills
ag-kit install-pack web        # Thêm pack vào project đã có
```

Pack history lưu trong `.agent/.installed_packs` → `ag-kit update` tự giữ nguyên.

---

## 5. CLI — Phân tầng Python Optional

| Tầng | Commands | Runtime |
|---|---|---|
| **Core** | init, update, status, packs, doctor | ✅ Node.js only |
| **Brain Lite** | Registry + Brain (trong init/update) | ✅ Node.js only |
| **Brain Full** | brain, search, context, impact | 🐍 Cần Python |
| **Memory** | memory, session-save, dashboard | 🐍 Cần Python |

→ User chỉ cần Node.js để bắt đầu. Python thêm sức mạnh nếu có.

---

## 6. MCP MEMORY SERVER

Mỗi project đăng ký `ag-kit-memory` MCP server:

**8 tools AI gọi native:**
`memory_save`, `memory_search`, `memory_link`, `memory_graph`,
`memory_hot`, `memory_cold`, `memory_consolidate`, `memory_status`

---

## 7. LUẬT BẤT BIẾN

1. **Không ghi dữ liệu nghiệp vụ project vào ag-kit template.**
2. **Mỗi project có graph.db riêng — không chia sẻ DB.**
3. **Pattern học được → tổng quát hóa trước khi đưa vào template.**
4. **Memory/brain data KHÔNG push Git.**
5. **init/update KHÔNG gọi Python** (JS-native fallback bắt buộc).
6. **SKILL.md ≤ 200 dòng** (chi tiết để sub-files).
7. **Khi sửa ag-kit → đọc `.agent/knowledge/CONTRIBUTING.md` trước.**

---

## 8. CROSS-PROJECT (Xem não dự án khác)

```
1. Đọc registry:  ~/.config/ag-kit/projects.json → tìm brain_path
2. Đọc brain:     <B>/.agent/brain/summary.md    → hiểu trong 500 tokens
3. Nếu cần sâu:   memory_search tại DB của project đó
4. KHÔNG:          Scan toàn bộ folder khi chưa đọc summary.md
```

---

_Cập nhật: 2026-06-26 v2.2.9_
