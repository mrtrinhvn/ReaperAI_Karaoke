---
name: frontend-design
description: |
  Progressive Design Intelligence cho UI/UX. 3 cấp độ tự động leo thang:
  L1 (inline) → L2 (design-tokens) → L3 (Open Design delegation).
  Token-efficient: chỉ nạp kiến thức khi complexity yêu cầu.
  v5.1: Tích hợp Anti-Slop Protocol, Brief Inference, Pre-Flight Check.
version: 5.1
priority: HIGH
---

## When to Activate

- UI/UX tasks: tạo page, component, landing, dashboard, redesign
- NOT for: sửa bug, thêm field, refactor backend → 🟢 SKIP

## ⚡ ROUTING

```
USER REQUEST
    │
    ├── "Sửa bug", "thêm field", "refactor"         → 🟢 SKIP
    ├── UI đơn giản (≤2 components)                  → 🟡 L1 (bên dưới)
    ├── "Dashboard", "landing page", "redesign"      → 🟠 L2 (đọc sub-files)
    └── "Brand identity", "pitch deck", "prototype"  → 🔴 L3 (Open Design)
```

---

## 🟡 L1: Hard Rules (Luôn áp dụng — 0 token thêm)

### Brief Inference — Trước khi code
Suy luận trước: loại trang, vibe, đối tượng, brand assets. Output 1 dòng:
> "Reading this as: [loại] cho [đối tượng], vibe [aesthetic]."

### 3 Dials (xác định từ Brief)
- **DESIGN_VARIANCE (1-10):** 1=đối xứng, 10=phá cách. Default 7-8
- **MOTION_INTENSITY (1-10):** 1=tĩnh, 10=spring physics. Default 5-6
- **VISUAL_DENSITY (1-10):** 1=gallery, 10=cockpit. Default 3-4

### Typography & Color
- ❌ CẤM Inter/serif default. ✅ `Geist`, `Outfit`, `Cabinet Grotesk`, `Satoshi`
- ❌ CẤM purple gradient, pure #000/#fff, beige-brass default
- ✅ HSL. Neutral bases (Zinc/Slate) + 1 accent. Max sat < 80%

### Layout
- ✅ Hero max 4 text elements. Headline ≤ 2 dòng. Subtext ≤ 20 chữ
- ❌ CẤM "3 card bằng nhau". CẤM Split-Header (trái H1/phải paragraph)
- ✅ `min-h-[100dvh]` thay vì `h-screen`. CSS Grid over flex-math
- ✅ Nav trên 1 dòng desktop, max 80px height

### Consistency Locks
- **Theme Lock**: 1 theme xuyên suốt. Sections KHÔNG invert
- **Color Lock**: 1 accent toàn trang
- **Shape Lock**: 1 corner-radius system nhất quán

### Motion & Assets
- ✅ Motion phải justify được. ❌ CẤM `addEventListener('scroll')`
- ✅ Reduced motion bắt buộc khi MOTION > 3
- ✅ Image: gen-tool → picsum → placeholder. ❌ CẤM div-fake screenshots

### AI Tells (tóm gọn — chi tiết xem L2)
- ❌ Em-dash (`—`), scroll cues, section-number eyebrows, version labels
- ❌ Fake stats, slop words, decoration strips, locale strips
- ❌ Eyebrow max ceil(sectionCount/3). Marquee max 1/page

---

## 🟠 L2: Deep Knowledge (đọc khi cần)

| Cần gì? | Đọc file | ~Lines |
|---------|----------|--------|
| **AI Tell chi tiết + Content Quality** | [anti-slop-protocol.md](anti-slop-protocol.md) | ~70 |
| **Redesign audit process** | [redesign-protocol.md](redesign-protocol.md) | ~55 |
| Palette/Dark mode | [color-system.md](color-system.md) | ~240 |
| Animation/Motion | [animation-guide.md](animation-guide.md) | ~200 |
| Typography scale | [typography-system.md](typography-system.md) | ~210 |
| Glassmorphism/Effects | [visual-effects.md](visual-effects.md) | ~210 |
| UX Psychology | [ux-psychology.md](ux-psychology.md) | ~390 |
| Decision tree (framework) | [decision-trees.md](decision-trees.md) | ~430 |
| Design tokens | [design-tokens.md](design-tokens.md) | ~195 |

> ⚠️ KHÔNG đọc tất cả. Chỉ đọc file liên quan đến yêu cầu hiện tại.

**Lookup knowledge (Memory MCP):** Dial Inference Table, Design System Mapping, Reference Vocabulary → `memory_search("frontend-design")`.

---

## 🔴 L3: Delegation → Open Design

| Yêu cầu | Delegate vì |
|----------|-------------|
| Pitch deck / Slides | 71 design systems + PPTX export |
| Video promo / Animation | MP4 export + HyperFrames |
| Brand identity / Logo | Brand-grade protocol |
| Prototype Figma-level | Sandboxed preview |

```
💡 npx open-design@latest
```

---

## 📋 Pre-Flight Check (Bắt buộc trước khi trả code UI)

```
[ ] Brief Inference declared? Dial values explicit?
[ ] Hero ≤4 elements, headline ≤2 lines, CTA visible?
[ ] Zero em-dashes? No AI tells (L2 chi tiết)?
[ ] Theme/Color/Shape Lock nhất quán?
[ ] Button contrast WCAG AA? CTA no-wrap?
[ ] Motion justified? Reduced-motion wrapped?
[ ] Real images? Font import? Spacing 4px grid?
[ ] Loading + Error + Empty states? Mobile responsive?
[ ] Copy self-audit passed? No placeholder/TODO?
```

---

## 🔗 Related Skills

| Skill | Khi nào |
|-------|---------|
| [web-design-guidelines](../web-design-guidelines/SKILL.md) | Audit accessibility/performance |
| [mobile-design](../mobile-design/SKILL.md) | React Native/Flutter |
| [app-builder](../app-builder/SKILL.md) | Scaffold app mới |
