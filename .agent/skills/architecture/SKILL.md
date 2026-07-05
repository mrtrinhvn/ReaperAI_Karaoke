---
name: architecture
description: Architectural decision-making framework. Requirements analysis, trade-off evaluation, ADR documentation. Use when making architecture decisions or analyzing system design.
allowed-tools: Read, Glob, Grep
---



## When to Activate

- Architectural decision-making framework. Requirements analysis, trade-off evaluation, ADR documentation. Use when making
- Working on architecture-related tasks
- Need guidance on: 🔴 CRITICAL RULE: CROSS-DOMAIN CONTAMINATION (CHỐNG Ô NHIỄM CHÉO)
- Need guidance on: 🎯 Selective Reading Rule
- Need guidance on: 🔗 Related Skills

# Architecture Decision Framework

> "Requirements drive architecture. Trade-offs inform decisions. ADRs capture rationale."

## 🔴 CRITICAL RULE: CROSS-DOMAIN CONTAMINATION (CHỐNG Ô NHIỄM CHÉO)
Khi được yêu cầu Audit (Kiểm toán), Review hoặc Tương tác với Mảng Lõi Hệ Thống (Ví dụ: ag-kit, Template gốc, Framework base):

- **KÍCH HOẠT CHẾ ĐỘ VÔ NGÃ (Agnostic Mode):** Lập tức đình chỉ mọi tư duy liên quan đến Chứng khoán, Quant, Trading. Trở về làm một Pure Tech Agent.
- **SĂN LÙNG SỰ Ô NHIỄM:** Bất kỳ file, từ khóa, biến môi trường hay Agent nào có yếu tố cụ thể của Nghiệp Vụ (Business Logic/Finance/Quant) mà đi lạc vào khu vực Lõi Framework (Core/Template) -> Tuyệt đối không được coi là "Người Nhà". Chấm dứt dung túng, phải lập tức Cảnh Báo và yêu cầu Gỡ Bỏ để bảo vệ tính Đa Dụng (Zero-Bias) của nền tảng Lõi.

## 🎯 Selective Reading Rule

**Read ONLY files relevant to the request!** Check the content map, find what you need.

| File | Description | When to Read |
|------|-------------|--------------|
| `context-discovery.md` | Questions to ask, project classification | Starting architecture design |
| `trade-off-analysis.md` | ADR templates, trade-off framework | Documenting decisions |
| `pattern-selection.md` | Decision trees, anti-patterns | Choosing patterns |
| `examples.md` | MVP, SaaS, Enterprise examples | Reference implementations |
| `patterns-reference.md` | Quick lookup for patterns | Pattern comparison |

---

## 🔗 Related Skills

| Skill | Use For |
|-------|---------|
| `@[skills/database-design]` | Database schema design |
| `@[skills/api-patterns]` | API design patterns |
| `@[skills/deployment-procedures]` | Deployment architecture |

---

## Core Principle

**"Simplicity is the ultimate sophistication."**

- Start simple
- Add complexity ONLY when proven necessary
- You can always add patterns later
- Removing complexity is MUCH harder than adding it

---

## Validation Checklist

Before finalizing architecture:

- [ ] Requirements clearly understood
- [ ] Constraints identified
- [ ] Each decision has trade-off analysis
- [ ] Simpler alternatives considered
- [ ] ADRs written for significant decisions
- [ ] Team expertise matches chosen patterns
