# Design Tokens — Hệ Thống Token Chuẩn Hóa

> Chỉ đọc file này khi SKILL.md routing đến L2 (UI phức tạp ≥3 components).

---

## 🎨 Color Palettes (Pick ONE per project)

### Palette 1: "Midnight Ocean" (Tech/SaaS/Dashboard)
```css
:root {
  --bg-primary: hsl(222, 47%, 7%);      /* Deep navy */
  --bg-card: hsl(222, 35%, 11%);
  --bg-elevated: hsl(222, 30%, 15%);
  --accent: hsl(199, 89%, 48%);          /* Cyan blue */
  --accent-hover: hsl(199, 89%, 55%);
  --text-primary: hsl(210, 40%, 96%);
  --text-secondary: hsl(215, 20%, 65%);
  --border: hsl(220, 20%, 18%);
  --success: hsl(142, 71%, 45%);
  --danger: hsl(0, 84%, 60%);
  --warning: hsl(38, 92%, 50%);
}
```

### Palette 2: "Warm Neutral" (E-commerce/Blog/Portfolio)
```css
:root {
  --bg-primary: hsl(40, 33%, 98%);      /* Warm white */
  --bg-card: hsl(0, 0%, 100%);
  --bg-elevated: hsl(40, 20%, 95%);
  --accent: hsl(16, 85%, 55%);           /* Warm coral */
  --accent-hover: hsl(16, 85%, 48%);
  --text-primary: hsl(20, 14%, 11%);
  --text-secondary: hsl(20, 8%, 45%);
  --border: hsl(30, 15%, 88%);
  --success: hsl(152, 60%, 40%);
  --danger: hsl(350, 80%, 55%);
  --warning: hsl(43, 96%, 56%);
}
```

### Palette 3: "Neon Terminal" (Developer tools/CLI/Gaming)
```css
:root {
  --bg-primary: hsl(0, 0%, 4%);         /* Near black */
  --bg-card: hsl(0, 0%, 8%);
  --bg-elevated: hsl(0, 0%, 12%);
  --accent: hsl(142, 100%, 50%);         /* Neon green */
  --accent-hover: hsl(142, 100%, 60%);
  --text-primary: hsl(0, 0%, 92%);
  --text-secondary: hsl(0, 0%, 55%);
  --border: hsl(0, 0%, 16%);
  --success: hsl(142, 71%, 45%);
  --danger: hsl(0, 100%, 60%);
  --warning: hsl(50, 100%, 55%);
}
```

### Palette 4: "Finance Pro" (Fintech/Trading/Banking)
```css
:root {
  --bg-primary: hsl(220, 25%, 6%);
  --bg-card: hsl(220, 20%, 10%);
  --bg-elevated: hsl(220, 18%, 14%);
  --accent: hsl(45, 100%, 51%);          /* Gold */
  --accent-hover: hsl(45, 100%, 60%);
  --text-primary: hsl(0, 0%, 95%);
  --text-secondary: hsl(220, 10%, 60%);
  --border: hsl(220, 15%, 18%);
  --success: hsl(145, 80%, 42%);         /* Tăng/Green */
  --danger: hsl(0, 85%, 55%);            /* Giảm/Red */
  --warning: hsl(38, 92%, 50%);
}
```

### Dark Mode Override Pattern
```css
@media (prefers-color-scheme: dark) {
  :root { /* swap to dark palette */ }
}
/* Or manual toggle: */
[data-theme="dark"] { /* dark vars */ }
```

---

## 📐 Typography Scale

```css
:root {
  --font-sans: 'Inter', 'DM Sans', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Modular scale (1.25 ratio) */
  --text-xs: 0.75rem;    /* 12px — caption, badge */
  --text-sm: 0.875rem;   /* 14px — secondary text, label */
  --text-base: 1rem;     /* 16px — body text */
  --text-lg: 1.25rem;    /* 20px — card title, subtitle */
  --text-xl: 1.75rem;    /* 28px — section heading */
  --text-2xl: 2.25rem;   /* 36px — page title */
  --text-3xl: 3rem;      /* 48px — hero headline */

  --leading-tight: 1.2;
  --leading-normal: 1.5;
  --leading-relaxed: 1.7;

  --weight-normal: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;
}
```

