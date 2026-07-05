#!/usr/bin/env python3
"""
Knowledge Graph Schema for ag-kit VFS.

Adapted from Understand-Anything's schema.ts (Lum1104/Understand-Anything).
Provides:
  - Typed node/edge definitions (21 node types, 35 edge types)
  - LLM alias system for robust normalization
  - 4-tier validation pipeline (sanitize → autofix → validate → fatal)
  - Fingerprint-based change detection
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# ──────────────────────────────────────────────
# Node Types (21 total: 5 code + 8 non-code + 3 domain + 5 knowledge)
# ──────────────────────────────────────────────
class NodeType(str, Enum):
    # Code
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    CONCEPT = "concept"
    # Non-code
    CONFIG = "config"
    DOCUMENT = "document"
    SERVICE = "service"
    TABLE = "table"
    ENDPOINT = "endpoint"
    PIPELINE = "pipeline"
    SCHEMA = "schema"
    RESOURCE = "resource"
    # Domain
    DOMAIN = "domain"
    FLOW = "flow"
    STEP = "step"
    # Knowledge
    ARTICLE = "article"
    ENTITY = "entity"
    TOPIC = "topic"
    CLAIM = "claim"
    SOURCE = "source"

# ──────────────────────────────────────────────
# Edge Types (35 total across 8 categories)
# ──────────────────────────────────────────────
class EdgeType(str, Enum):
    # Structural
    IMPORTS = "imports"
    EXPORTS = "exports"
    CONTAINS = "contains"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    # Behavioral
    CALLS = "calls"
    SUBSCRIBES = "subscribes"
    PUBLISHES = "publishes"
    MIDDLEWARE = "middleware"
    # Data flow
    READS_FROM = "reads_from"
    WRITES_TO = "writes_to"
    TRANSFORMS = "transforms"
    VALIDATES = "validates"
    # Dependencies
    DEPENDS_ON = "depends_on"
    TESTED_BY = "tested_by"
    CONFIGURES = "configures"
    # Semantic
    RELATED = "related"
    SIMILAR_TO = "similar_to"
    # Infrastructure
    DEPLOYS = "deploys"
    SERVES = "serves"
    PROVISIONS = "provisions"
    TRIGGERS = "triggers"
    # Schema/Data
    MIGRATES = "migrates"
    DOCUMENTS = "documents"
    ROUTES = "routes"
    DEFINES_SCHEMA = "defines_schema"
    # Domain
    CONTAINS_FLOW = "contains_flow"
    FLOW_STEP = "flow_step"
    CROSS_DOMAIN = "cross_domain"
    # Knowledge
    CITES = "cites"
    CONTRADICTS = "contradicts"
    BUILDS_ON = "builds_on"
    EXEMPLIFIES = "exemplifies"
    CATEGORIZED_UNDER = "categorized_under"
    AUTHORED_BY = "authored_by"


class Complexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class Direction(str, Enum):
    FORWARD = "forward"
    BACKWARD = "backward"
    BIDIRECTIONAL = "bidirectional"


# ──────────────────────────────────────────────
# LLM Alias System — auto-normalize fuzzy LLM output
# Learned from Understand-Anything's NODE_TYPE_ALIASES
# ──────────────────────────────────────────────
NODE_TYPE_ALIASES: dict[str, str] = {
    "func": "function", "fn": "function", "method": "function",
    "interface": "class", "struct": "class",
    "mod": "module", "pkg": "module", "package": "module",
    "container": "service", "deployment": "service", "pod": "service",
    "doc": "document", "readme": "document", "docs": "document",
    "job": "pipeline", "ci": "pipeline",
    "route": "endpoint", "api": "endpoint", "query": "endpoint", "mutation": "endpoint",
    "setting": "config", "env": "config", "configuration": "config",
    "infra": "resource", "infrastructure": "resource", "terraform": "resource",
    "migration": "table", "database": "table", "db": "table", "view": "table",
    "proto": "schema", "protobuf": "schema", "definition": "schema", "typedef": "schema",
    "business_domain": "domain",
    "business_flow": "flow", "business_process": "flow",
    "task": "step", "business_step": "step",
    "note": "article", "page": "article", "wiki_page": "article",
    "person": "entity", "actor": "entity", "organization": "entity",
    "tag": "topic", "category": "topic", "theme": "topic",
    "assertion": "claim", "decision": "claim", "thesis": "claim",
    "reference": "source", "raw": "source", "paper": "source",
}

EDGE_TYPE_ALIASES: dict[str, str] = {
    "extends": "inherits", "invokes": "calls", "invoke": "calls",
    "uses": "depends_on", "requires": "depends_on",
    "relates_to": "related", "related_to": "related",
    "similar": "similar_to",
    "import": "imports", "export": "exports",
    "contain": "contains", "publish": "publishes", "subscribe": "subscribes",
    "describes": "documents", "documented_by": "documents",
    "creates": "provisions", "exposes": "serves", "listens": "serves",
    "deploys_to": "deploys", "migrates_to": "migrates",
    "routes_to": "routes", "triggers_on": "triggers", "fires": "triggers",
    "defines": "defines_schema",
    "has_flow": "contains_flow", "next_step": "flow_step",
    "interacts_with": "cross_domain",
    "references": "cites", "cites_source": "cites",
    "conflicts_with": "contradicts", "disagrees_with": "contradicts",
    "refines": "builds_on", "elaborates": "builds_on",
    "illustrates": "exemplifies", "instance_of": "exemplifies", "example_of": "exemplifies",
    "belongs_to": "categorized_under", "tagged_with": "categorized_under",
    "written_by": "authored_by", "created_by": "authored_by",
}

COMPLEXITY_ALIASES: dict[str, str] = {
    "low": "simple", "easy": "simple",
    "medium": "moderate", "intermediate": "moderate",
    "high": "complex", "hard": "complex", "difficult": "complex",
}

DIRECTION_ALIASES: dict[str, str] = {
    "to": "forward", "outbound": "forward",
    "from": "backward", "inbound": "backward",
    "both": "bidirectional", "mutual": "bidirectional",
}


# ──────────────────────────────────────────────
# Data Classes — Graph primitives
# ──────────────────────────────────────────────
@dataclass
class GraphNode:
    id: str
    type: str  # NodeType value
    name: str
    summary: str
    tags: list[str] = field(default_factory=list)
    complexity: str = "moderate"
    file_path: Optional[str] = None
    line_range: Optional[tuple[int, int]] = None
    language_notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d = {k: v for k, v in asdict(self).items() if v is not None}
        return d


@dataclass
class GraphEdge:
    source: str
    target: str
    type: str  # EdgeType value
    direction: str = "forward"
    weight: float = 0.5
    description: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if d["description"] is None:
            del d["description"]
        return d


@dataclass
class ProjectMeta:
    name: str
    languages: list[str]
    frameworks: list[str]
    description: str
    analyzed_at: str
    git_commit_hash: str = ""


@dataclass
class KnowledgeGraph:
    version: str = "1.0.0"
    project: Optional[ProjectMeta] = None
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    layers: list[dict[str, Any]] = field(default_factory=list)
    tour: list[dict[str, Any]] = field(default_factory=list)


# ──────────────────────────────────────────────
# Fingerprint — change detection (from UA)
# ──────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class FunctionFingerprint:
    name: str
    params: tuple[str, ...]
    return_type: Optional[str] = None
    exported: bool = False
    line_count: int = 0


@dataclass(frozen=True, slots=True)
class ClassFingerprint:
    name: str
    methods: tuple[str, ...]
    properties: tuple[str, ...]
    exported: bool = False
    line_count: int = 0


@dataclass
class FileFingerprint:
    file_path: str
    content_hash: str
    functions: list[FunctionFingerprint] = field(default_factory=list)
    classes: list[ClassFingerprint] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    total_lines: int = 0
    has_structural_analysis: bool = False


class ChangeLevel(str, Enum):
    NONE = "NONE"
    COSMETIC = "COSMETIC"
    STRUCTURAL = "STRUCTURAL"


def content_hash(content: str) -> str:
    """SHA-256 content hash."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compare_fingerprints(old_fp: FileFingerprint, new_fp: FileFingerprint) -> tuple[ChangeLevel, list[str]]:
    """Compare two file fingerprints. Returns (change_level, details)."""
    if old_fp.content_hash == new_fp.content_hash:
        return ChangeLevel.NONE, []

    if not old_fp.has_structural_analysis or not new_fp.has_structural_analysis:
        return ChangeLevel.STRUCTURAL, ["no structural analysis — conservative"]

    details: list[str] = []

    old_func_names = {f.name for f in old_fp.functions}
    new_func_names = {f.name for f in new_fp.functions}
    for name in new_func_names - old_func_names:
        details.append(f"new function: {name}")
    for name in old_func_names - new_func_names:
        details.append(f"removed function: {name}")

    old_class_names = {c.name for c in old_fp.classes}
    new_class_names = {c.name for c in new_fp.classes}
    for name in new_class_names - old_class_names:
        details.append(f"new class: {name}")
    for name in old_class_names - new_class_names:
        details.append(f"removed class: {name}")

    if sorted(old_fp.imports) != sorted(new_fp.imports):
        details.append("imports changed")
    if sorted(old_fp.exports) != sorted(new_fp.exports):
        details.append("exports changed")

    if details:
        return ChangeLevel.STRUCTURAL, details
    return ChangeLevel.COSMETIC, ["internal logic changed (no structural impact)"]


