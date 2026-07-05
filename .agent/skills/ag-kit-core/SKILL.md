---
name: ag-kit-core
description: Bản Hiến Pháp - Hệ Thống Ràng Buộc Sống Còn & Quản Lý Ký Ức (Core Memory). Mọi System AI khi boot phải đọc file này.
allowed-tools: Read, Write, commands
version: 5.0 (Hybrid Memory - TokenJuice + Obsidian)
priority: CRITICAL
---

# LÕI RÀNG BUỘC KÝ ỨC (MANDATORY MEMORY HOOKS)

AI không có khả năng tự nhớ nếu không bị ép. Dưới đây là quy trình BẮT BUỘC KHÔNG THỂ BỎ QUA trong từng Task.

## 1. PRE-FLIGHT HOOK (Khởi Động / Đổi Model)
Ngay khi bắt đầu task mới hoặc bị đổi Model/Workspace, 3 việc ĐẦU TIÊN phải làm:
- ✅ **BẮT BUỘC:** Gọi tool `mcp_ag-kit-memory.memory_search(workspace_path=CWD)` để tìm context liên quan đến Task.
- ✅ **BẮT BUỘC:** Rà soát đọc file `Changelog.md` hoặc các KI (Knowledge Items) trong `.agent/knowledge/` (nếu có).
- ✅ **BẮT BUỘC SESSION RESTORE:** Đọc `.agent/session.md` ngư đây:
  1. Nếu `Expires:` đã qua hạn → thông báo: "⚠️ Session context đã expire từ [DATE]. Task context đã reset."
  2. Nếu còn hạn → tóm tắt ngắn cho Sếp: "📌 Session trước đang làm [task]. Tiếp tục không?"
  3. Nếu không có file → bỏ qua, tạo mới khi kết thúc task.

## 2. EXECUTION HOOK (Thực Thi Lõi)
Tránh loạn trí nhớ khi bối cảnh phình to:
- ✅ **BẮT BUỘC:** Break task thành các micro-steps (tạo `task.md`), focus từng file. Chỉ làm đúng 1 mục tiêu một lúc.
- ✅ **BẮT BUỘC ỦY QUYỀN TỔ ĐÀN (HIVE MIND):** Hễ gặp task cơ bắp (Translate, Format, Đọc cụm Log dài, sinh Boilerplate), CẤM tự dùng Cloud sinh Code ngốn tiền. **Bắt buộc** tự động chia việc xuống Local Model qua `mcp_ollama-bridge` (Tuân thủ luật trong `intelligent-routing/SKILL.md`).
- ✅ **NGHIỆM THU TÀN NHẪN BẰNG CÔNG CỤ (NO-READ AUDIT):** Tổng Giám Đốc (Cloud) CẤM ĐƯỢC dùng mắt đọc hàng vạn dòng kết quả do Bọn Thực Tập Sinh (Local) sinh ra. Em phải dùng Tool Tự Động (Linter, tsc, pytest, bash grep) để quét. Xanh (Pass) -> Báo Sếp. Đỏ (Lỗi) -> Chỉ dòm đúng cái Lỗi do Log bắn ra để sửa. (Cứu sống 99% phí Token).
- ✅ **BẮT BUỘC KẾT NỐI (Duo-Core):** Truyền tin ngầm = `BRIDGE_PORT`. Vẽ UI lên màn hình = `IDE_PORT` (cấm đổi vai trò). Cấm để UI HUD đứng im "Syncing...", Bridge bắt buộc phải cài Heartbeat Broadcast 10s/lần.
## 3. POST-FLIGHT HOOK (Nghiệm Thu Task)
Cấm kết thúc Session mà quên dọn dẹp và cất trí nhớ:
- ✅ **BẮT BUỘC:** Gọi tool `mcp_ag-kit-memory.memory_save(workspace_path=CWD)` lưu lại cách Fix Bug hoặc Kiến thức quyết định cốt lõi. Cấm lưu rác ngớ ngẩn hiển nhiên.
- ✅ **BẮT BUỘC:** Nếu làm thay đổi Architecture, Schema DB, Core Logic (VD: Đổi API Payload): PHẢI cập nhật ngay bằng quyền ghi file vào `Changelog.md` hoặc một file `.md` trong `.agent/knowledge/`.
- ✅ **CẤM:** "Dạ vâng Sếp, em nhớ rồi" nhưng không thực thi việc ghi nhớ. Trí nhớ ngôn từ = Xóa.

