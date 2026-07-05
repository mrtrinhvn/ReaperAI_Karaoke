# Redesign Protocol — Audit-First Methodology

> L2 sub-file. Đọc khi: redesigning existing pages, UI modernisation.
> Không cần đọc khi: building greenfield, fixing bugs.

---

## 1. Detect Mode

| Signal | Mode |
|---|---|
| Không có codebase cũ | Greenfield |
| "Improve / modernize / refresh" | Redesign-Preserve |
| "Redo / overhaul / from scratch" | Redesign-Overhaul |

## 2. Audit Before Touching

Trước khi code bất kỳ thứ gì, document:
- **Brand tokens có sẵn**: logo, colors, fonts → đây là material khởi đầu
- **IA (Information Architecture)**: page slugs, nav labels, anchor IDs
- **Content blocks**: preserve vs retire
- **Patterns to retire**: AI-slop tells, broken layouts, dead links
- **Dial reading hiện tại**: infer existing VARIANCE / MOTION / DENSITY. Đây là starting point
- **SEO baseline**: ranking pages, meta titles, structured data, OG cards. **SEO migration là rủi ro #1**

## 3. Preservation Rules (Không đổi trừ khi được yêu cầu)

- URL structure / route slugs
- Primary nav labels
- Form field names or order (breaks analytics + autofill)
- Brand logo or wordmark
- Legal / consent / cookie copy
- Existing accessibility wins (focus states, alt text, keyboard nav, contrast)
- Analytics event names (button IDs, section IDs downstream tracking phụ thuộc)

## 4. Modernisation Priority (dừng khi brief thỏa mãn)

1. **Typography refresh** — visual lift lớn nhất, rủi ro thấp nhất
2. **Spacing & rhythm** — tăng section padding, fix vertical rhythm
3. **Color recalibration** — desaturate, unify neutrals, giữ brand accent
4. **Motion layer** — thêm micro-interactions phù hợp MOTION_INTENSITY
5. **Hero & key-section recomposition** — restructure top-of-funnel
6. **Full block replacement** — chỉ khi block cũ không thể cứu

## 5. Decision Tree

- IA + content + SEO sound → **targeted evolution** (Levers 1-4). ~70% value, ~40% risk
- Visual debt cấu trúc (broken IA, no design system, broken mobile) → **full redesign** với strict content preservation
- Brand đang thay đổi → **greenfield**