# ──────────────────────────────────────────────
# Validation Pipeline — 4-tier self-healing (from UA)
# ──────────────────────────────────────────────
@dataclass
class GraphIssue:
    level: str  # "auto-corrected" | "dropped" | "fatal"
    category: str
    message: str
    path: Optional[str] = None


class ValidationResult:
    def __init__(self, success: bool, data: Optional[dict] = None,
                 issues: Optional[list[GraphIssue]] = None, fatal: Optional[str] = None):
        self.success = success
        self.data = data
        self.issues = issues or []
        self.fatal = fatal


def _normalize_alias(value: str, alias_map: dict[str, str]) -> str:
    """Normalize a value using alias map."""
    return alias_map.get(value.lower(), value.lower())


def _get_valid_values(enum_class: type[Enum]) -> set[str]:
    return {e.value for e in enum_class}


# Tier 1: Sanitize — null→empty, lowercase enums
def sanitize_graph(data: dict[str, Any]) -> dict[str, Any]:
    result = dict(data)
    if data.get("tour") is None:
        result["tour"] = []
    if data.get("layers") is None:
        result["layers"] = []

    if isinstance(data.get("nodes"), list):
        result["nodes"] = []
        for node in data["nodes"]:
            if not isinstance(node, dict):
                continue
            n = dict(node)
            for opt_field in ("file_path", "filePath", "line_range", "lineRange", "language_notes", "languageNotes"):
                if n.get(opt_field) is None:
                    n.pop(opt_field, None)
            if isinstance(n.get("type"), str):
                n["type"] = n["type"].lower()
            if isinstance(n.get("complexity"), str):
                n["complexity"] = n["complexity"].lower()
            result["nodes"].append(n)

    if isinstance(data.get("edges"), list):
        result["edges"] = []
        for edge in data["edges"]:
            if not isinstance(edge, dict):
                continue
            e = dict(edge)
            if e.get("description") is None:
                e.pop("description", None)
            if isinstance(e.get("type"), str):
                e["type"] = e["type"].lower()
            if isinstance(e.get("direction"), str):
                e["direction"] = e["direction"].lower()
            result["edges"].append(e)

    return result


