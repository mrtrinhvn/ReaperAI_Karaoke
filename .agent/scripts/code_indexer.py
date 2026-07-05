#!/usr/bin/env python3
"""
code_indexer.py — Ag-Kit Code Intelligence Indexer (v2.0)

Scans codebase using Tree-sitter AST, stores structured symbols,
import relationships, and framework routes into SQLite.

Uses cursor-based AST walking (compatible with tree-sitter 0.20-0.24+).

Usage:
  python3 .agent/scripts/code_indexer.py [--root PROJECT_DIR] [--full]
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# ─── Auto-bootstrap ─────────────────────────────────────────────────────────
def _ensure_deps():
    needed = []
    try:
        import tree_sitter
    except ImportError:
        needed.append("tree-sitter")
    for pkg in ["tree_sitter_python", "tree_sitter_javascript", "tree_sitter_typescript"]:
        try:
            __import__(pkg)
        except ImportError:
            needed.append(pkg.replace("_", "-"))
    if needed:
        import subprocess
        print(f"📦 Installing: {', '.join(needed)}")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + needed, capture_output=True)

_ensure_deps()

from tree_sitter import Language, Parser

# ─── Language Setup ──────────────────────────────────────────────────────────

_LANGS = {}

def _load_lang(name: str):
    if name in _LANGS:
        return _LANGS[name]
    try:
        if name == "python":
            import tree_sitter_python as m
            _LANGS[name] = Language(m.language())
        elif name == "javascript":
            import tree_sitter_javascript as m
            _LANGS[name] = Language(m.language())
        elif name == "typescript":
            import tree_sitter_typescript as m
            _LANGS[name] = Language(m.language_typescript())
        elif name == "tsx":
            import tree_sitter_typescript as m
            _LANGS[name] = Language(m.language_tsx())
        else:
            return None
    except Exception:
        return None
    return _LANGS.get(name)

EXT_TO_LANG = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".tsx": "tsx", ".jsx": "javascript",
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".agent", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "coverage", ".cache",
}
SKIP_EXTS = {".pyc", ".o", ".a", ".so", ".map", ".lock", ".min.js"}

# Node types that represent definitions
DEF_TYPES = {
    # Python
    "function_definition", "class_definition",
    # JS/TS
    "function_declaration", "class_declaration", "method_definition",
    "arrow_function", "generator_function_declaration",
    # TS specific
    "interface_declaration", "type_alias_declaration", "enum_declaration",
}

# Node types for imports
IMPORT_TYPES = {
    "import_statement", "import_from_statement",  # Python
    "import_declaration",  # JS/TS (tree-sitter uses this)
}

LAYER_RULES = {
    "api":     [r"routes?/", r"controllers?/", r"handlers?/", r"api/", r"endpoints?/"],
    "service": [r"services?/", r"usecases?/", r"interactors?/", r"business/"],
    "data":    [r"models?/", r"schemas?/", r"repositories?/", r"dao/", r"entities?/"],
    "ui":      [r"components?/", r"views?/", r"pages?/", r"layouts?/", r"templates?/"],
    "util":    [r"utils?/", r"helpers?/", r"lib/", r"common/", r"shared/"],
    "config":  [r"config/", r"settings?/"],
    "test":    [r"tests?/", r"__tests__/", r"spec/", r"_test\."],
}

ROUTE_PATTERNS = {
    "fastapi": re.compile(r'@\w+\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', re.I),
    "express": re.compile(r'\.(get|post|put|delete|patch|all)\(\s*["\']([^"\']+)["\']', re.I),
}

DEFAULT_DB = Path(__file__).parent.parent / "memory" / "graph.db"


# ─── Schema ──────────────────────────────────────────────────────────────────

def ensure_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS symbols (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL, name TEXT NOT NULL, kind TEXT NOT NULL,
            line_start INTEGER, line_end INTEGER, signature TEXT,
            parent_id INTEGER REFERENCES symbols(id),
            layer TEXT, file_hash TEXT, indexed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS struct_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_symbol INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
            to_symbol INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
            relation TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method TEXT, path TEXT,
            handler_symbol INTEGER REFERENCES symbols(id),
            framework TEXT, file_path TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_sym_file ON symbols(file_path);
        CREATE INDEX IF NOT EXISTS idx_sym_name ON symbols(name);
        CREATE INDEX IF NOT EXISTS idx_sym_kind ON symbols(kind);
        CREATE INDEX IF NOT EXISTS idx_se_from ON struct_edges(from_symbol);
        CREATE INDEX IF NOT EXISTS idx_route_path ON routes(path);
    """)
    conn.commit()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def fhash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]

