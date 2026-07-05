#!/usr/bin/env python3
"""
brain_builder.py — Auto-Brain Generator (Ag-Kit Standard)

Synthesizes a project's brain by reading:
  - Tầng 1: .agent/cache/repomap.json (codebase structure)
  - Tầng 2: .agent/memory/graph.db (working memory, top decisions)
  - Tầng 3: .agent/knowledge/*.md (architecture rules)
  - Project metadata: package.json / .env

Output:
  - .agent/brain/summary.md  (human+AI readable — primary brain file)
  - .agent/brain/index.json  (machine-readable metadata for global registry)
  - ~/.config/ag-kit/projects.json (global registry for cross-project discovery)

Auto-triggered by:
  - git post-commit hook
  - receptionist_up.sh (on session start)

Usage:
  python3 .agent/scripts/brain_builder.py [--root PROJECT_DIR] [--quick] [--update]
  --quick: only rebuild if source files changed since last brain update
  --update: force rebuild
"""

import argparse
import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

GLOBAL_REGISTRY = Path.home() / ".config" / "ag-kit" / "projects.json"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def read_file_safe(path: Path, max_chars=8000) -> str:
    try:
        text = path.read_text(encoding="utf-8")
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n...[truncated at {max_chars} chars]"
        return text
    except Exception:
        return ""


