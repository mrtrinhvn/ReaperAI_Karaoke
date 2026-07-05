#!/usr/bin/env python3
"""
Knowledge Graph Builder for ag-kit VFS.

Extends vfs_parser.py with graph-building capabilities.
Scans a codebase directory and produces a KnowledgeGraph JSON.

Architecture adapted from:
  - Understand-Anything's GraphBuilder (graph-builder.ts)
  - Semble's file_walker + chunking pipeline

Usage:
  python graph_builder.py <project_dir>                     # scan & print JSON
  python graph_builder.py <project_dir> -o graph.json       # scan & save to file
  python graph_builder.py <project_dir> --validate graph.json  # validate existing
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schema import (
    ChangeLevel,
    FileFingerprint,
    FunctionFingerprint,
    ClassFingerprint,
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    ProjectMeta,
    compare_fingerprints,
    content_hash,
    save_graph,
    validate_graph,
)

# Try importing doc_parsers for non-code enrichment
try:
    from doc_parsers import parse_document, is_parseable
    _HAS_DOC_PARSERS = True
except ImportError:
    _HAS_DOC_PARSERS = False

# ──────────────────────────────────────────────
# Language detection — from Semble's files.py (350+ extensions)
# Keeping the most common ones for ag-kit
# ──────────────────────────────────────────────
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python", ".pyi": "python", ".pyw": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "tsx", ".mts": "typescript", ".cts": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin", ".kts": "kotlin",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp",
    ".cs": "csharp",
    ".swift": "swift",
    ".dart": "dart",
    ".lua": "lua",
    ".sh": "bash", ".bash": "bash", ".zsh": "zsh",
    ".sql": "sql",
    ".graphql": "graphql", ".gql": "graphql",
    ".proto": "proto",
    ".html": "html", ".htm": "html",
    ".css": "css", ".scss": "scss", ".less": "less",
    ".json": "json", ".json5": "json5",
    ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".md": "markdown", ".mdx": "markdown",
    ".dockerfile": "dockerfile",
    ".tf": "terraform", ".tfvars": "terraform",
    ".vue": "vue", ".svelte": "svelte",
    ".prisma": "prisma",
    ".env": "env",
}

# File category detection — from UA's file-analyzer agent
DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".txt"}
CONFIG_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".xml", ".env", ".ini", ".cfg", ".properties"}
INFRA_PATTERNS = {"Dockerfile", "docker-compose", "Makefile", "Jenkinsfile", "Vagrantfile"}
DATA_EXTENSIONS = {".sql", ".graphql", ".gql", ".proto", ".prisma", ".csv"}
SCRIPT_EXTENSIONS = {".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd"}
MARKUP_EXTENSIONS = {".html", ".htm", ".css", ".scss", ".less"}

# Directories to skip during scanning
SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    ".env", "dist", "build", ".next", ".nuxt", "coverage", ".tox",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".agent", ".understand-anything",
    "vendor", "target", "bin", "obj",
}


def detect_language(file_path: str) -> str | None:
    """Detect language from file extension."""
    ext = Path(file_path).suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext)


def detect_file_category(file_path: str) -> str:
    """Categorize file: code, config, docs, infra, data, script, markup."""
    p = Path(file_path)
    name = p.name
    ext = p.suffix.lower()

    # Infra detection by filename
    for pattern in INFRA_PATTERNS:
        if name.startswith(pattern):
            return "infra"
    if ".github/workflows" in file_path or ".gitlab-ci" in name or ".circleci" in file_path:
        return "infra"
    if ext in {".tf", ".tfvars"}:
        return "infra"

    # Category by extension
    if ext in DOC_EXTENSIONS and name != "LICENSE":
        return "docs"
    if ext in CONFIG_EXTENSIONS:
        return "config"
    if ext in DATA_EXTENSIONS:
        return "data"
    if ext in SCRIPT_EXTENSIONS:
        return "script"
    if ext in MARKUP_EXTENSIONS:
        return "markup"

    return "code"


# ──────────────────────────────────────────────
# Node type mapping — from UA's file-analyzer agent
# ──────────────────────────────────────────────
CATEGORY_TO_NODE_TYPE: dict[str, str] = {
    "code": "file",
    "config": "config",
    "docs": "document",
    "infra": "service",
    "data": "table",
    "script": "file",
    "markup": "file",
}


def _get_git_hash(project_dir: Path) -> str:
    """Get current git commit hash, empty string if not a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=project_dir, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def _get_project_name(project_dir: Path) -> str:
    """Detect project name from package.json, pyproject.toml, or dir name."""
    pkg_json = project_dir / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            if "name" in data:
                return data["name"]
        except Exception:
            pass

    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        try:
            text = pyproject.read_text(encoding="utf-8")
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("name") and "=" in line:
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass

    return project_dir.name


