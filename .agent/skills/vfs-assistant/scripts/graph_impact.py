#!/usr/bin/env python3
"""
Diff/Impact Analyzer for Knowledge Graph.

GAP 5 fix: Maps changed files to graph nodes, finds 1-hop affected nodes,
computes blast radius, and auto-generates risk assessment.
Adapted from Understand-Anything's diff-analyzer.ts.

Flow: git diff → Map to nodes → Find affected components → Risk assessment

Usage:
  # Auto-detect from git
  python graph_impact.py <graph.json>

  # Specify changed files
  python graph_impact.py <graph.json> --files "src/booking.ts,src/api.ts"

  # JSON output
  python graph_impact.py <graph.json> --json
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────
# DiffContext — from UA's diff-analyzer.ts
# ──────────────────────────────────────────────
@dataclass
class DiffContext:
    """Impact analysis of changed files against the Knowledge Graph."""

    project_name: str = ""
    changed_files: list[str] = field(default_factory=list)
    changed_nodes: list[dict[str, Any]] = field(default_factory=list)
    affected_nodes: list[dict[str, Any]] = field(default_factory=list)
    impacted_edges: list[dict[str, Any]] = field(default_factory=list)
    affected_layers: list[dict[str, Any]] = field(default_factory=list)
    unmapped_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "changed_files": self.changed_files,
            "changed_node_count": len(self.changed_nodes),
            "affected_node_count": len(self.affected_nodes),
            "impacted_edge_count": len(self.impacted_edges),
            "unmapped_files": self.unmapped_files,
            "changed_nodes": [{"id": n.get("id"), "name": n.get("name"), "type": n.get("type")} for n in self.changed_nodes],
            "affected_nodes": [{"id": n.get("id"), "name": n.get("name"), "type": n.get("type")} for n in self.affected_nodes],
        }


# ──────────────────────────────────────────────
# Build Diff Context — from UA's buildDiffContext
# ──────────────────────────────────────────────
def build_diff_context(
    graph_data: dict[str, Any],
    changed_files: list[str],
) -> DiffContext:
    """Map changed files to graph nodes and compute impact.

    Adapted from UA's buildDiffContext().
    """
    project = graph_data.get("project", {})
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    layers = graph_data.get("layers", [])

    changed_node_ids: set[str] = set()
    unmapped_files: list[str] = []

    # Map changed files to node IDs
    for file_path in changed_files:
        mapped = False
        for node in nodes:
            if node.get("file_path") == file_path:
                changed_node_ids.add(node.get("id", ""))
                mapped = True
        if not mapped:
            unmapped_files.append(file_path)

    # Include "contains" children of changed file nodes
    for edge in edges:
        if edge.get("type") == "contains" and edge.get("source") in changed_node_ids:
            changed_node_ids.add(edge.get("target", ""))

    changed_nodes = [n for n in nodes if n.get("id") in changed_node_ids]

    # Find affected nodes: 1-hop neighbors (excluding already changed)
    affected_node_ids: set[str] = set()
    impacted_edges: list[dict[str, Any]] = []

    for edge in edges:
        source = edge.get("source", "")
        target = edge.get("target", "")
        source_changed = source in changed_node_ids
        target_changed = target in changed_node_ids

        if source_changed or target_changed:
            impacted_edges.append(edge)
            if source_changed and target not in changed_node_ids:
                affected_node_ids.add(target)
            if target_changed and source not in changed_node_ids:
                affected_node_ids.add(source)

    affected_nodes = [n for n in nodes if n.get("id") in affected_node_ids]

    # Find affected layers
    all_impacted_ids = changed_node_ids | affected_node_ids
    affected_layers = [
        layer for layer in layers
        if any(nid in all_impacted_ids for nid in layer.get("nodeIds", []))
    ]

    return DiffContext(
        project_name=project.get("name", ""),
        changed_files=changed_files,
        changed_nodes=changed_nodes,
        affected_nodes=affected_nodes,
        impacted_edges=impacted_edges,
        affected_layers=affected_layers,
        unmapped_files=unmapped_files,
    )


# ──────────────────────────────────────────────
# Risk Assessment — from UA's formatDiffAnalysis
# ──────────────────────────────────────────────
def format_impact_report(ctx: DiffContext) -> str:
    """Format impact analysis as structured markdown.

    Adapted from UA's formatDiffAnalysis().
    """
    lines: list[str] = []

    lines.append(f"# Impact Analysis: {ctx.project_name}")
    lines.append("")

    # Changed Components
    lines.append("## Changed Components")
    lines.append("")
    if not ctx.changed_nodes:
        lines.append("No mapped components found for changed files.")
    else:
        for node in ctx.changed_nodes:
            lines.append(f"- **{node.get('name', '')}** ({node.get('type', '')}) — {node.get('summary', '')}")
            if node.get("file_path"):
                lines.append(f"  - File: `{node['file_path']}`")
            lines.append(f"  - Complexity: {node.get('complexity', 'unknown')}")
    lines.append("")

    # Affected Components
    lines.append("## Affected Components (Downstream)")
    lines.append("")
    if not ctx.affected_nodes:
        lines.append("No downstream impact detected.")
    else:
        lines.append("These components are connected to changed code and may need attention:")
        lines.append("")
        for node in ctx.affected_nodes:
            lines.append(f"- **{node.get('name', '')}** ({node.get('type', '')}) — {node.get('summary', '')}")
    lines.append("")

    # Affected Layers
    if ctx.affected_layers:
        lines.append("## Affected Layers")
        lines.append("")
        for layer in ctx.affected_layers:
            lines.append(f"- **{layer.get('name', '')}**: {layer.get('description', '')}")
        lines.append("")

    # Impacted Relationships
    non_contains = [e for e in ctx.impacted_edges if e.get("type") != "contains"]
    if non_contains:
        lines.append("## Impacted Relationships")
        lines.append("")
        for edge in non_contains[:20]:  # cap to avoid huge output
            lines.append(f"- {edge.get('source', '')} --[{edge.get('type', '')}]--> {edge.get('target', '')}")
        lines.append("")

    # Unmapped Files
    if ctx.unmapped_files:
        lines.append("## Unmapped Files")
        lines.append("")
        lines.append("These changed files are not yet in the knowledge graph:")
        lines.append("")
        for f in ctx.unmapped_files:
            lines.append(f"- `{f}`")
        lines.append("")

    # Risk Assessment
    lines.append("## Risk Assessment")
    lines.append("")
    complex_changes = [n for n in ctx.changed_nodes if n.get("complexity") == "complex"]
    cross_layer_count = len(set(l.get("id", "") for l in ctx.affected_layers))

    risk_flags = []
    if complex_changes:
        names = ", ".join(n.get("name", "") for n in complex_changes)
        risk_flags.append(f"- 🔴 **High complexity**: {len(complex_changes)} complex component(s) changed: {names}")
    if cross_layer_count > 1:
        risk_flags.append(f"- 🟡 **Cross-layer impact**: Changes span {cross_layer_count} architectural layers")
    if len(ctx.affected_nodes) > 5:
        risk_flags.append(f"- 🟡 **Wide blast radius**: {len(ctx.affected_nodes)} components affected downstream")
    if ctx.unmapped_files:
        risk_flags.append(f"- 🟠 **New/unmapped files**: {len(ctx.unmapped_files)} files not in the knowledge graph")

    if risk_flags:
        lines.extend(risk_flags)
    else:
        lines.append("- ✅ **Low risk**: Changes are localized with limited downstream impact.")
    lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# Git Integration — auto-detect changed files
# ──────────────────────────────────────────────
def get_changed_files(project_dir: Path) -> list[str]:
    """Get list of changed files from git (staged + unstaged + untracked)."""
    try:
        # Staged + unstaged changes
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, cwd=project_dir, timeout=10,
        )
        files = set()
        if result.returncode == 0:
            files.update(f.strip() for f in result.stdout.strip().splitlines() if f.strip())

        # Also check staged changes that haven't been committed
        result2 = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True, text=True, cwd=project_dir, timeout=10,
        )
        if result2.returncode == 0:
            files.update(f.strip() for f in result2.stdout.strip().splitlines() if f.strip())

        return sorted(files)
    except Exception:
        return []


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Analyze impact of changed files on Knowledge Graph")
    parser.add_argument("graph_file", help="Path to knowledge-graph.json")
    parser.add_argument("--files", help="Comma-separated list of changed files (auto-detect from git if omitted)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    graph_path = Path(args.graph_file)
    graph_data = json.loads(graph_path.read_text(encoding="utf-8"))

    if args.files:
        changed_files = [f.strip() for f in args.files.split(",")]
    else:
        # Auto-detect from git
        project_dir = graph_path.parent.parent.parent  # .agent/brain/graph.json → project root
        changed_files = get_changed_files(project_dir)

    if not changed_files:
        print("✅ No changed files detected.")
        return

    ctx = build_diff_context(graph_data, changed_files)

    if args.json:
        print(json.dumps(ctx.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(format_impact_report(ctx))


if __name__ == "__main__":
    main()