def read_json_safe(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_project_name(root: Path) -> str:
    # Always use root folder name as project name — subfolder package.json names
    # like "backend" or "frontend" are misleading (not the actual project name)
    pkg = read_json_safe(root / "package.json")
    if pkg.get("name"):
        return pkg["name"]
    return root.name  # e.g. "sohoc", "MoneyHunter" — always correct


def get_tech_stack(root: Path) -> list[str]:
    stack = []
    
    # Search package.json in root and common subfolders
    pkg_paths = [
        root / "package.json",
        root / "backend" / "package.json",
        root / "frontend" / "package.json",
        root / "src" / "package.json",
    ]
    for pkg_path in pkg_paths:
        if pkg_path.exists():
            pkg = read_json_safe(pkg_path)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "typescript" in deps:
                stack.append("TypeScript")
            if "next" in deps:
                stack.append("Next.js")
            if "react" in deps and "Next.js" not in stack:
                stack.append("React")
            if "express" in deps:
                stack.append("Express")
            if "fastify" in deps:
                stack.append("Fastify")
            if deps and not stack:
                stack.append("Node.js")
            break  # Use first found package.json
    
    # Fallback: detect plain JS project by scanning for .js files
    if not stack:
        js_files = list(root.rglob("*.js"))
        js_files = [f for f in js_files if ".agent" not in str(f) and "node_modules" not in str(f)]
        if len(js_files) > 3:
            stack.append("JavaScript")

    # Python detection: check root and subfolders
    for py_indicator in ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"]:
        if (root / py_indicator).exists():
            stack.append("Python")
            break
    # Fallback: detect Python by .py files
    if "Python" not in stack:
        py_files = list(root.rglob("*.py"))
        py_files = [f for f in py_files if ".agent" not in str(f)]
        if len(py_files) > 3:
            stack.append("Python")

    if (root / "Cargo.toml").exists():
        stack.append("Rust")
    if (root / "go.mod").exists():
        stack.append("Go")
    return stack or ["Unknown"]


def get_memory_nodes(root: Path, limit=8) -> list[str]:
    db_path = root / ".agent" / "memory" / "graph.db"
    nodes = []
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            rows = conn.execute(
                "SELECT content, category FROM nodes ORDER BY energy DESC, updated_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            conn.close()
            nodes = [f"[{r[1]}] {r[0][:120]}" for r in rows]
        except Exception:
            pass
            
    # Tự động hút thành tựu (Trò trống) từ Git Log để AI Không bao giờ quên!
    import subprocess
    try:
        git_log = subprocess.run(
            ["git", "log", "-n", "3", "--pretty=format:- %s (%cr)"],
            cwd=str(root), capture_output=True, text=True, timeout=5
        )
        if git_log.stdout:
            nodes.insert(0, "\n**[Auto-Git-Memory] Thành tựu gần nhất:**\n" + git_log.stdout + "\n")
    except Exception:
        pass
        
    return nodes



def get_knowledge_summary(root: Path) -> str:
    knowledge_dir = root / ".agent" / "knowledge"
    if not knowledge_dir.exists():
        return "_No knowledge files found._"
    parts = []
    for md in sorted(knowledge_dir.glob("*.md"))[:6]:
        content = read_file_safe(md, max_chars=800)
        # Extract first meaningful paragraph
        lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
        snippet = " ".join(lines[:3])[:300]
        parts.append(f"**{md.stem}**: {snippet}")
    return "\n".join(parts) if parts else "_Empty._"


def get_repomap_summary(root: Path) -> str:
    db_path = root / ".agent" / "memory" / "graph.db"
    
    # Try symbol DB first (from code_indexer.py)
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            # Check if symbols table exists and has data
            has_symbols = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='symbols'"
            ).fetchone()[0]
            
            if has_symbols:
                sym_count = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
                if sym_count > 0:
                    parts = [f"📊 Code Index: {sym_count} symbols\n"]
                    
                    # Layer breakdown
                    layers = conn.execute(
                        "SELECT layer, COUNT(*) n FROM symbols WHERE layer IS NOT NULL GROUP BY layer ORDER BY n DESC"
                    ).fetchall()
                    if layers:
                        parts.append("Layers: " + " | ".join(f"{r['layer']}({r['n']})" for r in layers))
                    
                    # Top files by symbol count
                    top_files = conn.execute(
                        "SELECT file_path, COUNT(*) n FROM symbols GROUP BY file_path ORDER BY n DESC LIMIT 15"
                    ).fetchall()
                    for f in top_files:
                        syms = conn.execute(
                            "SELECT name, kind FROM symbols WHERE file_path=? ORDER BY line_start LIMIT 8",
                            (f["file_path"],)
                        ).fetchall()
                        sym_str = ", ".join(f"{s['name']}({s['kind'][0]})" for s in syms)
                        parts.append(f"|-- {f['file_path']} [{f['n']}]: {sym_str}")
                    
                    # Routes
                    has_routes = conn.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='routes'"
                    ).fetchone()[0]
                    if has_routes:
                        routes = conn.execute("SELECT method, path, framework FROM routes LIMIT 10").fetchall()
                        if routes:
                            parts.append("\n🌐 Routes:")
                            for r in routes:
                                parts.append(f"  {r['method']} {r['path']} ({r['framework']})")
                    
                    conn.close()
                    return "\n".join(parts)
            conn.close()
        except Exception:
            pass
    
    # Fallback: cached repomap text
    cache = root / ".agent" / "cache" / "repomap.json"
    if cache.exists():
        data = read_json_safe(cache)
        lines = data.get("lines", [])
        return "\n".join(lines[:40]) or "_Empty._"
    # Fallback: run repomap directly
    repomap_script = root / ".agent" / "scripts" / "repomap.py"
    if repomap_script.exists():
        import subprocess
        try:
            result = subprocess.run(
                ["python3", str(repomap_script), str(root), "--max-files", "50"],
                capture_output=True, text=True, timeout=15
            )
            lines = result.stdout.splitlines()[:40]
            return "\n".join(lines) or "_Could not scan._"
        except Exception:
            pass
    return "_RepoMap not available. Run: ag-kit brain_"


def get_env_ports(root: Path) -> dict:
    env_file = root / ".env"
    ports = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "PORT" in line and "=" in line:
                k, _, v = line.partition("=")
                ports[k.strip()] = v.strip().split("#")[0].strip()
    return ports


