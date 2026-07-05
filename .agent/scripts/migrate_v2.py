#!/usr/bin/env python3
"""
migrate_v2.py — Ag-Kit v2.0 Migration Script

Upgrades existing ag-kit projects to v2.0 architecture:
  1. Copies new/updated scripts (code_indexer.py, memory_mcp_server.py, memory_tool.py, brain_builder.py)
  2. Creates new SQLite tables (symbols, struct_edges, routes) — ADDITIVE, no data loss
  3. Runs code_indexer on the project (first full index)
  4. Rebuilds brain with symbol-aware summary
  5. Updates .version marker

Safe to run multiple times (idempotent).

Usage:
  python3 migrate_v2.py                        # Migrate current directory
  python3 migrate_v2.py --all                   # Migrate ALL registered projects
  python3 migrate_v2.py --project /path/to/proj # Migrate specific project
  python3 migrate_v2.py --dry-run               # Preview without changes
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime

TEMPLATE_DIR = Path(__file__).parent.parent  # .agent/ of the template
# Resolve ag-kit root: this script is at template/.agent/scripts/migrate_v2.py
# so ag-kit root = ../../.. from this file
AGKIT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # ag-kit repo root
GLOBAL_REGISTRY = Path.home() / ".config" / "ag-kit" / "projects.json"
TARGET_VERSION = "2.0.0"

# Files that need to be updated in each project
SCRIPTS_TO_COPY = [
    "scripts/code_indexer.py",
    "scripts/memory_mcp_server.py",
    "scripts/memory_tool.py",
    "scripts/brain_builder.py",
]


def log(msg, dry=False):
    prefix = "[DRY-RUN] " if dry else ""
    print(f"  {prefix}{msg}")


def get_registered_projects() -> list[Path]:
    """Get all project roots from global registry."""
    if not GLOBAL_REGISTRY.exists():
        return []
    try:
        data = json.loads(GLOBAL_REGISTRY.read_text())
        roots = set()
        for info in data.values():
            root = Path(info.get("root", ""))
            if root.exists() and (root / ".agent").exists():
                roots.add(root)
        return sorted(roots)
    except Exception:
        return []


def get_project_version(proj_root: Path) -> str:
    vfile = proj_root / ".agent" / ".version"
    if vfile.exists():
        return vfile.read_text().strip()
    return "0.0.0"


def copy_scripts(proj_root: Path, dry=False):
    """Copy updated scripts from ag-kit template to project."""
    template_agent = AGKIT_ROOT / "template" / ".agent"
    proj_agent = proj_root / ".agent"
    copied = 0

    for rel in SCRIPTS_TO_COPY:
        src = template_agent / rel
        dst = proj_agent / rel

        if not src.exists():
            log(f"⚠️  Source not found: {src}", dry)
            continue

        # Check if file changed
        if dst.exists():
            if src.read_bytes() == dst.read_bytes():
                continue  # identical, skip

        if not dry:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        log(f"📄 {rel}", dry)
        copied += 1

    return copied


def ensure_schema(proj_root: Path, dry=False):
    """Create new tables in existing graph.db (additive migration)."""
    db_path = proj_root / ".agent" / "memory" / "graph.db"
    if not db_path.exists():
        log("ℹ️  No graph.db yet — will be created on first use", dry)
        return

    if dry:
        log("🗄️  Would add symbols/struct_edges/routes tables to graph.db", dry)
        return

    import sqlite3
    conn = sqlite3.connect(str(db_path))

    # Check current state
    existing = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}

    new_tables = []
    if "symbols" not in existing:
        new_tables.append("symbols")
    if "struct_edges" not in existing:
        new_tables.append("struct_edges")
    if "routes" not in existing:
        new_tables.append("routes")

    if not new_tables:
        log("🗄️  Tables already exist — schema OK")
        conn.close()
        return

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

    # Also ensure memory nodes have temporal columns (from v1.6.3+)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(nodes)").fetchall()]
    for col, typedef in [("valid_from", "TEXT"), ("ended", "TEXT"), ("tags", "TEXT")]:
        if col not in cols:
            conn.execute(f"ALTER TABLE nodes ADD COLUMN {col} {typedef}")

    conn.commit()
    conn.close()
    log(f"🗄️  Added tables: {', '.join(new_tables)}")


def run_code_indexer(proj_root: Path, dry=False):
    """Run code_indexer.py on the project for first-time symbol indexing."""
    indexer = proj_root / ".agent" / "scripts" / "code_indexer.py"
    if not indexer.exists():
        log("⚠️  code_indexer.py not found — skipping index", dry)
        return

    if dry:
        log("🔍 Would run code_indexer.py --full", dry)
        return

    log("🔍 Running code indexer (first-time full scan)...")
    result = subprocess.run(
        [sys.executable, str(indexer), "--root", str(proj_root), "--full"],
        capture_output=True, text=True, timeout=120, cwd=str(proj_root)
    )
    for line in result.stdout.strip().splitlines():
        log(f"   {line}")
    if result.returncode != 0 and result.stderr:
        log(f"   ⚠️ stderr: {result.stderr[:200]}")


def rebuild_brain(proj_root: Path, dry=False):
    """Rebuild brain summary with new symbol-aware builder."""
    builder = proj_root / ".agent" / "scripts" / "brain_builder.py"
    if not builder.exists():
        return

    if dry:
        log("🧠 Would rebuild brain summary", dry)
        return

    log("🧠 Rebuilding brain...")
    result = subprocess.run(
        [sys.executable, str(builder), "--root", str(proj_root), "--update"],
        capture_output=True, text=True, timeout=30, cwd=str(proj_root)
    )
    for line in result.stdout.strip().splitlines():
        log(f"   {line}")


def update_version(proj_root: Path, dry=False):
    vfile = proj_root / ".agent" / ".version"
    if dry:
        log(f"📌 Would update .version to {TARGET_VERSION}", dry)
        return
    vfile.write_text(TARGET_VERSION)
    log(f"📌 Version → {TARGET_VERSION}")


def migrate_project(proj_root: Path, dry=False):
    """Full migration pipeline for a single project."""
    proj_root = proj_root.resolve()
    agent_dir = proj_root / ".agent"

    if not agent_dir.exists():
        print(f"❌ No .agent/ in {proj_root} — not an ag-kit project")
        return False

    current_ver = get_project_version(proj_root)
    print(f"\n{'='*60}")
    print(f"🚀 Migrating: {proj_root.name}  (v{current_ver} → v{TARGET_VERSION})")
    print(f"   Path: {proj_root}")
    print(f"{'='*60}")

    if current_ver >= TARGET_VERSION:
        print(f"  ✅ Already at v{current_ver} — skipping")
        return True

    # Step 1: Copy updated scripts
    copied = copy_scripts(proj_root, dry)
    log(f"Scripts updated: {copied} files")

    # Step 2: Schema migration (additive)
    ensure_schema(proj_root, dry)

    # Step 3: Run code indexer
    run_code_indexer(proj_root, dry)

    # Step 4: Rebuild brain
    rebuild_brain(proj_root, dry)

    # Step 5: Version bump
    update_version(proj_root, dry)

    print(f"  ✅ Migration complete!")
    return True


def main():
    p = argparse.ArgumentParser(
        description="Ag-Kit v2.0 Migration — Upgrade existing projects"
    )
    p.add_argument("--all", action="store_true",
                    help="Migrate ALL registered projects")
    p.add_argument("--project", "-p", type=str,
                    help="Migrate a specific project directory")
    p.add_argument("--dry-run", action="store_true",
                    help="Preview changes without applying")
    args = p.parse_args()

    print(f"🔄 Ag-Kit Migration v{TARGET_VERSION}")
    print(f"   Template: {AGKIT_ROOT / 'template' / '.agent'}")
    if args.dry_run:
        print(f"   Mode: DRY-RUN (no changes will be made)\n")

    if args.all:
        projects = get_registered_projects()
        if not projects:
            print("❌ No registered projects found in ~/.config/ag-kit/projects.json")
            return
        print(f"📋 Found {len(projects)} projects to migrate")
        success = 0
        for proj in projects:
            try:
                if migrate_project(proj, dry=args.dry_run):
                    success += 1
            except Exception as e:
                print(f"  ❌ Error: {e}")
        print(f"\n{'='*60}")
        print(f"✅ Done: {success}/{len(projects)} projects migrated")

    elif args.project:
        migrate_project(Path(args.project), dry=args.dry_run)

    else:
        # Default: migrate current directory
        migrate_project(Path.cwd(), dry=args.dry_run)


if __name__ == "__main__":
    main()
