#!/usr/bin/env python3
"""
Context Builder for Knowledge Graph → LLM Prompt injection.

GAP 4 fix: The bridge between static Knowledge Graph and dynamic AI Agent.
Adapted from Understand-Anything's context-builder.ts.

Flow: Query → Search graph → 1-hop expand via edges → Format markdown context

Usage:
  # As library (called by agent tools)
  from graph_context import build_context, format_context_prompt
  ctx = build_context(graph_data, "booking payload format")
  prompt = format_context_prompt(ctx)

  # CLI test
  python graph_context.py <graph.json> "query"
  python graph_context.py <graph.json> "query" --max-nodes 20
  python graph_context.py <graph.json> "query" --json
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Import search engine
sys.path.insert(0, str(Path(__file__).parent))
from graph_search import GraphSearchEngine


# ──────────────────────────────────────────────
# ChatContext — from UA's context-builder.ts
# ──────────────────────────────────────────────
@dataclass
class ChatContext:
    """Context assembled from Knowledge Graph for LLM consumption."""

    project_name: str = ""
    project_description: str = ""
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    query: str = ""
    relevant_nodes: list[dict[str, Any]] = field(default_factory=list)
    relevant_edges: list[dict[str, Any]] = field(default_factory=list)
    relevant_layers: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "query": self.query,
            "languages": self.languages,
            "node_count": len(self.relevant_nodes),
            "edge_count": len(self.relevant_edges),
            "layer_count": len(self.relevant_layers),
            "nodes": self.relevant_nodes,
            "edges": self.relevant_edges,
            "layers": self.relevant_layers,
        }


# ──────────────────────────────────────────────
# Context Builder — search + 1-hop expand
# ──────────────────────────────────────────────
def build_context(
    graph_data: dict[str, Any],
    query: str,
    max_nodes: int = 15,
) -> ChatContext:
    """Build a ChatContext by searching the KG and expanding 1-hop.

    Adapted from UA's buildChatContext().
    """
    project = graph_data.get("project", {})
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    layers = graph_data.get("layers", [])

    # 1. Search for relevant nodes
    engine = GraphSearchEngine()
    engine.build_from_graph(graph_data)
    results = engine.search(query, top_k=max_nodes, mode="hybrid")

    matched_ids = {r.node_id for r in results}

    # 2. Expand to connected nodes (1-hop via edges)
    expanded_ids = set(matched_ids)
    for edge in edges:
        source = edge.get("source", "")
        target = edge.get("target", "")
        if source in matched_ids:
            expanded_ids.add(target)
        if target in matched_ids:
            expanded_ids.add(source)

    # 3. Collect node objects
    node_map = {n.get("id", ""): n for n in nodes}
    relevant_nodes = [node_map[nid] for nid in expanded_ids if nid in node_map]

    # 4. Collect edges where both endpoints are in the relevant set
    relevant_edges = [
        e for e in edges
        if e.get("source", "") in expanded_ids and e.get("target", "") in expanded_ids
    ]

    # 5. Find layers containing any relevant node
    relevant_layers = [
        layer for layer in layers
        if any(nid in expanded_ids for nid in layer.get("nodeIds", []))
    ]

    return ChatContext(
        project_name=project.get("name", ""),
        project_description=project.get("description", ""),
        languages=project.get("languages", []),
        frameworks=project.get("frameworks", []),
        query=query,
        relevant_nodes=relevant_nodes,
        relevant_edges=relevant_edges,
        relevant_layers=relevant_layers,
    )


# ──────────────────────────────────────────────
# Prompt Formatter — from UA's formatContextForPrompt
# ──────────────────────────────────────────────
def format_context_prompt(ctx: ChatContext) -> str:
    """Format ChatContext as markdown for LLM consumption.

    Adapted from UA's formatContextForPrompt().
    """
    lines: list[str] = []

    # Project header
    lines.append(f"# Project: {ctx.project_name}")
    lines.append("")
    if ctx.project_description:
        lines.append(ctx.project_description)
        lines.append("")
    lines.append(f"**Languages:** {', '.join(ctx.languages)}")
    if ctx.frameworks:
        lines.append(f"**Frameworks:** {', '.join(ctx.frameworks)}")
    lines.append("")

    # Layers section
    if ctx.relevant_layers:
        lines.append("## Relevant Layers")
        lines.append("")
        for layer in ctx.relevant_layers:
            lines.append(f"### {layer.get('name', 'Unknown')}")
            lines.append(layer.get("description", ""))
            lines.append("")

    # Nodes section
    if ctx.relevant_nodes:
        lines.append("## Code Components")
        lines.append("")
        for node in ctx.relevant_nodes:
            node_name = node.get("name", "")
            node_type = node.get("type", "")
            lines.append(f"### {node_name} ({node_type})")
            if node.get("file_path"):
                lines.append(f"- **File:** {node['file_path']}")
            lines.append(f"- **Complexity:** {node.get('complexity', 'unknown')}")
            lines.append(f"- **Summary:** {node.get('summary', '')}")
            if node.get("tags"):
                lines.append(f"- **Tags:** {', '.join(node['tags'])}")
            if node.get("line_range"):
                lr = node["line_range"]
                if isinstance(lr, (list, tuple)) and len(lr) >= 2:
                    lines.append(f"- **Lines:** {lr[0]}-{lr[1]}")
            lines.append("")

    # Edges/relationships section
    if ctx.relevant_edges:
        # Filter out 'contains' edges for cleaner output
        non_contains = [e for e in ctx.relevant_edges if e.get("type") != "contains"]
        if non_contains:
            node_name_map = {n.get("id", ""): n.get("name", "") for n in ctx.relevant_nodes}
            lines.append("## Relationships")
            lines.append("")
            for edge in non_contains:
                src = node_name_map.get(edge.get("source", ""), edge.get("source", ""))
                tgt = node_name_map.get(edge.get("target", ""), edge.get("target", ""))
                desc = f": {edge['description']}" if edge.get("description") else ""
                lines.append(f"- {src} --[{edge.get('type', '')}]--> {tgt}{desc}")
            lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# Compact Context — token-efficient version
# ──────────────────────────────────────────────
def format_compact_context(ctx: ChatContext) -> str:
    """Compact format for injection into agent system prompts.

    Much shorter than full markdown — saves tokens.
    """
    lines = [f"[KG Context: {ctx.project_name} | {len(ctx.relevant_nodes)} nodes relevant]"]

    for node in ctx.relevant_nodes[:10]:  # cap at 10 for token efficiency
        fp = node.get("file_path", "")
        name = node.get("name", "")
        ntype = node.get("type", "")
        summary = node.get("summary", "")[:60]
        lr = node.get("line_range", "")
        lr_str = f" L{lr[0]}-{lr[1]}" if isinstance(lr, (list, tuple)) and len(lr) >= 2 else ""
        lines.append(f"  {ntype}:{name} | {fp}{lr_str} | {summary}")

    # Add key relationships
    non_contains = [e for e in ctx.relevant_edges if e.get("type") != "contains"]
    if non_contains:
        lines.append(f"  [{len(non_contains)} relationships: {', '.join(set(e.get('type','') for e in non_contains))}]")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build context from Knowledge Graph")
    parser.add_argument("graph_file", help="Path to knowledge-graph.json")
    parser.add_argument("query", help="Context query")
    parser.add_argument("--max-nodes", type=int, default=15, help="Max nodes to collect (default: 15)")
    parser.add_argument("--compact", action="store_true", help="Compact format (token-efficient)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    graph_data = json.loads(Path(args.graph_file).read_text(encoding="utf-8"))
    ctx = build_context(graph_data, args.query, max_nodes=args.max_nodes)

    if args.json:
        print(json.dumps(ctx.to_dict(), indent=2, ensure_ascii=False))
    elif args.compact:
        print(format_compact_context(ctx))
    else:
        print(format_context_prompt(ctx))


if __name__ == "__main__":
    main()
