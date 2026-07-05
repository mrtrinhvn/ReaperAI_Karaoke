#!/usr/bin/env python3
"""
repomap.py — Ag-Kit RepoMap (v2.0 — Graph-backed)

Generates a structural map of the codebase by reading from:
  1. code_indexer's graph.db (primary, zero-dependency)
  2. Simple filesystem walk (fallback, no tree-sitter needed)

v2.0 replaces the broken tree_sitter_languages dependency
with direct SQLite reads from graph.db (populated by code_indexer.py).

Usage:
  python3 .agent/scripts/repomap.py [root] [-o output.json] [--max-files N]
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".agent", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "coverage", ".cache", ".aider",
}
SKIP_EXTS = {".pyc", ".o", ".a", ".so", ".map", ".lock", ".min.js", ".min.css"}


def generate_from_graphdb(root: Path, db_path: Path, max_files: int = 100) -> str:
    """Read symbols from code_indexer's graph.db."""
    if not db_path.exists():
        return ""
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        # Check symbols table exists
        has = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='symbols'"
        ).fetchone()[0]
        if not has:
            conn.close()
            return ""

        count = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        if count == 0:
            conn.close()
            return ""

        lines = []
        top_files = conn.execute(
            "SELECT file_path, COUNT(*) n FROM symbols GROUP BY file_path ORDER BY file_path LIMIT ?",
            (max_files,)
        ).fetchall()

        for f in top_files:
            syms = conn.execute(
                "SELECT name, kind, line_start FROM symbols WHERE file_path=? ORDER BY line_start",
                (f["file_path"],)
            ).fetchall()
            lines.append(f"|-- {f['file_path']}")
            for s in syms[:15]:  # limit symbols per file
                kind_short = {"function": "fn", "class": "cls", "method": "meth",
                              "interface": "iface", "enum": "enum", "type": "type"}.get(s["kind"], s["kind"])
                lines.append(f"|   |-- {s['name']} ({kind_short}, L{s['line_start']})")

        # Routes
        has_routes = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='routes'"
        ).fetchone()[0]
        if has_routes:
            routes = conn.execute("SELECT method, path, framework FROM routes ORDER BY path LIMIT 20").fetchall()
            if routes:
                lines.append("")
                lines.append("🌐 Routes:")
                for r in routes:
                    lines.append(f"  {r['method']} {r['path']} ({r['framework']})")

        conn.close()
        return "\n".join(lines)
    except Exception:
        return ""


def generate_from_filesystem(root: Path, max_files: int = 100) -> str:
    """Simple filesystem walk fallback — no tree-sitter needed."""
    repo_map = []
    count = 0
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel_root = os.path.relpath(dirpath, root)
        if rel_root == ".":
            rel_root = ""
        for fn in sorted(files):
            if count >= max_files:
                break
            if fn.startswith("."):
                continue
            ext = Path(fn).suffix
            if ext in SKIP_EXTS:
                continue
            rel_path = os.path.join(rel_root, fn) if rel_root else fn
            repo_map.append(f"|-- {rel_path}")
            count += 1
    return "\n".join(repo_map)


def generate_map(root: Path, max_files: int = 100) -> str:
    """Generate repomap: try graph.db first, fallback to filesystem."""
    db_path = root / ".agent" / "memory" / "graph.db"
    result = generate_from_graphdb(root, db_path, max_files)
    if result:
        return result
    return generate_from_filesystem(root, max_files)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RepoMapper v2.0: Graph-backed codebase map")
    parser.add_argument("root", nargs="?", default=".", help="Root directory (default: current dir)")
    parser.add_argument("--output", "-o", help="Output file path (e.g. .agent/cache/repomap.json)")
    parser.add_argument("--max-files", type=int, default=100, help="Max files to scan (default: 100)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    text_map = generate_map(root, max_files=args.max_files)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if args.format == "json" or args.output.endswith(".json"):
            data = {
                "generated_at": datetime.now().isoformat(),
                "root": str(root),
                "engine": "graph.db" if (root / ".agent" / "memory" / "graph.db").exists() else "filesystem",
                "map": text_map,
                "lines": text_map.splitlines()
            }
            output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            output_path.write_text(text_map)
        print(f"✅ RepoMap saved to: {output_path.absolute()}")
    else:
        print(text_map)