def scan_files(project_dir: Path) -> list[dict[str, str | int]]:
    """Walk the project directory and collect file metadata.

    Prefers `git ls-files` when available (follows .gitignore).
    """
    files: list[dict[str, str | int]] = []

    # Try git ls-files first
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True, text=True, cwd=project_dir, timeout=10,
        )
        if result.returncode == 0:
            for rel_path in result.stdout.strip().splitlines():
                if not rel_path:
                    continue
                abs_path = project_dir / rel_path
                if not abs_path.is_file():
                    continue
                lang = detect_language(rel_path)
                if lang is None:
                    continue
                try:
                    line_count = abs_path.read_text(encoding="utf-8", errors="replace").count("\n") + 1
                except OSError:
                    continue
                files.append({
                    "path": rel_path,
                    "language": lang,
                    "sizeLines": line_count,
                    "fileCategory": detect_file_category(rel_path),
                })
            return files
    except Exception:
        pass

    # Fallback: recursive walk
    for root, dirs, filenames in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in filenames:
            abs_path = Path(root) / fname
            rel_path = str(abs_path.relative_to(project_dir))
            lang = detect_language(rel_path)
            if lang is None:
                continue
            try:
                line_count = abs_path.read_text(encoding="utf-8", errors="replace").count("\n") + 1
            except OSError:
                continue
            files.append({
                "path": rel_path,
                "language": lang,
                "sizeLines": line_count,
                "fileCategory": detect_file_category(rel_path),
            })

    files.sort(key=lambda f: f["path"])
    return files