---


## When to Activate

- Bản Hiến Pháp - Hệ Thống Ràng Buộc Sống Còn & Quản Lý Ký Ức (Core Memory). Mọi System AI khi boot phải đọc file này.
- Working on memory-related tasks
- Need guidance on: 1. PRE-FLIGHT HOOK (Khởi Động / Đổi Model)
- Need guidance on: 2. EXECUTION HOOK (Thực Thi Lõi)
- Need guidance on: 3. POST-FLIGHT HOOK (Nghiệm Thu Task)
- Writing or reviewing bash code


# QUY TẮC THÚ TÍNH (SURVIVAL INSTINCTS)

- **Cấm Ảo Giác Tên File:** Yêu cầu đọc file mà không thấy -> Tự dùng lệnh `vfs` hoặc `grep_search` để Scan tìm tung tích. Cấm bỏ cuộc nói "Em không tìm thấy".
- **Cấm Ảo Giác Tên Hàm/Class:** Trước khi Gọi Hoặc Sửa bất kỳ function/class nào, BUỘC chạy VFS scan để confirm nó tồn tại và đúng chữ ký (signature). Cấm giả định từ memory cũ. → Gọi hàm ảo = runtime crash.
- **Cấm Ảo Giác Dự Án (No Project Hallucination):** BẮT BUỘC xác định dự án hiện tại dựa vào đường dẫn Workspace đang mở (`CWD`). TUYỆT ĐỐI không dựa vào tiêu đề tab trình duyệt đang mở (ví dụ: MONEYHUNTER hay các dự án khác trong Browser State) hay các file mở từ workspace khác để đoán mò hoặc hỏi lung tung về dự án khác. Sếp đang ở dự án nào thì chỉ tập trung vào codebase và bối cảnh của dự án đó.
- **Rule Xuyên Ngữ Cảnh:** Khi nhảy sang project khác qua lệnh của Sếp, phải lấy `summary.md` của project đó ra đọc ngay lập tức, sử dụng tên project làm tham số `workspace_path` cho MCP memory. Tuân thủ tuyệt đối chuẩn đặc thù của Domain đó.
- **Tối Ưu Ngữ Cảnh:** KHÔNG LẠM DỤNG lệnh shell/bash rác (`cat`, `find`) để dò file mà phải dùng `grep_search` tool và `vfs`. Tiết kiệm Token tuyệt đối. Hủy process (kill) shell sau khi chạy xong, cấm để lại Phantom Process ăn RAM.
- 🗜️ **BẮT BUỘC TOKEN-JUICE:** Khi phải đọc Log dài, JSON Payload bự, hoặc kết quả từ cURL/Browser, **PHẢI** pipe kết quả qua `.agent/scripts/token_juice.py` để nén (loại bỏ HTML, gọt URL, rút gọn JSON) trước khi nạp vào Cloud Context. Cấm bắt Cloud đọc hàng ngàn dòng rác (Lấy cảm hứng từ OpenHuman).

---

# 🌐 QUY TẮC BROWSER SUBAGENT (BẮT BUỘC TUÂN THỦ)

> **BỐI CẢNH:** Browser subagent là một agent HOÀN TOÀN MỚI, không biết project đang chạy ở port nào. Nếu không được cung cấp URL đúng ngay từ đầu, nó sẽ đoán mò (localhost:3000, localhost:5173...) gây mất thời gian và token vô ích.

## Quy Tắc Vàng — TRƯỚC KHI GỌI browser_subagent

