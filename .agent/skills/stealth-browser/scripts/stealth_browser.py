#!/usr/bin/env python3
"""
stealth_browser.py — AG-Kit CloakBrowser wrapper

Ready-to-use stealth browser operations for any project.
Requires: pip install cloakbrowser

Commands:
  test                  — Run stealth detection tests
  scrape <url>          — Scrape page content (returns text)
  screenshot <url> <f>  — Screenshot a page
  login <url> <profile> — Start persistent session for manual login
  eval <url> <js>       — Evaluate JS on a stealth page

Usage:
  python .agent/scripts/stealth_browser.py test
  python .agent/scripts/stealth_browser.py scrape https://protected-site.com
  python .agent/scripts/stealth_browser.py screenshot https://target.com shot.png
  python .agent/scripts/stealth_browser.py login https://app.com ./my-profile
  python .agent/scripts/stealth_browser.py eval https://example.com "document.title"
"""

import json
import sys
import os
import time


def check_install():
    """Check if cloakbrowser is installed."""
    try:
        import cloakbrowser
        return True
    except ImportError:
        return False


def auto_install():
    """Auto-install cloakbrowser if missing. Returns True if ready."""
    if check_install():
        return True

    print("🔧 CloakBrowser not installed. Auto-installing...")
    import subprocess
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "cloakbrowser"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )
        print("  ✅ cloakbrowser installed")
        return True
    except subprocess.CalledProcessError:
        print("  ❌ Failed to install cloakbrowser")
        print("     Manual fix: pip install cloakbrowser")
        return False


def ensure_binary_ready():
    """Ensure stealth Chromium binary is downloaded."""
    try:
        from cloakbrowser import binary_info, __version__
        info = binary_info()
        if info['installed']:
            return True
        print("📥 Downloading stealth Chromium binary (~200MB, one-time)...")
        from cloakbrowser.download import ensure_binary
        ensure_binary()
        return True
    except Exception as e:
        print(f"  ❌ Binary download failed: {e}")
        return False


def cmd_setup():
    """Full auto-setup: install package + download binary + verify stealth."""
    print("🕵️  AG-Kit Stealth Browser — Auto Setup")
    print("=" * 50)

    # Step 1: Install package
    if not check_install():
        if not auto_install():
            return 1
    else:
        from cloakbrowser import __version__
        print(f"  ✅ cloakbrowser v{__version__} installed")

    # Step 2: Download binary
    if not ensure_binary_ready():
        return 1

    from cloakbrowser import binary_info
    info = binary_info()
    print(f"  ✅ Chromium {info['version']} ready")
    print(f"     Binary: {info['binary_path']}")

    # Step 3: Stealth verification
    print()
    print("  Running stealth checks...")
    result = cmd_test()

    if result == 0:
        print()
        print("  🎉 Stealth Browser is READY!")
        print()
        print("  Usage in your code:")
        print("  ────────────────────")
        print("  from cloakbrowser import launch")
        print("  browser = launch(humanize=True)")
        print("  page = browser.new_page()")
        print("  page.goto('https://target.com')")
        print("  browser.close()")
    return result


def cmd_test():
    """Run quick stealth verification."""
    from cloakbrowser import launch

    print("🕵️  CloakBrowser Stealth Quick Test")
    print("=" * 50)

    browser = launch(headless=True)
    page = browser.new_page()

    # Test 1: navigator.webdriver
    page.goto("about:blank")
    webdriver = page.evaluate("navigator.webdriver")
    plugins = page.evaluate("navigator.plugins.length")
    chrome_obj = page.evaluate("typeof window.chrome")
    ua = page.evaluate("navigator.userAgent")

    print(f"  navigator.webdriver : {webdriver} {'✅' if not webdriver else '❌'}")
    print(f"  plugins.length      : {plugins} {'✅' if plugins > 0 else '❌'}")
    print(f"  window.chrome       : {chrome_obj} {'✅' if chrome_obj == 'object' else '❌'}")
    print(f"  HeadlessChrome leak : {'❌ LEAK' if 'HeadlessChrome' in ua else '✅ Clean'}")
    print(f"  User-Agent          : {ua[:80]}...")

    # Test 2: WebGL
    gpu = page.evaluate("""() => {
        const c = document.createElement('canvas');
        const gl = c.getContext('webgl');
        if (!gl) return 'N/A';
        const dbg = gl.getExtension('WEBGL_debug_renderer_info');
        return dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : 'N/A';
    }""")
    print(f"  WebGL GPU           : {gpu}")

    # Test 3: Platform
    platform_val = page.evaluate("navigator.platform")
    cores = page.evaluate("navigator.hardwareConcurrency")
    memory = page.evaluate("navigator.deviceMemory")
    screen_w = page.evaluate("screen.width")
    screen_h = page.evaluate("screen.height")
    print(f"  Platform            : {platform_val}")
    print(f"  Cores/Memory        : {cores} / {memory}GB")
    print(f"  Screen              : {screen_w}x{screen_h}")

    browser.close()

    passed = sum([
        not webdriver,
        plugins > 0,
        chrome_obj == 'object',
        'HeadlessChrome' not in ua,
    ])
    print(f"\n  Result: {passed}/4 stealth checks passed")
    print("=" * 50)
    return 0 if passed == 4 else 1