# Tier 2: Auto-fix — defaults, alias mapping, weight clamping
def autofix_graph(data: dict[str, Any]) -> tuple[dict[str, Any], list[GraphIssue]]:
    issues: list[GraphIssue] = []
    result = dict(data)
    valid_node_types = _get_valid_values(NodeType)
    valid_edge_types = _get_valid_values(EdgeType)
    valid_complexities = _get_valid_values(Complexity)
    valid_directions = _get_valid_values(Direction)

    if isinstance(data.get("nodes"), list):
        fixed_nodes = []
        for i, node in enumerate(data["nodes"]):
            if not isinstance(node, dict):
                continue
            n = dict(node)
            name = n.get("name", n.get("id", f"index {i}"))

            # Fix type via alias
            raw_type = str(n.get("type", ""))
            if raw_type and raw_type not in valid_node_types:
                resolved = _normalize_alias(raw_type, NODE_TYPE_ALIASES)
                if resolved in valid_node_types:
                    issues.append(GraphIssue("auto-corrected", "alias",
                                             f'nodes[{i}] ("{name}"): type "{raw_type}" → "{resolved}"',
                                             f"nodes[{i}].type"))
                    n["type"] = resolved
                else:
                    n["type"] = "file"
                    issues.append(GraphIssue("auto-corrected", "missing-field",
                                             f'nodes[{i}] ("{name}"): unknown type "{raw_type}" → "file"',
                                             f"nodes[{i}].type"))
            elif not raw_type:
                n["type"] = "file"
                issues.append(GraphIssue("auto-corrected", "missing-field",
                                         f'nodes[{i}] ("{name}"): missing type → "file"',
                                         f"nodes[{i}].type"))

            # Fix complexity
            raw_cx = str(n.get("complexity", ""))
            if raw_cx and raw_cx not in valid_complexities:
                resolved = _normalize_alias(raw_cx, COMPLEXITY_ALIASES)
                if resolved in valid_complexities:
                    n["complexity"] = resolved
                    issues.append(GraphIssue("auto-corrected", "alias",
                                             f'nodes[{i}] ("{name}"): complexity "{raw_cx}" → "{resolved}"',
                                             f"nodes[{i}].complexity"))
                else:
                    n["complexity"] = "moderate"
            elif not raw_cx:
                n["complexity"] = "moderate"

            # Fix tags
            if not isinstance(n.get("tags"), list):
                n["tags"] = []
                issues.append(GraphIssue("auto-corrected", "missing-field",
                                         f'nodes[{i}] ("{name}"): missing tags → []',
                                         f"nodes[{i}].tags"))

            # Fix summary
            if not n.get("summary"):
                n["summary"] = str(n.get("name", "No summary"))
                issues.append(GraphIssue("auto-corrected", "missing-field",
                                         f'nodes[{i}] ("{name}"): missing summary → name',
                                         f"nodes[{i}].summary"))

            fixed_nodes.append(n)
        result["nodes"] = fixed_nodes

    if isinstance(data.get("edges"), list):
        fixed_edges = []
        for i, edge in enumerate(data["edges"]):
            if not isinstance(edge, dict):
                continue
            e = dict(edge)

            # Fix type via alias
            raw_type = str(e.get("type", ""))
            if raw_type and raw_type not in valid_edge_types:
                resolved = _normalize_alias(raw_type, EDGE_TYPE_ALIASES)
                if resolved in valid_edge_types:
                    e["type"] = resolved
                    issues.append(GraphIssue("auto-corrected", "alias",
                                             f'edges[{i}]: type "{raw_type}" → "{resolved}"',
                                             f"edges[{i}].type"))
                else:
                    e["type"] = "depends_on"
                    issues.append(GraphIssue("auto-corrected", "missing-field",
                                             f'edges[{i}]: unknown type "{raw_type}" → "depends_on"',
                                             f"edges[{i}].type"))
            elif not raw_type:
                e["type"] = "depends_on"

            # Fix direction
            raw_dir = str(e.get("direction", ""))
            if raw_dir and raw_dir not in valid_directions:
                resolved = _normalize_alias(raw_dir, DIRECTION_ALIASES)
                if resolved in valid_directions:
                    e["direction"] = resolved
                else:
                    e["direction"] = "forward"
            elif not raw_dir:
                e["direction"] = "forward"

            # Fix weight
            w = e.get("weight")
            if w is None:
                e["weight"] = 0.5
            elif isinstance(w, str):
                try:
                    e["weight"] = float(w)
                except ValueError:
                    e["weight"] = 0.5
            if isinstance(e["weight"], (int, float)):
                e["weight"] = max(0.0, min(1.0, float(e["weight"])))

            fixed_edges.append(e)
        result["edges"] = fixed_edges

    return result, issues


