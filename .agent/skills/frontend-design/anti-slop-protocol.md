# Anti-Slop Protocol — Detailed AI Tell Detection & Prevention

> L2 sub-file. Đọc khi: building marketing pages, landing pages, redesign, hoặc bất kỳ UI nào user-facing.
> Không cần đọc khi: sửa bug, thêm field, refactor backend.

---

## AI Tells — Danh Sách Cấm Chi Tiết

### Typography Tells
- ❌ `Inter` as default (chỉ khi user gọi tên hoặc yêu cầu neutral/Linear-style)
- ❌ Serif default. Cấm `Fraunces`, `Instrument_Serif`. Serif chỉ khi brief gọi đích danh
- ❌ Emphasis bằng cách trộn serif vào headline sans. Dùng italic/bold CÙNG font

### Color Tells
- ❌ Purple/violet gradient mesh lấp chỗ trống
- ❌ AI-default premium palette: warm beige + brass/clay/oxblood + espresso
- ❌ Pure `#000000` hoặc `#ffffff`. Dùng off-black (zinc-950) và off-white
- ❌ Box-shadow đen kịt trên nền sáng (pha màu shadow trùng nền)
- ✅ **Premium-Consumer Alternatives** (rotate, không lặp): Cold Luxury (silver+chrome), Forest (green+bone+amber), Black and Tan, Cobalt+Cream, Terracotta+Slate, monochrome + 1 pop accent

### Layout Tells
- ❌ "3 card tính năng bằng nhau" nằm ngang. Đổi sang bento/zigzag/scroll
- ❌ Split-Header: trái H1 to + phải paragraph nhỏ lơ lửng. Stack vertically
- ❌ 3+ sections liên tiếp dùng cùng layout (zigzag, card row)
- ❌ Hero nhồi nhét > 4 text elements

### Content Tells
- ❌ Em-dash (`—`) hoàn toàn cấm. Dùng hyphen, comma, period
- ❌ Số liệu ảo (99.99%) + từ sáo rỗng ("Elevate", "Unleash", "Seamless", "Next-Gen")
- ❌ Generic names ("John Doe", "Acme", "Nexus", "SmartFlow")
- ❌ Section-number eyebrows ("001 · Capabilities", "06 · how it works")
- ❌ Scroll cues ("Scroll", "↓ scroll", "Scroll to explore")
- ❌ Version labels ảo trong hero (V0.6, BETA) khi không yêu cầu
- ❌ Decoration text strips ở hero bottom ("BRAND. MOTION. SPATIAL.")
- ❌ Locale/city/time/weather strips (trừ brief globally-distributed)
- ❌ "Quietly in use at" / "From the field" / poetic labels
- ❌ Micro-meta sentences dưới eyebrows
- ❌ Photo-credit captions as decoration
- ❌ Pills/labels overlaid on images
- ❌ Version footers trên marketing pages
- ❌ Decorative colored status dots (trừ real semantic state)
- ❌ Middle-dot (`·`) max 1 per line
- ❌ `border-t` + `border-b` trên every row of long lists

### Density Tells
- ❌ Eyebrow count > ceil(sectionCount/3). Đếm cơ học
- ❌ Marquee > 1 per page
- ❌ No Duplicate CTA Intent: "Get in touch" + "Contact us" = cùng intent → chọn 1

---

## Content Quality Gate

1. **Copy Self-Audit bắt buộc**: Đọc lại MỌI visible string. Flag: grammatically broken, unclear referents, AI hallucination
2. Fake-precise numbers (92%, 4.1×) phải có real data hoặc labeled mock
3. 1 copy register per page. Không trộn technical mono + editorial prose + marketing punch
4. Quotes: Max 3 dòng body. Attribution: name + role + (company). Dùng typographic quotes (" ") hoặc none

---

## Image Strategy (thứ tự ưu tiên)

1. **Image-gen tool first** — Nếu có `generate_image`, PHẢI dùng
2. **Real web images** — `https://picsum.photos/seed/{descriptive-seed}/{w}/{h}`
3. **Last resort** — Placeholder slots rõ ràng + nói user cần cung cấp
- ❌ CẤM div-fake screenshots. CẤM hand-rolled decorative SVGs
- ❌ CẤM broken Unsplash links
- ✅ Logo wall = SVG logos thật (Simple Icons / devicon). CẤM plain text wordmarks