class GraphBuilder:
    """Builds a KnowledgeGraph from a project directory.

    Adapted from UA's GraphBuilder class.
    """

    def __init__(self, project_dir: str | Path):
        self.project_dir = Path(project_dir).resolve()
        self.nodes: list[GraphNode] = []
        self.edges: list[GraphEdge] = []
        self._node_ids: set[str] = set()
        self._edge_keys: set[str] = set()
        self._languages: set[str] = set()

    def _add_node(self, node: GraphNode) -> bool:
        """Add a node if its ID is unique. Returns True if added."""
        if node.id in self._node_ids:
            return False
        self._node_ids.add(node.id)
        self.nodes.append(node)
        return True

    def _add_edge(self, edge: GraphEdge) -> bool:
        """Add an edge if its key is unique. Returns True if added."""
        key = f"{edge.type}|{edge.source}|{edge.target}"
        if key in self._edge_keys:
            return False
        self._edge_keys.add(key)
        self.edges.append(edge)
        return True

    def add_file(self, file_info: dict[str, Any], analysis: dict | None = None) -> str:
        """Add a file node and optional function/class sub-nodes.

        Returns the file node ID.
        """
        rel_path = file_info["path"]
        lang = file_info.get("language", "unknown")
        category = file_info.get("fileCategory", "code")
        line_count = file_info.get("sizeLines", 0)

        if lang != "unknown":
            self._languages.add(lang)

        # Determine node type from category
        node_type = CATEGORY_TO_NODE_TYPE.get(category, "file")
        node_id = f"{node_type}:{rel_path}"

        # Determine complexity from line count
        if line_count < 50:
            complexity = "simple"
        elif line_count < 200:
            complexity = "moderate"
        else:
            complexity = "complex"

        file_node = GraphNode(
            id=node_id,
            type=node_type,
            name=Path(rel_path).name,
            summary=f"{Path(rel_path).name} ({lang}, {line_count} lines)",
            tags=[category, lang],
            complexity=complexity,
            file_path=rel_path,
        )
        self._add_node(file_node)

        # Add function/class sub-nodes from VFS analysis
        if analysis and category == "code":
            for sym in analysis.get("symbols", []):
                sym_type = sym.get("type", "").lower()
                sym_name = sym.get("name", "")
                start = sym.get("start", 0)
                end = sym.get("end", 0)

                if sym_type in ("function", "method"):
                    child_id = f"function:{rel_path}:{sym_name}"
                    child_node = GraphNode(
                        id=child_id,
                        type="function",
                        name=sym_name,
                        summary=sym.get("signature", sym_name),
                        tags=[],
                        complexity="simple" if (end - start) < 20 else "moderate",
                        file_path=rel_path,
                        line_range=(start, end),
                    )
                    if self._add_node(child_node):
                        self._add_edge(GraphEdge(
                            source=node_id, target=child_id,
                            type="contains", direction="forward", weight=1.0,
                        ))

                elif sym_type in ("class", "interface"):
                    child_id = f"class:{rel_path}:{sym_name}"
                    child_node = GraphNode(
                        id=child_id,
                        type="class",
                        name=sym_name,
                        summary=sym.get("signature", sym_name),
                        tags=[],
                        complexity="moderate" if (end - start) < 100 else "complex",
                        file_path=rel_path,
                        line_range=(start, end),
                    )
                    if self._add_node(child_node):
                        self._add_edge(GraphEdge(
                            source=node_id, target=child_id,
                            type="contains", direction="forward", weight=1.0,
                        ))

        # Enrich non-code files with doc_parsers (Phase 5)
        elif _HAS_DOC_PARSERS and category != "code":
            abs_path = self.project_dir / rel_path
            if is_parseable(abs_path):
                doc_result = parse_document(abs_path)
                if doc_result:
                    # Enrich summary
                    if doc_result.summary:
                        file_node.summary = doc_result.summary

                    # Add parsed definitions as sub-nodes (SQL, Proto)
                    for defn in doc_result.definitions:
                        defn_name = defn.get("name", "")
                        defn_type_raw = defn.get("type", "UNKNOWN").lower()
                        defn_line = defn.get("line", 0)

                        # Map definition type to node type
                        type_map = {
                            "table": "table", "view": "table",
                            "function": "function", "procedure": "function",
                            "index": "resource", "trigger": "resource",
                            "message": "schema", "service": "service",
                            "rpc": "endpoint", "enum": "schema",
                        }
                        mapped_type = type_map.get(defn_type_raw, "resource")
                        child_id = f"{mapped_type}:{rel_path}:{defn_name}"
                        child_node = GraphNode(
                            id=child_id,
                            type=mapped_type,
                            name=defn_name,
                            summary=f"{defn_type_raw.upper()} {defn_name}",
                            tags=[defn_type_raw],
                            file_path=rel_path,
                            line_range=(defn_line, defn_line),
                        )
                        if self._add_node(child_node):
                            self._add_edge(GraphEdge(
                                source=node_id, target=child_id,
                                type="defines", direction="forward", weight=1.0,
                            ))

                    # Add heading structure for docs
                    if doc_result.headings and category == "docs":
                        file_node.tags.extend(["documented"])
                        h1s = [h["text"] for h in doc_result.headings if h["level"] == 1]
                        if h1s:
                            file_node.summary = h1s[0]

                    # Add variable info for .env files
                    if doc_result.variables:
                        file_node.tags.extend(["env-config"])
                        file_node.summary = f"{len(doc_result.variables)} env vars"

                    # Add Docker info
                    if doc_result.base_images:
                        file_node.tags.extend(["container"])
                        file_node.summary = doc_result.summary

        return node_id

    def add_import_edge(self, from_file: str, to_file: str) -> None:
        """Add an import edge between two files."""
        from_type = "file"
        to_type = "file"
        # Detect node type from existing nodes
        for n in self.nodes:
            if n.file_path == from_file:
                from_type = n.type
                break
        for n in self.nodes:
            if n.file_path == to_file:
                to_type = n.type
                break

        self._add_edge(GraphEdge(
            source=f"{from_type}:{from_file}",
            target=f"{to_type}:{to_file}",
            type="imports",
            direction="forward",
            weight=0.7,
        ))

    def build(self) -> KnowledgeGraph:
        """Assemble the final KnowledgeGraph with auto-detected layers."""
        project_meta = ProjectMeta(
            name=_get_project_name(self.project_dir),
            languages=sorted(self._languages),
            frameworks=[],
            description="",
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            git_commit_hash=_get_git_hash(self.project_dir),
        )

        # GAP 7 fix: Auto-detect architectural layers from path patterns
        layers = self._detect_layers()

        return KnowledgeGraph(
            version="1.0.0",
            project=project_meta,
            nodes=list(self.nodes),
            edges=list(self.edges),
            layers=layers,
        )

    def _detect_layers(self) -> list[dict]:
        """Auto-detect architectural layers from file paths.

        GAP 7 fix: Adapted from UA's layer concepts.
        Uses heuristic path patterns instead of LLM.
        """
        # Layer definitions: (id, name, description, path_patterns)
        layer_defs = [
            ("frontend", "Frontend / UI",
             "Client-side code, components, pages, styles",
             ["frontend/", "client/", "src/components/", "src/pages/",
              "src/app/", "src/views/", "public/", "styles/", "css/"]),
            ("backend", "Backend / Server",
             "Server-side logic, API handlers, business logic",
             ["server/", "server-node/", "backend/", "api/", "src/api/",
              "src/server/", "src/services/", "services/", "handlers/"]),
            ("config", "Configuration",
             "Project configuration, environment, and build settings",
             ["config/", ".env", "webpack", "vite", "tsconfig",
              "package.json", "next.config", "tailwind", "eslint"]),
            ("infra", "Infrastructure / DevOps",
             "Docker, CI/CD, deployment, and infrastructure",
             ["docker", "Dockerfile", ".github/", ".gitlab",
              "deploy/", "k8s/", "terraform/", "infra/"]),
            ("docs", "Documentation",
             "Project documentation, guides, and specs",
             ["docs/", "doc/", "README", "CONTRIBUTING",
              "CHANGELOG", ".md"]),
            ("tests", "Testing",
             "Test files, fixtures, and test utilities",
             ["test/", "tests/", "__tests__/", "spec/",
              ".test.", ".spec.", "test_", "_test."]),
            ("data", "Data / Models",
             "Database schemas, migrations, data models",
             ["models/", "schemas/", "migrations/", "prisma/",
              "db/", "database/", "sql/"]),
            ("tools", "Tools / Scripts",
             "Build scripts, utility tools, automation",
             ["tools/", "scripts/", "bin/", "utils/", "helpers/"]),
        ]

        layers = []
        for layer_id, name, description, patterns in layer_defs:
            node_ids = []
            for node in self.nodes:
                fp = node.file_path or ""
                if any(pat in fp or fp.startswith(pat) or fp.endswith(pat) for pat in patterns):
                    node_ids.append(node.id)

            if node_ids:  # Only include layers that have nodes
                layers.append({
                    "id": layer_id,
                    "name": name,
                    "description": f"{description} ({len(node_ids)} components)",
                    "nodeIds": node_ids,
                })

        return layers


