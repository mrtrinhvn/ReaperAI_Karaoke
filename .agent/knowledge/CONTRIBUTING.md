# 🚨 AG-KIT CONTRIBUTING — Luật Bất Biến Khi Sửa Đổi Bộ Kit

> **BẮT BUỘC ĐỌC** trước khi sửa BẤT KỲ file nào trong repo `ag-kit`.
> Đây KHÔNG phải project thường — đây là **framework cấy vào mọi project khác**.
> Một lỗi ở đây = lỗi ở 17+ projects.

---

## 1. NGUYÊN TẮC RUNTIME — Node.js First

### 🔴 LUẬT #1: `init` và `update` KHÔNG ĐƯỢC gọi Python

AG-Kit cài qua `npx` → user **chắc chắn có Node.js**.
User **chưa chắc có Python**. Vì vậy:

```
✅ ĐÚNG: Core flow (init, update, status, packs, doctor) = 100% Node.js
✅ ĐÚNG: Hàm JS-native trong cli.js (buildSlimRegistryJS, buildBrainJS)
❌ SAI:  execSync(`python3 script.py`) trong init/update
❌ SAI:  Thêm Python script mới cho tính năng core
```

**Python chỉ được dùng cho tính năng NÂNG CAO** (brain full AST, embeddings, knowledge graph).
Mọi Python call trong core PHẢI có `try/catch` fallback về JS.

### Lý do (từ sai lầm thực tế):
- v2.2.5: `skill_registry_slim.py` gọi trong `update` → user không có Python → update fail
- v2.2.9: Port sang JS → update nhanh 40%, hoạt động trên mọi máy

---

## 2. NGUYÊN TẮC SKILL — Thông Minh Nhưng Lười

### 🔴 LUẬT #2: SKILL.md ≤ 200 dòng. Không nhồi nhét.

```
✅ ĐÚNG: SKILL.md chứa LUẬT + TRIGGER. Chi tiết để trong sub-files.
❌ SAI:  Copy nguyên bài blog/tutorial vào SKILL.md
❌ SAI:  SKILL.md > 200 dòng (bloat token mỗi session)
```

**Cấu trúc chuẩn:**
```
skills/tên-skill/
├── SKILL.md          ← ≤200 dòng: What, When, Rules
├── protocol.md       ← Chi tiết protocol (load khi cần)
├── examples.md       ← Ví dụ (load khi cần)
└── scripts/          ← Automation scripts
```

### Lý do:
- AI đọc registry (~3K tokens) → chỉ load SKILL.md khi cần (~500 tokens)
- Nếu SKILL.md 500 dòng = lãng phí 2000 tokens MỖI LẦN load
- 57 skills × 2000 tokens = 114K tokens nếu tất cả đều bloat

---

## 3. NGUYÊN TẮC HỌC HỎI — Hấp Thu, Không Copy

### 🔴 LUẬT #3: Học từ bên ngoài = Chuyển hóa thành LUẬT, không copy code

Khi tích hợp kiến thức từ nguồn bên ngoài (taste-skill, design systems, v.v.):

```
✅ ĐÚNG: Đọc source → Rút ra NGUYÊN TẮC → Viết thành LUẬT ngắn gọn
✅ ĐÚNG: "Rule: Dùng HSL thay vì HEX cho color harmony"
❌ SAI:  Copy nguyên file 500 dòng vào SKILL.md
❌ SAI:  Giữ nguyên cấu trúc/naming của source gốc
❌ SAI:  Import dependency của source vào ag-kit
```

### Quy trình tích hợp:
1. **Đọc** source → hiểu INTENT (mục đích)
2. **Chưng cất** thành ≤10 rules cốt lõi
3. **Viết** rules vào SKILL.md dưới dạng hành động cụ thể
4. **Kiểm tra** có trùng lắp với skill khác không
5. **Test** skill mới có được registry nhận diện đúng không

---

## 4. NGUYÊN TẮC REGISTRY — YAML Frontmatter Chuẩn

### 🔴 LUẬT #4: Mỗi SKILL.md PHẢI có YAML frontmatter hợp lệ

```yaml
---
name: tên-skill
description: Mô tả 1 dòng (≤80 ký tự, KHÔNG dùng | hoặc >)
priority: P0|P1|P2
---
```

**Không bao giờ dùng YAML multiline (`|`, `>`) cho description.**
JS parser ĐÃ xử lý được, nhưng tránh phức tạp không cần thiết.