# Tier 3 + 4: Validate nodes/edges individually, check referential integrity
def validate_graph(data: Any) -> ValidationResult:
    """Full 4-tier validation pipeline."""
    if not isinstance(data, dict):
        return ValidationResult(False, fatal="Invalid input: not a dict")

    # Tier 1
    sanitized = sanitize_graph(data)

    # Tier 2
    fixed, issues = autofix_graph(sanitized)

    # Tier 4: Fatal — malformed top-level collections
    for collection in ("nodes", "edges", "layers", "tour"):
        val = fixed.get(collection)
        if val is not None and not isinstance(val, list):
            fatal = f'"{collection}" must be an array'
            issues.append(GraphIssue("fatal", "invalid-collection", fatal, collection))
            return ValidationResult(False, issues=issues, fatal=fatal)

    # Tier 4: Missing project metadata
    if not isinstance(fixed.get("project"), dict):
        return ValidationResult(False, issues=issues, fatal="Missing project metadata")

    # Tier 3: Validate nodes individually, drop broken
    valid_node_types = _get_valid_values(NodeType)
    valid_nodes = []
    nodes = fixed.get("nodes", [])
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue
        if not node.get("id") or not node.get("type"):
            name_hint = node.get("name", f"index {i}")
            issues.append(GraphIssue("dropped", "invalid-node",
                                     f'nodes[{i}] ("{name_hint}"): missing id or type — removed',
                                     f"nodes[{i}]"))
            continue
        if node["type"] not in valid_node_types:
            issues.append(GraphIssue("dropped", "invalid-node",
                                     f'nodes[{i}] ("{node.get("name", "?")}") invalid type "{node["type"]}" — removed',
                                     f"nodes[{i}]"))
            continue
        valid_nodes.append(node)

    if not valid_nodes:
        return ValidationResult(False, issues=issues, fatal="No valid nodes found")

    # Tier 3: Validate edges + referential integrity
    node_ids = {n["id"] for n in valid_nodes}
    valid_edge_types = _get_valid_values(EdgeType)
    valid_edges = []
    edges = fixed.get("edges", [])
    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            continue
        if edge.get("type") not in valid_edge_types:
            issues.append(GraphIssue("dropped", "invalid-edge",
                                     f'edges[{i}]: invalid type "{edge.get("type")}" — removed',
                                     f"edges[{i}]"))
            continue
        if edge.get("source") not in node_ids:
            issues.append(GraphIssue("dropped", "invalid-reference",
                                     f'edges[{i}]: source "{edge.get("source")}" not in nodes — removed',
                                     f"edges[{i}].source"))
            continue
        if edge.get("target") not in node_ids:
            issues.append(GraphIssue("dropped", "invalid-reference",
                                     f'edges[{i}]: target "{edge.get("target")}" not in nodes — removed',
                                     f"edges[{i}].target"))
            continue
        valid_edges.append(edge)

    graph = {
        "version": fixed.get("version", "1.0.0"),
        "project": fixed["project"],
        "nodes": valid_nodes,
        "edges": valid_edges,
        "layers": fixed.get("layers", []),
        "tour": fixed.get("tour", []),
    }

    return ValidationResult(True, data=graph, issues=issues)