def cmd_scrape(url):
    """Scrape a URL and return page text content."""
    from cloakbrowser import launch

    print(f"🕵️  Scraping: {url}")
    browser = launch(headless=True, humanize=False)
    page = browser.new_page()

    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        title = page.title()
        text = page.evaluate("document.body.innerText")

        print(f"  Title: {title}")
        print(f"  Length: {len(text)} chars")
        print("-" * 50)
        print(text[:2000])
        if len(text) > 2000:
            print(f"\n... ({len(text) - 2000} more chars)")

    finally:
        browser.close()
    return 0


def cmd_screenshot(url, output_path):
    """Take a screenshot of a URL."""
    from cloakbrowser import launch

    print(f"📸 Screenshot: {url} → {output_path}")
    browser = launch(headless=True)
    page = browser.new_page()

    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(2)
        page.screenshot(path=output_path, full_page=True)
        print(f"  ✅ Saved: {output_path}")
    finally:
        browser.close()
    return 0


def cmd_login(url, profile_dir):
    """Start a headed persistent session for manual login."""
    from cloakbrowser import launch_persistent_context

    print(f"🔑 Persistent session: {url}")
    print(f"   Profile: {profile_dir}")
    print("   Login manually, then close the browser window to save session.")
    print()

    ctx = launch_persistent_context(
        profile_dir,
        headless=False,
        humanize=True,
        human_preset="careful",
    )
    page = ctx.new_page()
    page.goto(url)

    # Wait for user to close manually
    try:
        input("   Press Enter when done to save session and exit...")
    except (KeyboardInterrupt, EOFError):
        pass

    ctx.close()
    print(f"  ✅ Session saved to {profile_dir}")
    return 0


def cmd_eval(url, js_code):
    """Evaluate JavaScript on a stealth page."""
    from cloakbrowser import launch

    browser = launch(headless=True)
    page = browser.new_page()

    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(1)
        result = page.evaluate(js_code)
        print(json.dumps(result, indent=2, ensure_ascii=False) if isinstance(result, (dict, list)) else str(result))
    finally:
        browser.close()
    return 0


def cmd_info():
    """Show CloakBrowser installation info."""
    from cloakbrowser import binary_info, __version__

    info = binary_info()
    print(f"🕵️  CloakBrowser v{__version__}")
    print(f"   Chromium: {info['version']}")
    print(f"   Platform: {info['platform']}")
    print(f"   Installed: {'✅' if info['installed'] else '❌'}")
    print(f"   Binary: {info['binary_path']}")
    print(f"   Cache: {info['cache_dir']}")
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    cmd = sys.argv[1]

    # setup command works even without cloakbrowser installed
    if cmd == "setup":
        return cmd_setup()

    # All other commands need cloakbrowser
    if not check_install():
        print("❌ cloakbrowser not installed.")
        print("   Run: python %s setup" % sys.argv[0])
        print("   This will auto-install and configure everything.")
        return 1

    if cmd == "test":
        return cmd_test()
    elif cmd == "info":
        return cmd_info()
    elif cmd == "scrape" and len(sys.argv) >= 3:
        return cmd_scrape(sys.argv[2])
    elif cmd == "screenshot" and len(sys.argv) >= 4:
        return cmd_screenshot(sys.argv[2], sys.argv[3])
    elif cmd == "login" and len(sys.argv) >= 4:
        return cmd_login(sys.argv[2], sys.argv[3])
    elif cmd == "eval" and len(sys.argv) >= 4:
        return cmd_eval(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