### Lý do (từ sai lầm thực tế):
- v2.2.5: `frontend-design` description dùng `|` → parser cũ trả về `"|"` → registry hỏng
- v2.2.9: Parser đã fix, nhưng tránh multiline = phòng ngừa

---

## 5. NGUYÊN TẮC VERSION — Nguồn Chân Lý Duy Nhất

### 🔴 LUẬT #5: Version chỉ có MỘT nguồn: `package.json`

```
package.json → CLI đọc → ghi vào .agent/.version → registry đọc
```

```
❌ SAI: Hardcode version trong registry template
❌ SAI: Đọc version từ package.json CỦA PROJECT (không phải ag-kit)
❌ SAI: Ghi .version TRƯỚC khi build registry (order matters!)
```

**Thứ tự trong update:**
1. Copy skills/scripts/rules
2. Ghi `.version` = pkg.version ← TRƯỚC registry
3. Build registry (đọc `.version`)
4. Build brain

---

## 6. NGUYÊN TẮC CLI — Backward Compatible

### 🔴 LUẬT #6: `update` không được phá dữ liệu project

```
✅ ĐÚNG: Backup custom skills → update → restore
✅ ĐÚNG: knowledge/ dùng MERGE (không overwrite file đã có)
✅ ĐÚNG: .installed_packs giữ nguyên qua update
❌ SAI:  Xóa toàn bộ skills/ rồi copy mới (mất custom skills)
❌ SAI:  Overwrite knowledge/ (mất domain knowledge thật)
```

---

## 7. NGUYÊN TẮC TEST — Phải Chứng Minh

### 🔴 LUẬT #7: Mọi thay đổi CLI phải test E2E trước khi push

Checklist bắt buộc:
- [ ] `node -c bin/cli.js` (syntax OK)
- [ ] Fresh init trên temp dir
- [ ] Update trên project thật (MoneyHunter hoặc tương đương)
- [ ] Registry: version đúng, descriptions không trống
- [ ] Brain: tạo thành công, project name đúng, stack detected
- [ ] Doctor: ≥10/11 pass

```bash
# Quick test script
ag-kit update && ag-kit doctor
```

---

## 8. DANH SÁCH SAI LẦM ĐÃ XẢY RA (Anti-Pattern Registry)

| Sai lầm | Version | Hậu quả | Fix |
|---|---|---|---|
| YAML `\|` trong description | v2.2.5 | Registry descriptions trống | Parser JS xử lý multiline |
| `brain_builder.py` trong update | v2.2.5 | Update fail khi không có Python | Port sang `buildBrainJS()` |
| `skill_registry_slim.py` trong update | v2.2.5 | Update fail khi không có Python | Port sang `buildSlimRegistryJS()` |
| Đọc `package.json` thay vì `.version` | v2.2.8 | Registry version = project version (sai) | Đọc `.agent/.version` |
| Ghi `.version` SAU registry build | v2.2.8 | Registry có version cũ | Đổi thứ tự: ghi trước, build sau |
| `total_agents` thay vì `agents.length` | v2.2.8 | Doctor hiện 0 agents | Đọc từ `agents` array |
| Copy tutorial vào SKILL.md | v2.2.6 | Skill 500+ dòng, tốn token | Chưng cất thành ≤200 dòng rules |
| `__pycache__` trong git | v2.2.8 | Rác trong repo | Thêm `.gitignore` |

---

## 9. FILE MAP — Biết File Nào Ở Đâu

```
ag-kit/
├── bin/cli.js              ← CLI duy nhất. Chứa buildSlimRegistryJS(), buildBrainJS()
├── package.json            ← SOURCE OF TRUTH cho version
├── template/
│   └── .agent/
│       ├── .version        ← Stamp version khi init/update
│       ├── skills_registry.json ← Generated, KHÔNG sửa tay
│       ├── skills/         ← Template skills (copy vào project)
│       ├── agents/         ← Agent definitions (YAML frontmatter)
│       ├── scripts/        ← Python scripts (advanced features)
│       ├── packs/          ← Pack manifests (*.pack files)
│       ├── rules/          ← GEMINI.md + rule files
│       ├── knowledge/      ← Template knowledge (MERGE, không overwrite)
│       ├── review-specialists/ ← Code review checklists
│       └── workflows/      ← Sprint, brainstorm workflows
└── .agent/                 ← AG-Kit's OWN brain (for developing ag-kit)
    └── knowledge/
        └── CONTRIBUTING.md ← FILE NÀY
```

---

_Cập nhật: 2026-06-26 | Version: v2.2.9 | Tác giả: Hội đồng Hardening Sprint_