def _try_vfs_parse(file_path: Path) -> dict | None:
    """Try to get VFS analysis for a file using vfs_parser.py."""
    vfs_script = Path(__file__).parent / "vfs_parser.py"
    if not vfs_script.exists():
        return None

    try:
        result = subprocess.run(
            [sys.executable, str(vfs_script), str(file_path)],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return None

        symbols = []
        for line in result.stdout.strip().splitlines():
            if line.startswith("Line "):
                # Parse "Line 10-25 [FUNCTION]: def formatDate(..."
                parts = line.split(" ", 2)
                if len(parts) < 3:
                    continue
                line_range = parts[1].split("-")
                if len(line_range) != 2:
                    continue
                rest = parts[2]
                tag_end = rest.find("]:")
                if tag_end < 0:
                    continue
                tag = rest[1:tag_end].lower()
                sig = rest[tag_end + 3:].strip()
                # Extract name from signature
                name = sig.split("(")[0].split(" ")[-1].strip(":")

                symbols.append({
                    "type": tag,
                    "name": name,
                    "start": int(line_range[0]),
                    "end": int(line_range[1]),
                    "signature": sig,
                })
        return {"symbols": symbols} if symbols else None
    except Exception:
        return None


def build_project_graph(project_dir: str | Path) -> KnowledgeGraph:
    """Scan a project directory and build a KnowledgeGraph."""
    project_dir = Path(project_dir).resolve()
    builder = GraphBuilder(project_dir)

    print(f"Scanning {project_dir}...", file=sys.stderr)
    files = scan_files(project_dir)
    print(f"Found {len(files)} files", file=sys.stderr)

    for file_info in files:
        # Try VFS analysis for code files
        analysis = None
        if file_info["fileCategory"] == "code":
            abs_path = project_dir / file_info["path"]
            analysis = _try_vfs_parse(abs_path)

        builder.add_file(file_info, analysis)

    graph = builder.build()
    print(f"Built graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges", file=sys.stderr)
    return graph


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build a Knowledge Graph from a codebase")
    parser.add_argument("project_dir", help="Path to project directory")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument("--validate", metavar="FILE", help="Validate an existing graph file")
    parser.add_argument("--stats", action="store_true", help="Print graph statistics only")
    args = parser.parse_args()

    if args.validate:
        from schema import load_graph
        result = load_graph(args.validate)
        if result.success:
            nodes = result.data.get("nodes", [])
            edges = result.data.get("edges", [])
            print(f"✅ Valid: {len(nodes)} nodes, {len(edges)} edges")
        else:
            print(f"❌ Invalid: {result.fatal}")
        for issue in result.issues:
            icon = {"auto-corrected": "🔧", "dropped": "⚠️", "fatal": "❌"}.get(issue.level, "?")
            print(f"  {icon} [{issue.category}] {issue.message}")
        return

    graph = build_project_graph(args.project_dir)

    if args.stats:
        node_types = {}
        for n in graph.nodes:
            node_types[n.type] = node_types.get(n.type, 0) + 1
        edge_types = {}
        for e in graph.edges:
            edge_types[e.type] = edge_types.get(e.type, 0) + 1
        print(f"Project: {graph.project.name}")
        print(f"Languages: {', '.join(graph.project.languages)}")
        print(f"Nodes ({len(graph.nodes)}):")
        for t, c in sorted(node_types.items(), key=lambda x: -x[1]):
            print(f"  {t}: {c}")
        print(f"Edges ({len(graph.edges)}):")
        for t, c in sorted(edge_types.items(), key=lambda x: -x[1]):
            print(f"  {t}: {c}")
        return

    if args.output:
        save_graph(graph, args.output)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        from dataclasses import asdict
        raw = {
            "version": graph.version,
            "project": asdict(graph.project),
            "nodes": [n.to_dict() for n in graph.nodes],
            "edges": [e.to_dict() for e in graph.edges],
            "layers": graph.layers,
            "tour": graph.tour,
        }
        print(json.dumps(raw, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
