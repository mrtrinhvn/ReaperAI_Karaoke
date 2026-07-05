---
name: stealth-browser
description: >
  CloakBrowser integration — stealth Chromium that passes every bot detection test.
  Drop-in Playwright replacement with 58 source-level C++ fingerprint patches.
  Use for web scraping, booking automation, P2P trading, and any site with anti-bot protection.
activation_triggers:
  - browser automation
  - stealth browser
  - web scraping protected site
  - bypass captcha
  - cloudflare turnstile
  - recaptcha
  - fingerprint detection
  - anti-bot
  - cloakbrowser
  - humanize click
  - persistent browser session
  - booking bot
  - P2P automation
  - playwright
  - puppeteer
  - headless chrome
  - scrape website
  - login automation
---

# 🕵️ Stealth Browser (CloakBrowser Integration)

> Stealth Chromium binary with 58 C++ source-level patches. Pass Cloudflare, reCAPTCHA, FingerprintJS, and 30+ detection systems.

## 🔴 AUTO-SETUP GUARD (MANDATORY)

**Before writing ANY code that uses browser/Playwright/scraping, you MUST run this check:**

```bash
python .agent/skills/stealth-browser/scripts/stealth_browser.py setup
```

This command will:
1. ✅ Check if `cloakbrowser` is installed → auto-install if missing
2. ✅ Check if Chromium binary is downloaded → auto-download if missing
3. ✅ Run 4-point stealth verification
4. ✅ Print ready-to-use import snippet

**If the project uses browser automation (detected by `playwright`, `selenium`, `puppeteer`, `requests`, `httpx` in dependencies), this skill is AUTO-ACTIVATED.**

### Auto-Detection Rules

AI MUST activate this skill when:
- Project has `playwright` or `puppeteer` in `package.json` / `requirements.txt`
- User mentions **scraping**, **booking**, **P2P**, **login automation**
- Code imports `playwright`, `selenium`, or `requests` for web interaction
- Target URL has Cloudflare, reCAPTCHA, or known bot detection

### Migration: Replace Stock Playwright

When this skill is active, ALL browser code should use CloakBrowser:

```diff
# Python
- from playwright.sync_api import sync_playwright
- pw = sync_playwright().start()
- browser = pw.chromium.launch()
+ from cloakbrowser import launch
+ browser = launch(humanize=True)

# Node.js  
- import { chromium } from 'playwright';
- const browser = await chromium.launch();
+ import { launch } from 'cloakbrowser';
+ const browser = await launch({ humanize: true });
```

## When to Activate

- User needs to **automate a website with anti-bot protection**
- User mentions **Cloudflare, reCAPTCHA, captcha bypass**
- User needs **human-like browser interaction** (click, type, scroll)
- User wants **persistent browser sessions** (cookies survive restarts)
- Task involves **web scraping protected sites** (Binance P2P, booking sites, etc.)
- User mentions **stealth**, **anti-detect**, **fingerprint**

## Quick Start — 5 Usage Patterns

### 1. Basic Stealth (simplest)

```python
from cloakbrowser import launch

browser = launch()  # headless, random fingerprint
page = browser.new_page()
page.goto("https://protected-site.com")
print(page.title())
browser.close()
```

### 2. Human-Like Interaction (booking, forms)

```python
from cloakbrowser import launch

browser = launch(headless=False, humanize=True)
page = browser.new_page()

page.goto("https://booking-site.com")
page.locator("#email").fill("user@example.com")  # per-char typing with pauses
page.locator("#password").fill("secret123")       # realistic timing
page.locator("button[type=submit]").click()       # Bézier mouse curve
browser.close()
```

### 3. Async (for event loops / FastAPI backends)

```python
import asyncio
from cloakbrowser import launch_async

async def scrape():
    browser = await launch_async(humanize=True)
    page = await browser.new_page()
    await page.goto("https://target.com")
    data = await page.evaluate("document.body.innerText")
    await browser.close()
    return data

asyncio.run(scrape())
```

### 4. Persistent Session (stay logged in across restarts)

```python
from cloakbrowser import launch_persistent_context

# First run — login, cookies saved
ctx = launch_persistent_context("./browser-profile", headless=False)
page = ctx.new_page()
page.goto("https://app.example.com/login")
ctx.close()

# Next run — already logged in
ctx = launch_persistent_context("./browser-profile", headless=False)
```

### 5. With Proxy + GeoIP

```python
from cloakbrowser import launch

browser = launch(
    proxy="http://user:pass@residential-proxy:port",
    geoip=True,
    headless=False,
    humanize=True,
    human_preset="careful",
)
```

## Key Parameters

| Param | Type | Default | Purpose |
|:--|:--|:--|:--|
| `headless` | bool | `True` | Show browser window |
| `proxy` | str/dict | `None` | Proxy URL or dict |
| `humanize` | bool | `False` | Human-like mouse/keyboard/scroll |
| `human_preset` | str | `"default"` | `"default"` or `"careful"` |
| `geoip` | bool | `False` | Auto timezone/locale from proxy |
| `args` | list | `None` | Extra Chromium CLI args |

## Wrapper Script Commands

```bash
python .agent/skills/stealth-browser/scripts/stealth_browser.py setup       # Auto-install + verify
python .agent/skills/stealth-browser/scripts/stealth_browser.py test        # Quick stealth check
python .agent/skills/stealth-browser/scripts/stealth_browser.py scrape URL  # Scrape protected page
python .agent/skills/stealth-browser/scripts/stealth_browser.py screenshot URL out.png
python .agent/skills/stealth-browser/scripts/stealth_browser.py login URL ./profile
python .agent/skills/stealth-browser/scripts/stealth_browser.py info
```
