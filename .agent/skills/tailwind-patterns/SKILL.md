---
name: tailwind-patterns
description: Tailwind CSS v4 decision rules. CSS-first config, container queries, design tokens.
priority: P2
---

## When to Activate

- Using Tailwind CSS in a project
- Choosing CSS architecture or design token strategy

# Tailwind CSS v4 Rules

> AI model đã biết Tailwind utilities, flexbox, grid.
> File này = v4 changes + decision rules. Không reference tables.

---

## v3 → v4 Key Changes

| v3 | v4 |
|---|---|
| `tailwind.config.js` | CSS-based `@theme` directive |
| PostCSS plugin | Oxide engine (10x faster) |
| JIT mode opt-in | Native, always-on |
| `@apply` encouraged | Discouraged — prefer components |

## Hard Rules

### Configuration
- ✅ v4: Define tokens in CSS `@theme {}`, NOT in JS config
- ✅ Use `oklch()` for colors (perceptually uniform). Avoid raw RGB
- ✅ Semantic token layers: Primitive (`--blue-500`) → Semantic (`--color-primary`) → Component (`--button-bg`)
- ❌ CẤM mix v3 config with v4. Migrate fully to CSS-first

### Layout
- ✅ Mobile-first: base styles no prefix, `md:` for tablet, `lg:` for desktop
- ✅ Reusable components → Container queries (`@container`) not viewport breakpoints
- ✅ Grid > Flexbox for complex layouts. `auto-fit` + `minmax` for responsive grids
- ✅ Prefer asymmetric/Bento layouts over symmetric 3-column grids

### Dark Mode
| Method | When |
|---|---|
| `class` | Manual theme switcher |
| `media` | Follow system preference |
| `selector` | Complex theming (v4) |

### Component Extraction
| Signal | Action |
|---|---|
| Same class combo 3+ times | Extract to component |
| Complex state variants | Extract to component |
| Design system element | Extract + document |
- ✅ Extract via React/Vue component (preferred) or `@apply` in CSS
- ❌ CẤM duplicate long class lists. CẤM arbitrary values everywhere
- ❌ CẤM `!important`. CẤM `style=` inline. CẤM heavy `@apply`

### Performance
- ✅ No dynamic class strings (template interpolation breaks purge)
- ✅ Oxide engine auto-purges unused CSS

### Breakpoints

| Prefix | Min Width | Target |
|---|---|---|
| (none) | 0px | Mobile base |
| `sm:` | 640px | Large phone |
| `md:` | 768px | Tablet |
| `lg:` | 1024px | Laptop |
| `xl:` | 1280px | Desktop |
| `2xl:` | 1536px | Large desktop |
