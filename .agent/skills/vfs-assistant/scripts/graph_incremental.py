#!/usr/bin/env python3
"""
Incremental Analysis Engine for ag-kit Knowledge Graph.

Phase 3 of the VFS v2.0 upgrade:
  - File fingerprinting (SHA-256 content hash + structural signature)
  - Change detection: NONE / COSMETIC / STRUCTURAL levels
  - Incremental graph rebuild: only re-analyze changed files
  - Fingerprint cache stored alongside knowledge-graph.json

Adapted from Understand-Anything's fingerprint.ts + file-analyzer.md

Usage:
  python graph_incremental.py <project_dir>                 # incremental rebuild
  python graph_incremental.py <project_dir> --full          # force full rebuild
  python graph_incremental.py <project_dir> --status        # show change summary
  python graph_incremental.py <project_dir> --diff          # show detailed changes
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Import from siblings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schema import ChangeLevel, FileFingerprint, FunctionFingerprint, ClassFingerprint
from graph_builder import (
    GraphBuilder,
    build_project_graph,
    scan_files,
    save_graph,
    _get_git_hash,
    _get_project_name,
    _try_vfs_parse,
    CATEGORY_TO_NODE_TYPE,
)


# ──────────────────────────────────────────────
# Fingerprint Store — persistent cache
# ──────────────────────────────────────────────
FINGERPRINT_FILE = "fingerprints.json"


@dataclass
class FingerprintStore:
    """Persistent store for file fingerprints. Enables incremental analysis."""

    fingerprints: dict[str, FileFingerprint] = field(default_factory=dict)
    last_git_hash: str = ""
    last_analyzed_at: str = ""

    def get(self, file_path: str) -> FileFingerprint | None:
        return self.fingerprints.get(file_path)

    def set(self, file_path: str, fp: FileFingerprint) -> None:
        self.fingerprints[file_path] = fp

    def remove(self, file_path: str) -> None:
        self.fingerprints.pop(file_path, None)

    def save(self, path: Path) -> None:
        """Serialize to JSON."""
        data = {
            "last_git_hash": self.last_git_hash,
            "last_analyzed_at": self.last_analyzed_at,
            "fingerprints": {},
        }
        for fp_path, fp in self.fingerprints.items():
            data["fingerprints"][fp_path] = {
                "file_path": fp.file_path,
                "content_hash": fp.content_hash,
                "total_lines": fp.total_lines,
                "has_structural_analysis": fp.has_structural_analysis,
                "imports": list(fp.imports),
                "exports": list(fp.exports),
                "functions": [
                    {"name": f.name, "params": list(f.params),
                     "return_type": f.return_type, "exported": f.exported,
                     "line_count": f.line_count}
                    for f in fp.functions
                ],
                "classes": [
                    {"name": c.name, "methods": list(c.methods),
                     "properties": list(c.properties), "exported": c.exported,
                     "line_count": c.line_count}
                    for c in fp.classes
                ],
            }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> FingerprintStore:
        """Deserialize from JSON."""
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()

        store = cls(
            last_git_hash=data.get("last_git_hash", ""),
            last_analyzed_at=data.get("last_analyzed_at", ""),
        )
        for fp_path, fp_data in data.get("fingerprints", {}).items():
            functions = [
                FunctionFingerprint(
                    name=f["name"],
                    params=tuple(f.get("params", [])),
                    return_type=f.get("return_type"),
                    exported=f.get("exported", False),
                    line_count=f.get("line_count", 0),
                )
                for f in fp_data.get("functions", [])
            ]
            classes = [
                ClassFingerprint(
                    name=c["name"],
                    methods=tuple(c.get("methods", [])),
                    properties=tuple(c.get("properties", [])),
                    exported=c.get("exported", False),
                    line_count=c.get("line_count", 0),
                )
                for c in fp_data.get("classes", [])
            ]
            store.fingerprints[fp_path] = FileFingerprint(
                file_path=fp_data.get("file_path", fp_path),
                content_hash=fp_data.get("content_hash", ""),
                functions=functions,
                classes=classes,
                imports=fp_data.get("imports", []),
                exports=fp_data.get("exports", []),
                total_lines=fp_data.get("total_lines", 0),
                has_structural_analysis=fp_data.get("has_structural_analysis", False),
            )
        return store


# ──────────────────────────────────────────────
# Fingerprint Builder — from VFS analysis
# ──────────────────────────────────────────────
def build_fingerprint(file_path: str, project_dir: Path) -> FileFingerprint:
    """Build a fingerprint for a single file."""
    abs_path = project_dir / file_path
    try:
        content = abs_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return FileFingerprint(
            file_path=file_path,
            content_hash="",
            total_lines=0,
        )

    content_hash_val = hashlib.sha256(content.encode("utf-8")).hexdigest()
    total_lines = content.count("\n") + 1

    # Try VFS structural analysis
    analysis = _try_vfs_parse(abs_path)
    functions: list[FunctionFingerprint] = []
    classes: list[ClassFingerprint] = []
    has_structural = False

    if analysis and analysis.get("symbols"):
        has_structural = True
        for sym in analysis["symbols"]:
            sym_type = sym.get("type", "").lower()
            sym_name = sym.get("name", "")
            start = sym.get("start", 0)
            end = sym.get("end", 0)
            line_count = max(0, end - start)

            if sym_type in ("function", "method"):
                functions.append(FunctionFingerprint(
                    name=sym_name,
                    params=(),  # VFS doesn't extract params yet
                    line_count=line_count,
                ))
            elif sym_type in ("class", "interface"):
                classes.append(ClassFingerprint(
                    name=sym_name,
                    methods=(),
                    properties=(),
                    line_count=line_count,
                ))

    return FileFingerprint(
        file_path=file_path,
        content_hash=content_hash_val,
        functions=functions,
        classes=classes,
        total_lines=total_lines,
        has_structural_analysis=has_structural,
    )


# ──────────────────────────────────────────────
# Change Detection — from UA's fingerprint comparison
# ──────────────────────────────────────────────
@dataclass
class FileChange:
    file_path: str
    change_type: str  # "added", "removed", "modified"
    change_level: str  # ChangeLevel value
    details: list[str] = field(default_factory=list)


def detect_changes(
    old_store: FingerprintStore,
    current_files: list[dict[str, Any]],
    project_dir: Path,
) -> list[FileChange]:
    """Compare old fingerprints with current files to detect changes."""
    changes: list[FileChange] = []
    current_paths = {f["path"] for f in current_files}
    old_paths = set(old_store.fingerprints.keys())

    # New files
    for f in current_files:
        if f["path"] not in old_paths:
            changes.append(FileChange(
                file_path=f["path"],
                change_type="added",
                change_level=ChangeLevel.STRUCTURAL.value,
                details=["new file"],
            ))

    # Removed files
    for path in old_paths - current_paths:
        changes.append(FileChange(
            file_path=path,
            change_type="removed",
            change_level=ChangeLevel.STRUCTURAL.value,
            details=["file deleted"],
        ))

    # Modified files (check content hash)
    for f in current_files:
        if f["path"] not in old_paths:
            continue
        old_fp = old_store.get(f["path"])
        if not old_fp:
            continue

        abs_path = project_dir / f["path"]
        try:
            content = abs_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        new_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if new_hash == old_fp.content_hash:
            continue  # No change

        # Content changed — determine level
        new_fp = build_fingerprint(f["path"], project_dir)

        # Compare structural elements
        old_func_names = {fn.name for fn in old_fp.functions}
        new_func_names = {fn.name for fn in new_fp.functions}
        old_class_names = {c.name for c in old_fp.classes}
        new_class_names = {c.name for c in new_fp.classes}

        details: list[str] = []
        for name in new_func_names - old_func_names:
            details.append(f"+ function: {name}")
        for name in old_func_names - new_func_names:
            details.append(f"- function: {name}")
        for name in new_class_names - old_class_names:
            details.append(f"+ class: {name}")
        for name in old_class_names - new_class_names:
            details.append(f"- class: {name}")

        if details:
            level = ChangeLevel.STRUCTURAL.value
        elif not old_fp.has_structural_analysis or not new_fp.has_structural_analysis:
            level = ChangeLevel.STRUCTURAL.value
            details.append("no structural analysis available")
        else:
            level = ChangeLevel.COSMETIC.value
            details.append("internal logic changed")

        changes.append(FileChange(
            file_path=f["path"],
            change_type="modified",
            change_level=level,
            details=details,
        ))

    return changes


# ──────────────────────────────────────────────
# Incremental Graph Rebuild
# ──────────────────────────────────────────────
def incremental_rebuild(
    project_dir: str | Path,
    force_full: bool = False,
) -> dict[str, Any]:
    """Incrementally rebuild the knowledge graph.

    Returns stats dict with rebuild info.
    """
    project_dir = Path(project_dir).resolve()
    brain_dir = project_dir / ".agent" / "brain"
    brain_dir.mkdir(parents=True, exist_ok=True)

    graph_path = brain_dir / "knowledge-graph.json"
    fp_path = brain_dir / FINGERPRINT_FILE
    start_time = time.time()

    # Load existing fingerprints
    old_store = FingerprintStore.load(fp_path) if not force_full else FingerprintStore()

    # Scan current files
    print("📂 Scanning project files...", file=sys.stderr)
    current_files = scan_files(project_dir)

    # Detect changes
    changes = detect_changes(old_store, current_files, project_dir)

    structural_changes = [c for c in changes if c.change_level == ChangeLevel.STRUCTURAL.value]
    cosmetic_changes = [c for c in changes if c.change_level == ChangeLevel.COSMETIC.value]
    total_changed = len(changes)
    total_files = len(current_files)

    print(f"📊 {total_files} files total, {total_changed} changed "
          f"({len(structural_changes)} structural, {len(cosmetic_changes)} cosmetic)",
          file=sys.stderr)

    if total_changed == 0 and graph_path.exists() and not force_full:
        print("✅ No changes detected. Knowledge Graph is up to date.", file=sys.stderr)
        elapsed = time.time() - start_time
        return {
            "status": "up_to_date",
            "total_files": total_files,
            "changed": 0,
            "elapsed_seconds": round(elapsed, 2),
        }

    # Decide: full rebuild or incremental
    change_ratio = total_changed / max(total_files, 1)
    do_full = force_full or change_ratio > 0.3 or not graph_path.exists()

    if do_full:
        reason = "forced" if force_full else "new graph" if not graph_path.exists() else f"{change_ratio:.0%} files changed"
        print(f"🔄 Full rebuild ({reason})...", file=sys.stderr)
        graph = build_project_graph(project_dir)
        save_graph(graph, graph_path)
    else:
        # Incremental: load existing graph, only update changed nodes
        print(f"⚡ Incremental update ({total_changed} files)...", file=sys.stderr)
        try:
            existing_data = json.loads(graph_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            print("⚠️  Existing graph corrupt, doing full rebuild...", file=sys.stderr)
            graph = build_project_graph(project_dir)
            save_graph(graph, graph_path)
            existing_data = None

        if existing_data:
            # Remove nodes for deleted/modified files
            changed_paths = {c.file_path for c in changes}
            removed_paths = {c.file_path for c in changes if c.change_type == "removed"}

            # Filter out affected nodes
            kept_nodes = []
            removed_ids = set()
            for node in existing_data.get("nodes", []):
                node_fp = node.get("file_path", "")
                if node_fp in changed_paths:
                    removed_ids.add(node.get("id", ""))
                else:
                    kept_nodes.append(node)

            # Filter out affected edges
            kept_edges = [
                e for e in existing_data.get("edges", [])
                if e.get("source") not in removed_ids and e.get("target") not in removed_ids
            ]

            # Re-analyze changed files (not removed ones)
            builder = GraphBuilder(project_dir)
            builder.nodes = []  # fresh for changed files
            builder.edges = []

            for f in current_files:
                if f["path"] in changed_paths and f["path"] not in removed_paths:
                    analysis = None
                    if f.get("fileCategory") == "code":
                        abs_path = project_dir / f["path"]
                        analysis = _try_vfs_parse(abs_path)
                    builder.add_file(f, analysis)

            # Merge
            from schema import GraphNode, GraphEdge
            existing_data["nodes"] = kept_nodes + [n.to_dict() for n in builder.nodes]
            existing_data["edges"] = kept_edges + [e.to_dict() for e in builder.edges]
            existing_data["project"]["analyzed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            existing_data["project"]["git_commit_hash"] = _get_git_hash(project_dir)

            graph_path.write_text(
                json.dumps(existing_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"✅ Updated: {len(existing_data['nodes'])} nodes, "
                  f"{len(existing_data['edges'])} edges", file=sys.stderr)

    # Update fingerprint store
    new_store = FingerprintStore(
        last_git_hash=_get_git_hash(project_dir),
        last_analyzed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    for f in current_files:
        fp = build_fingerprint(f["path"], project_dir)
        new_store.set(f["path"], fp)
    new_store.save(fp_path)

    elapsed = time.time() - start_time
    print(f"⏱️  Completed in {elapsed:.1f}s", file=sys.stderr)

    return {
        "status": "rebuilt" if do_full else "incremental",
        "total_files": total_files,
        "changed": total_changed,
        "structural": len(structural_changes),
        "cosmetic": len(cosmetic_changes),
        "elapsed_seconds": round(elapsed, 2),
    }


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Incremental Knowledge Graph rebuild")
    parser.add_argument("project_dir", help="Path to project directory")
    parser.add_argument("--full", action="store_true", help="Force full rebuild")
    parser.add_argument("--status", action="store_true", help="Show change summary only")
    parser.add_argument("--diff", action="store_true", help="Show detailed changes")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()

    if args.status or args.diff:
        fp_path = project_dir / ".agent" / "brain" / FINGERPRINT_FILE
        old_store = FingerprintStore.load(fp_path)
        current_files = scan_files(project_dir)
        changes = detect_changes(old_store, current_files, project_dir)

        if not changes:
            print("✅ No changes since last analysis.")
            return

        structural = [c for c in changes if c.change_level == ChangeLevel.STRUCTURAL.value]
        cosmetic = [c for c in changes if c.change_level == ChangeLevel.COSMETIC.value]

        print(f"📊 {len(changes)} changes detected:")
        print(f"   🔴 Structural: {len(structural)}")
        print(f"   🟡 Cosmetic: {len(cosmetic)}")

        if args.diff:
            print()
            for c in changes:
                icon = {"added": "🟢", "removed": "🔴", "modified": "🟡"}.get(c.change_type, "?")
                level_icon = "🔴" if c.change_level == ChangeLevel.STRUCTURAL.value else "🟡"
                print(f"  {icon} [{c.change_type}] {c.file_path} ({level_icon} {c.change_level})")
                if c.details:
                    for detail in c.details:
                        print(f"      → {detail}")
        return

    result = incremental_rebuild(args.project_dir, force_full=args.full)
    if result["status"] == "up_to_date":
        print(f"\n✅ Knowledge Graph is current ({result['total_files']} files, {result['elapsed_seconds']}s)")
    else:
        print(f"\n✅ {result['status'].title()}: {result['changed']}/{result['total_files']} files "
              f"({result.get('structural', 0)} structural, {result.get('cosmetic', 0)} cosmetic) "
              f"in {result['elapsed_seconds']}s")


if __name__ == "__main__":
    main()