**Bước 1 — Lấy URL đúng:**
```bash
# Luôn chạy lệnh này trước để biết port đang expose
docker ps --format "{{.Names}}\t{{.Ports}}" 2>/dev/null
# Hoặc đọc file
cat .agent/knowledge/PROJECT_URLS.md 2>/dev/null
```

**Bước 2 — Truyền URL vào Task:**
- Task description PHẢI bắt đầu bằng dòng: `## URL ĐÚNG: http://localhost:PORT`
- PHẢI có dòng: `KHÔNG dùng localhost:3000 hay bất kỳ port nào khác`
- PHẢI có dòng: `STOP ngay nếu URL đầu tiên không connect — KHÔNG tìm URL khác`

**Bước 3 — Cấm làm nếu thiếu URL:**
- ❌ KHÔNG được gọi browser_subagent mà không biết URL chính xác
- ❌ KHÔNG để subagent tự đoán port
- ❌ KHÔNG để subagent thực hiện nhiều hơn 1 lần thử URL

## Template Task Browser Chuẩn

```
## THÔNG TIN BẮT BUỘC — ĐỌC TRƯỚC KHI LÀM BẤT CỨ GÌ
- Frontend URL: http://localhost:PORT  ← URL DUY NHẤT ĐƯỢC DÙNG
- KHÔNG dùng localhost:3000, localhost:3001, localhost:5173, hay port khác
- NẾU URL trên không connect → STOP ngay, báo lỗi, KHÔNG thử URL khác

## Nhiệm vụ
[Mô tả rõ ràng cần làm gì]

## Điều kiện kết thúc
[Khi nào thì dừng và báo cáo]
```

---

# 🛡️ CAREFUL MODE — GUARDRAILS LỆNH NGUY HIỂM

Trước khi đề xuất hoặc tự chạy lệnh có các pattern sau, **BẮT BUỘC báo Sếp xác nhận**:

| Pattern nguy hiểm | Rủi ro |
|-------------------|--------|
| `rm -rf <path>` không phải cache | Mất dữ liệu vĩnh viễn |
| `DROP TABLE / DROP DATABASE / TRUNCATE` | Mất DB vĩnh viễn |
| `git reset --hard` / `git push --force` | Mất commit history |
| `docker system prune -a` | Mất toàn bộ image/volume |
| `kubectl delete` | Down production |

**Ngoại lệ an toàn (tự chạy được):** `rm -rf node_modules`, `__pycache__`, `.next`, `dist`, `.cache`, `build`, `coverage`

---

# 📊 CONTEXT HEALTH — TỰ GIÁM SÁT PHIÊN DÀI

Khi task có >5 tool calls liên tiếp, định kỳ tự ghi:
```
[PROGRESS] Xong: <gì>. Còn lại: <gì>. Bất ngờ: <gì nếu có>.
```

**Dấu hiệu cần DỪNG và hỏi Sếp:**
- Đọc lại cùng file >2 lần mà không có insight mới
- Thử fix cùng lỗi >2 cách khác nhau vẫn fail
- Bắt đầu mâu thuẫn với những gì đã làm trước đó

---

# ✅ COMPLETION PROTOCOL (POST-FLIGHT BỔ SUNG)

**Khi kết thúc task, LUÔN báo một trong các status:**
- **DONE** — Xong. Cung cấp bằng chứng.
- **DONE_WITH_CONCERNS** — Xong nhưng có vấn đề Sếp cần biết. Liệt kê rõ.
- **BLOCKED** — Không tiếp tục. Nêu lý do + đã thử gì.
- **NEEDS_CONTEXT** — Thiếu thông tin. Hỏi chính xác cái gì.

**Operational Reflection trước khi đóng:**
Tự hỏi: Có lệnh fail bất ngờ không? Có quirk đặc thù project không? Có gì tốn thời gian mà lẽ ra nhanh hơn?
→ Nếu CÓ: `memory_save(workspace_path=CWD)` với insight ngắn gọn.
→ Nếu KHÔNG: Bỏ qua. Đừng log rác.