def detect_layer(rel: str):
    for layer, pats in LAYER_RULES.items():
        for p in pats:
            if re.search(p, rel, re.I):
                return layer
    return None

def _get_name(node):
    """Extract the name identifier from a definition node."""
    for child in node.children:
        if child.type in ("identifier", "property_identifier", "type_identifier"):
            return child.text.decode("utf-8")
    # For variable_declarator parents
    if node.type == "variable_declarator":
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf-8")
    return None

def _get_kind(node_type: str) -> str:
    if "class" in node_type: return "class"
    if "interface" in node_type: return "interface"
    if "enum" in node_type: return "enum"
    if "type_alias" in node_type: return "type"
    if "method" in node_type: return "method"
    return "function"


# ─── Core Indexer ────────────────────────────────────────────────────────────

class CodeIndexer:
    def __init__(self, root: Path, db_path: Path):
        self.root = root.resolve()
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        ensure_schema(self.conn)
        self.stats = {"files": 0, "symbols": 0, "edges": 0, "routes": 0, "skipped": 0}

    def _existing_hashes(self) -> dict:
        rows = self.conn.execute("SELECT DISTINCT file_path, file_hash FROM symbols").fetchall()
        return {r["file_path"]: r["file_hash"] for r in rows}

    def _clear_file(self, rel):
        ids = [r[0] for r in self.conn.execute("SELECT id FROM symbols WHERE file_path=?", (rel,)).fetchall()]
        if ids:
            ph = ",".join("?" * len(ids))
            self.conn.execute(f"DELETE FROM struct_edges WHERE from_symbol IN ({ph}) OR to_symbol IN ({ph})", ids + ids)
            self.conn.execute(f"DELETE FROM symbols WHERE id IN ({ph})", ids)
        self.conn.execute("DELETE FROM routes WHERE file_path=?", (rel,))

    def _walk_symbols(self, node, content: str, rel: str, fh: str, layer, now, parent_sym_id=None):
        """Recursively walk AST and extract definitions."""
        for child in node.children:
            if child.type in DEF_TYPES:
                name = _get_name(child)
                if not name:
                    # For arrow functions assigned to variables
                    if child.parent and child.parent.type == "variable_declarator":
                        name = _get_name(child.parent)
                if name:
                    kind = _get_kind(child.type)
                    sig_start = child.start_byte
                    sig_end = min(sig_start + 200, child.end_byte)
                    sig = content[sig_start:sig_end].split("\n")[0].strip()

                    cur = self.conn.execute(
                        "INSERT INTO symbols (file_path,name,kind,line_start,line_end,signature,parent_id,layer,file_hash,indexed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (rel, name, kind, child.start_point[0]+1, child.end_point[0]+1, sig[:200], parent_sym_id, layer, fh, now)
                    )
                    self.stats["symbols"] += 1
                    # Recurse for methods inside classes
                    if kind in ("class", "interface"):
                        self._walk_symbols(child, content, rel, fh, layer, now, cur.lastrowid)
                    continue

            # Also catch `export const X = () => {}` patterns (variable_declarator with arrow)
            if child.type == "variable_declarator":
                for sub in child.children:
                    if sub.type in ("arrow_function", "function_expression"):
                        name = _get_name(child)
                        if name:
                            sig = content[child.start_byte:min(child.start_byte+200, child.end_byte)].split("\n")[0].strip()
                            self.conn.execute(
                                "INSERT INTO symbols (file_path,name,kind,line_start,line_end,signature,parent_id,layer,file_hash,indexed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                (rel, name, "function", child.start_point[0]+1, child.end_point[0]+1, sig[:200], parent_sym_id, layer, fh, now)
                            )
                            self.stats["symbols"] += 1
                        break

            # Recurse deeper
            self._walk_symbols(child, content, rel, fh, layer, now, parent_sym_id)

    def _extract_imports(self, node, rel: str, now: str):
        """Extract import sources for struct_edges."""
        for child in node.children:
            if child.type in IMPORT_TYPES or child.type == "import_statement":
                # Find the source/module string
                for sub in child.children:
                    if sub.type in ("string", "string_literal"):
                        mod = sub.text.decode("utf-8").strip("'\"")
                        from_sym = self.conn.execute("SELECT id FROM symbols WHERE file_path=? LIMIT 1", (rel,)).fetchone()
                        if from_sym:
                            to_sym = self.conn.execute("SELECT id FROM symbols WHERE file_path LIKE ? LIMIT 1", (f"%{mod.replace('.', '/')}%",)).fetchone()
                            if to_sym and to_sym["id"] != from_sym["id"]:
                                self.conn.execute("INSERT INTO struct_edges (from_symbol,to_symbol,relation,created_at) VALUES (?,?,?,?)",
                                    (from_sym["id"], to_sym["id"], "imports", now))
                                self.stats["edges"] += 1
                    elif sub.type == "dotted_name":
                        # Python imports
                        mod = sub.text.decode("utf-8")
                        from_sym = self.conn.execute("SELECT id FROM symbols WHERE file_path=? LIMIT 1", (rel,)).fetchone()
                        if from_sym:
                            to_sym = self.conn.execute("SELECT id FROM symbols WHERE file_path LIKE ? LIMIT 1", (f"%{mod.replace('.', '/')}%",)).fetchone()
                            if to_sym and to_sym["id"] != from_sym["id"]:
                                self.conn.execute("INSERT INTO struct_edges (from_symbol,to_symbol,relation,created_at) VALUES (?,?,?,?)",
                                    (from_sym["id"], to_sym["id"], "imports", now))
                                self.stats["edges"] += 1
            else:
                self._extract_imports(child, rel, now)

    def _extract_routes(self, content: str, rel: str):
        for fw, pat in ROUTE_PATTERNS.items():
            for m in pat.finditer(content):
                method, path = m.group(1).upper(), m.group(2)
                line = content[:m.start()].count("\n") + 1
                handler = self.conn.execute(
                    "SELECT id FROM symbols WHERE file_path=? AND line_start>=? AND line_start<=? LIMIT 1",
                    (rel, max(1, line-2), line+5)
                ).fetchone()
                self.conn.execute(
                    "INSERT INTO routes (method,path,handler_symbol,framework,file_path) VALUES (?,?,?,?,?)",
                    (method, path, handler["id"] if handler else None, fw, rel))
                self.stats["routes"] += 1

    def index(self, force_full=False, max_files=500):
        existing = {} if force_full else self._existing_hashes()
        if force_full:
            self.conn.execute("DELETE FROM struct_edges")
            self.conn.execute("DELETE FROM routes")
            self.conn.execute("DELETE FROM symbols")
            self.conn.commit()

        files = []
        for root, dirs, fnames in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fn in fnames:
                fp = Path(root) / fn
                if fp.suffix not in EXT_TO_LANG or fp.suffix in SKIP_EXTS or fn.startswith("."):
                    continue
                rel = str(fp.relative_to(self.root))
                h = fhash(fp)
                if not force_full and existing.get(rel) == h:
                    self.stats["skipped"] += 1
                    continue
                files.append((fp, rel, EXT_TO_LANG[fp.suffix], h))
                if len(files) >= max_files:
                    break

        print(f"📂 {len(files)} files to index ({self.stats['skipped']} unchanged)")
        now = datetime.now().isoformat()

        # Pass 1: symbols + routes
        for fp, rel, lang_name, h in files:
            try:
                content = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            lang = _load_lang(lang_name)
            if not lang:
                continue

            self._clear_file(rel)
            parser = Parser(lang)
            tree = parser.parse(bytes(content, "utf-8"))
            layer = detect_layer(rel)
            self._walk_symbols(tree.root_node, content, rel, h, layer, now)
            self._extract_routes(content, rel)
            self.stats["files"] += 1

        self.conn.commit()

        # Pass 2: imports (needs all symbols)
        for fp, rel, lang_name, h in files:
            try:
                content = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            lang = _load_lang(lang_name)
            if not lang:
                continue
            parser = Parser(lang)
            tree = parser.parse(bytes(content, "utf-8"))
            self._extract_imports(tree.root_node, rel, now)
        self.conn.commit()
        self.conn.close()

    def print_stats(self):
        print(f"\n✅ Code Indexer Complete:")
        print(f"   📄 Files: {self.stats['files']}  🔤 Symbols: {self.stats['symbols']}")
        print(f"   🔗 Edges: {self.stats['edges']}  🌐 Routes: {self.stats['routes']}")
        print(f"   ⏭️  Unchanged: {self.stats['skipped']}")


def main():
    p = argparse.ArgumentParser(description="Ag-Kit Code Indexer")
    p.add_argument("--root", default=".", help="Project root")
    p.add_argument("--db", default=str(DEFAULT_DB))
    p.add_argument("--full", action="store_true", help="Force full re-index")
    p.add_argument("--max-files", type=int, default=500)
    args = p.parse_args()

    root = Path(args.root).resolve()
    print(f"🔍 Indexing: {root.name}...")
    idx = CodeIndexer(root, Path(args.db))
    idx.index(force_full=args.full, max_files=args.max_files)
    idx.print_stats()

if __name__ == "__main__":
    main()