def needs_rebuild(root: Path) -> bool:
    """Check if any source changed since last brain generation."""
    brain_file = root / ".agent" / "brain" / "summary.md"
    if not brain_file.exists():
        return True
    last_build = brain_file.stat().st_mtime
    check_dirs = [
        root / ".agent" / "knowledge",
        root / "src",
        root / "backend",
    ]
    for d in check_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*.md"):
            if f.stat().st_mtime > last_build:
                return True
        for f in d.rglob("*.ts"):
            if f.stat().st_mtime > last_build:
                return True
    return False


# ─── Core Builder ────────────────────────────────────────────────────────────

def build_brain(root: Path) -> tuple[str, dict]:
    name = get_project_name(root)
    stack = get_tech_stack(root)
    ports = get_env_ports(root)
    memory_nodes = get_memory_nodes(root)
    knowledge = get_knowledge_summary(root)
    repomap = get_repomap_summary(root)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    port_str = " | ".join(f"{k}={v}" for k, v in ports.items()) if ports else "See .env"
    mem_str = "\n".join(f"  - {n}" for n in memory_nodes) if memory_nodes else "  _(No decisions recorded yet)_"

    summary = f"""# 🧠 Project Brain: {name}
> Auto-generated by ag-kit brain_builder | Last updated: {now}
> Root: {root}

---

## 1. Identity (Định danh)
- **Project**: {name}
- **Stack**: {', '.join(stack)}
- **Root**: `{root}`
- **Ports**: {port_str}

---

## 2. Codebase Structure (Tầng 1 — Repomap)
```
{repomap}
```

---

## 3. Architecture & Rules (Tầng 3 — Knowledge Base)
{knowledge}

---

## 4. Recent Decisions (Tầng 2 — Working Memory)
{mem_str}

---

## 5. How to Read This Brain (Cross-Project Usage)
If you are an AI Agent working in ANOTHER project and need to understand **{name}**:
1. Read this file — it gives a complete overview in ~500 tokens.
2. For deeper code context: `vfs {root}/src`
3. For live physical memory (AG-KIT V5): Read markdown files inside `{root}/.agent/knowledge/nodes/`
4. For semantic vector search: `python3 {root}/.agent/scripts/memory_tool.py search <keyword>`

---
_Auto-generated. Do not edit manually — changes will be overwritten on next rebuild._
"""

    index = {
        "name": name,
        "root": str(root),
        "stack": stack,
        "ports": ports,
        "brain_path": str(root / ".agent" / "brain" / "summary.md"),
        "updated_at": now,
    }
    return summary, index


def update_global_registry(index: dict):
    GLOBAL_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    registry = {}
    if GLOBAL_REGISTRY.exists():
        try:
            registry = json.loads(GLOBAL_REGISTRY.read_text())
        except Exception:
            pass
    registry[index["name"]] = index
    GLOBAL_REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False))


def write_brain(root: Path, summary: str, index: dict):
    brain_dir = root / ".agent" / "brain"
    brain_dir.mkdir(parents=True, exist_ok=True)
    (brain_dir / "summary.md").write_text(summary, encoding="utf-8")
    (brain_dir / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False))


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Ag-Kit Brain Builder — Auto-generate project brain.")
    p.add_argument("--root", default=".", help="Project root directory (default: current dir)")
    p.add_argument("--quick", action="store_true", help="Skip rebuild if no source changes detected")
    p.add_argument("--update", action="store_true", help="Force rebuild (default behavior)")
    args = p.parse_args()

    root = Path(args.root).resolve()

    if args.quick and not needs_rebuild(root):
        print(f"⚡ Brain is up-to-date for: {root.name} (use --update to force)")
        return

    print(f"🧠 Building brain for: {root.name}...")
    summary, index = build_brain(root)
    write_brain(root, summary, index)
    update_global_registry(index)

    brain_path = root / ".agent" / "brain" / "summary.md"
    print(f"✅ Brain saved: {brain_path}")
    print(f"📋 Global registry updated: {GLOBAL_REGISTRY}")


if __name__ == "__main__":
    main()