# ──────────────────────────────────────────────
# I/O helpers
# ──────────────────────────────────────────────
def save_graph(graph: KnowledgeGraph, path: str | Path) -> None:
    """Save a knowledge graph to JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    raw: dict[str, Any] = {
        "version": graph.version,
        "project": asdict(graph.project) if graph.project else None,
        "nodes": [n.to_dict() for n in graph.nodes],
        "edges": [e.to_dict() for e in graph.edges],
        "layers": graph.layers,
        "tour": graph.tour,
    }
    p.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")


def load_graph(path: str | Path) -> ValidationResult:
    """Load and validate a knowledge graph from JSON file."""
    p = Path(path)
    if not p.exists():
        return ValidationResult(False, fatal=f"File not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return ValidationResult(False, fatal=f"Invalid JSON: {exc}")
    return validate_graph(data)


# ──────────────────────────────────────────────
# CLI entrypoint — validate a graph file
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python schema.py <graph.json>")
        print("  Validates a knowledge graph file and prints issues.")
        sys.exit(1)

    result = load_graph(sys.argv[1])
    if result.success:
        n_nodes = len(result.data.get("nodes", []))
        n_edges = len(result.data.get("edges", []))
        print(f"✅ Valid graph: {n_nodes} nodes, {n_edges} edges")
    else:
        print(f"❌ Invalid graph: {result.fatal}")

    for issue in result.issues:
        icon = {"auto-corrected": "🔧", "dropped": "⚠️", "fatal": "❌"}.get(issue.level, "?")
        print(f"  {icon} [{issue.category}] {issue.message}")