**Import:** `<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">`

---

## 📏 Spacing & Layout

```css
:root {
  /* 4px grid system */
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */

  --container-max: 1200px;
  --container-narrow: 720px;
  --container-padding: var(--space-4);

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-full: 9999px;
}

/* Responsive container */
.container {
  width: 100%;
  max-width: var(--container-max);
  margin: 0 auto;
  padding: 0 var(--container-padding);
}
```

---

## 🌊 Elevation & Depth

```css
:root {
  --shadow-sm: 0 1px 2px hsl(0 0% 0% / 0.05);
  --shadow-md: 0 4px 12px hsl(0 0% 0% / 0.08);
  --shadow-lg: 0 8px 32px hsl(0 0% 0% / 0.12);
  --shadow-xl: 0 16px 48px hsl(0 0% 0% / 0.16);

  /* Dark mode: stronger shadows */
  --shadow-dark-sm: 0 1px 3px hsl(0 0% 0% / 0.3);
  --shadow-dark-md: 0 4px 16px hsl(0 0% 0% / 0.4);
  --shadow-dark-lg: 0 12px 40px hsl(0 0% 0% / 0.5);
}

/* Glass effect (use sparingly) */
.glass {
  background: hsl(0 0% 100% / 0.06);
  backdrop-filter: blur(12px);
  border: 1px solid hsl(0 0% 100% / 0.08);
}
```

---

## ✨ Animation Tokens

```css
:root {
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
}

/* Standard hover */
.interactive {
  transition: transform var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-fast) var(--ease-out),
              background var(--duration-fast) var(--ease-out);
}
.interactive:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
.interactive:active {
  transform: translateY(0) scale(0.98);
}

/* Fade in */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fadeIn var(--duration-normal) var(--ease-out); }

/* Stagger children */
.stagger > * {
  animation: fadeIn var(--duration-normal) var(--ease-out) both;
}
.stagger > *:nth-child(1) { animation-delay: 0ms; }
.stagger > *:nth-child(2) { animation-delay: 60ms; }
.stagger > *:nth-child(3) { animation-delay: 120ms; }
.stagger > *:nth-child(4) { animation-delay: 180ms; }
.stagger > *:nth-child(5) { animation-delay: 240ms; }
```

---

## 📱 Responsive Breakpoints

```css
/* Mobile-first breakpoints */
@media (min-width: 640px)  { /* sm: tablet portrait */ }
@media (min-width: 1024px) { /* lg: desktop */ }
@media (min-width: 1440px) { /* xl: wide desktop */ }

/* Common pattern: grid responsive */
.grid-responsive {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: 1fr;
}
@media (min-width: 640px) {
  .grid-responsive { grid-template-columns: repeat(2, 1fr); }
}
@media (min-width: 1024px) {
  .grid-responsive { grid-template-columns: repeat(3, 1fr); }
}
```

---

## 🧩 Component Patterns (Copy-paste ready)

### Button System
```css
.btn {
  display: inline-flex; align-items: center; gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font: var(--weight-medium) var(--text-sm) / 1 var(--font-sans);
  border-radius: var(--radius-sm); border: none; cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}
.btn-primary { background: var(--accent); color: white; }
.btn-primary:hover { background: var(--accent-hover); transform: translateY(-1px); }
.btn-ghost { background: transparent; color: var(--text-primary); border: 1px solid var(--border); }
.btn-ghost:hover { background: var(--bg-elevated); }
```

### Card System
```css
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  transition: all var(--duration-fast) var(--ease-out);
}
.card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
```

### Input System
```css
.input {
  width: 100%; padding: var(--space-2) var(--space-3);
  font: var(--text-base) var(--font-sans);
  background: var(--bg-primary); color: var(--text-primary);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  transition: border var(--duration-fast) var(--ease-out);
}
.input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px hsl(from var(--accent) h s l / 0.15); }
```
