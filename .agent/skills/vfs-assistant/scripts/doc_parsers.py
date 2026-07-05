#!/usr/bin/env python3
"""
Document Parsers for Non-Code Files.

Phase 5 of VFS v2.0:
  - Markdown: extract headings, TODOs, code blocks, links
  - YAML/JSON: extract keys, structure depth, references
  - Dockerfile: extract base image, stages, exposed ports
  - .env: extract variable names (NOT values — security)
  - SQL: extract table/view/function definitions

Purpose: Enrich Knowledge Graph nodes with structured metadata
from non-code files. These parsers extract lightweight signatures
without needing tree-sitter or AST.

Usage:
  # Directly
  from doc_parsers import parse_document

  result = parse_document("/path/to/README.md")
  # Returns: {"type": "markdown", "headings": [...], "todos": [...], ...}

  # CLI test
  python doc_parsers.py <file_path>
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────
# Result Type
# ──────────────────────────────────────────────
@dataclass
class DocParseResult:
    """Structured metadata extracted from a non-code file."""

    doc_type: str = ""
    headings: list[dict[str, Any]] = field(default_factory=list)  # [{level, text, line}]
    todos: list[dict[str, Any]] = field(default_factory=list)     # [{text, line, done}]
    code_blocks: list[dict[str, Any]] = field(default_factory=list)  # [{language, line_start, line_count}]
    links: list[dict[str, Any]] = field(default_factory=list)     # [{text, url, line}]
    keys: list[str] = field(default_factory=list)                 # Top-level keys (YAML/JSON)
    definitions: list[dict[str, Any]] = field(default_factory=list)  # [{type, name, line}]
    variables: list[str] = field(default_factory=list)            # Env variable names
    stages: list[str] = field(default_factory=list)               # Docker stages
    base_images: list[str] = field(default_factory=list)          # Docker FROM images
    ports: list[int] = field(default_factory=list)                # Exposed ports
    summary: str = ""                                              # Auto-generated one-liner

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"doc_type": self.doc_type}
        if self.headings:
            d["headings"] = self.headings
        if self.todos:
            d["todos"] = self.todos
        if self.code_blocks:
            d["code_blocks"] = self.code_blocks
        if self.links:
            d["links"] = self.links
        if self.keys:
            d["keys"] = self.keys
        if self.definitions:
            d["definitions"] = self.definitions
        if self.variables:
            d["variables"] = self.variables
        if self.stages:
            d["stages"] = self.stages
        if self.base_images:
            d["base_images"] = self.base_images
        if self.ports:
            d["ports"] = self.ports
        if self.summary:
            d["summary"] = self.summary
        return d


# ──────────────────────────────────────────────
# Markdown Parser
# ──────────────────────────────────────────────
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_TODO_RE = re.compile(r"^[\s]*[-*]\s+\[([ xX])\]\s+(.+)$", re.MULTILINE)
_CODE_BLOCK_START_RE = re.compile(r"^```(\w*)$", re.MULTILINE)
_CODE_BLOCK_END_RE = re.compile(r"^```$", re.MULTILINE)
_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


def parse_markdown(content: str) -> DocParseResult:
    """Extract structure from Markdown files."""
    result = DocParseResult(doc_type="markdown")
    lines = content.split("\n")

    # Headings
    for match in _HEADING_RE.finditer(content):
        level = len(match.group(1))
        text = match.group(2).strip()
        line = content[:match.start()].count("\n") + 1
        result.headings.append({"level": level, "text": text, "line": line})

    # TODOs
    for match in _TODO_RE.finditer(content):
        done = match.group(1).lower() == "x"
        text = match.group(2).strip()
        line = content[:match.start()].count("\n") + 1
        result.todos.append({"text": text, "line": line, "done": done})

    # Code blocks
    in_code = False
    code_lang = ""
    code_start = 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not in_code and stripped.startswith("```"):
            in_code = True
            code_lang = stripped[3:].strip()
            code_start = i
        elif in_code and stripped == "```":
            result.code_blocks.append({
                "language": code_lang or "unknown",
                "line_start": code_start,
                "line_count": i - code_start - 1,
            })
            in_code = False

    # Links (first 50 to avoid huge docs)
    for match in list(_LINK_RE.finditer(content))[:50]:
        text = match.group(1)
        url = match.group(2)
        line = content[:match.start()].count("\n") + 1
        result.links.append({"text": text, "url": url, "line": line})

    # Summary: first heading or first non-empty line
    if result.headings:
        result.summary = result.headings[0]["text"]
    else:
        for line in lines[:5]:
            if line.strip():
                result.summary = line.strip()[:100]
                break

    return result


# ──────────────────────────────────────────────
# YAML Parser (lightweight, no pyyaml needed)
# ──────────────────────────────────────────────
_YAML_KEY_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_.-]*):", re.MULTILINE)
_YAML_NESTED_RE = re.compile(r"^(\s+)([a-zA-Z_][a-zA-Z0-9_.-]*):", re.MULTILINE)


def parse_yaml(content: str) -> DocParseResult:
    """Extract top-level keys and structure from YAML files."""
    result = DocParseResult(doc_type="yaml")

    # Top-level keys (no indentation)
    for match in _YAML_KEY_RE.finditer(content):
        key = match.group(1)
        if key not in result.keys:
            result.keys.append(key)

    # Count nesting depth
    max_depth = 0
    for match in _YAML_NESTED_RE.finditer(content):
        depth = len(match.group(1)) // 2  # assume 2-space indent
        max_depth = max(max_depth, depth)

    result.summary = f"YAML config with {len(result.keys)} top-level keys, depth={max_depth+1}"
    return result


# ──────────────────────────────────────────────
# JSON Parser
# ──────────────────────────────────────────────
def parse_json_file(content: str) -> DocParseResult:
    """Extract top-level keys from JSON files."""
    result = DocParseResult(doc_type="json")

    try:
        data = json.loads(content)
        if isinstance(data, dict):
            result.keys = list(data.keys())[:50]  # cap at 50
            result.summary = f"JSON object with {len(data)} keys"
        elif isinstance(data, list):
            result.summary = f"JSON array with {len(data)} items"
            if data and isinstance(data[0], dict):
                result.keys = list(data[0].keys())[:20]
                result.summary += f", item keys: {', '.join(result.keys[:5])}"
    except json.JSONDecodeError:
        result.summary = "Invalid JSON"

    return result


# ──────────────────────────────────────────────
# Dockerfile Parser
# ──────────────────────────────────────────────
_FROM_RE = re.compile(r"^\s*FROM\s+(\S+)(?:\s+[Aa][Ss]\s+(\S+))?", re.MULTILINE)
_EXPOSE_RE = re.compile(r"^\s*EXPOSE\s+(\d+)", re.MULTILINE)


def parse_dockerfile(content: str) -> DocParseResult:
    """Extract FROM images, stages, and ports from Dockerfiles."""
    result = DocParseResult(doc_type="dockerfile")

    for match in _FROM_RE.finditer(content):
        image = match.group(1)
        stage = match.group(2)
        result.base_images.append(image)
        if stage:
            result.stages.append(stage)

    for match in _EXPOSE_RE.finditer(content):
        try:
            result.ports.append(int(match.group(1)))
        except ValueError:
            pass

    parts = []
    if result.base_images:
        parts.append(f"FROM {result.base_images[0]}")
    if result.stages:
        parts.append(f"{len(result.stages)} stages")
    if result.ports:
        parts.append(f"ports: {','.join(str(p) for p in result.ports)}")
    result.summary = " | ".join(parts) if parts else "Dockerfile"

    return result


# ──────────────────────────────────────────────
# .env Parser (SECURE: names only, NO values)
# ──────────────────────────────────────────────
_ENV_VAR_RE = re.compile(r"^([A-Z][A-Z0-9_]*)=", re.MULTILINE)


def parse_env(content: str) -> DocParseResult:
    """Extract variable names from .env files. Values are NEVER stored."""
    result = DocParseResult(doc_type="env")

    for match in _ENV_VAR_RE.finditer(content):
        name = match.group(1)
        if name not in result.variables:
            result.variables.append(name)

    result.summary = f"Environment config: {len(result.variables)} variables"
    return result


# ──────────────────────────────────────────────
# SQL Parser
# ──────────────────────────────────────────────
_SQL_CREATE_RE = re.compile(
    r"^\s*CREATE\s+(?:OR\s+REPLACE\s+)?"
    r"(TABLE|VIEW|FUNCTION|PROCEDURE|INDEX|TRIGGER|TYPE)\s+"
    r"(?:IF\s+NOT\s+EXISTS\s+)?"
    r"[`\"]?(\w+(?:\.\w+)*)[`\"]?",
    re.MULTILINE | re.IGNORECASE,
)
_SQL_ALTER_RE = re.compile(
    r"^\s*ALTER\s+(TABLE|VIEW)\s+[`\"]?(\w+(?:\.\w+)*)[`\"]?",
    re.MULTILINE | re.IGNORECASE,
)


def parse_sql(content: str) -> DocParseResult:
    """Extract CREATE/ALTER definitions from SQL files."""
    result = DocParseResult(doc_type="sql")

    for match in _SQL_CREATE_RE.finditer(content):
        def_type = match.group(1).upper()
        name = match.group(2)
        line = content[:match.start()].count("\n") + 1
        result.definitions.append({"type": def_type, "name": name, "line": line})

    for match in _SQL_ALTER_RE.finditer(content):
        def_type = f"ALTER_{match.group(1).upper()}"
        name = match.group(2)
        line = content[:match.start()].count("\n") + 1
        result.definitions.append({"type": def_type, "name": name, "line": line})

    if result.definitions:
        types = set(d["type"] for d in result.definitions)
        result.summary = f"SQL: {len(result.definitions)} definitions ({', '.join(sorted(types))})"
    else:
        result.summary = "SQL script"

    return result


# ──────────────────────────────────────────────
# Proto (Protobuf) Parser
# ──────────────────────────────────────────────
_PROTO_MSG_RE = re.compile(r"^\s*message\s+(\w+)\s*\{", re.MULTILINE)
_PROTO_SVC_RE = re.compile(r"^\s*service\s+(\w+)\s*\{", re.MULTILINE)
_PROTO_RPC_RE = re.compile(r"^\s*rpc\s+(\w+)\s*\(", re.MULTILINE)
_PROTO_ENUM_RE = re.compile(r"^\s*enum\s+(\w+)\s*\{", re.MULTILINE)


def parse_proto(content: str) -> DocParseResult:
    """Extract message, service, rpc, and enum definitions from .proto files."""
    result = DocParseResult(doc_type="protobuf")

    for match in _PROTO_MSG_RE.finditer(content):
        line = content[:match.start()].count("\n") + 1
        result.definitions.append({"type": "MESSAGE", "name": match.group(1), "line": line})

    for match in _PROTO_SVC_RE.finditer(content):
        line = content[:match.start()].count("\n") + 1
        result.definitions.append({"type": "SERVICE", "name": match.group(1), "line": line})

    for match in _PROTO_RPC_RE.finditer(content):
        line = content[:match.start()].count("\n") + 1
        result.definitions.append({"type": "RPC", "name": match.group(1), "line": line})

    for match in _PROTO_ENUM_RE.finditer(content):
        line = content[:match.start()].count("\n") + 1
        result.definitions.append({"type": "ENUM", "name": match.group(1), "line": line})

    msgs = sum(1 for d in result.definitions if d["type"] == "MESSAGE")
    svcs = sum(1 for d in result.definitions if d["type"] == "SERVICE")
    result.summary = f"Proto: {msgs} messages, {svcs} services"
    return result


# ──────────────────────────────────────────────
# Router — dispatch to correct parser
# ──────────────────────────────────────────────
PARSER_MAP: dict[str, type | None] = {
    ".md": None,       # -> parse_markdown
    ".mdx": None,      # -> parse_markdown
    ".yml": None,      # -> parse_yaml
    ".yaml": None,     # -> parse_yaml
    ".json": None,     # -> parse_json_file
    ".dockerfile": None,  # -> parse_dockerfile
    ".env": None,      # -> parse_env
    ".sql": None,      # -> parse_sql
    ".proto": None,    # -> parse_proto
}


def parse_document(file_path: str | Path) -> DocParseResult | None:
    """Parse a document file and return structured metadata.

    Returns None if the file type is not supported.
    """
    file_path = Path(file_path)
    ext = file_path.suffix.lower()
    name = file_path.name.lower()

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    if ext in (".md", ".mdx"):
        return parse_markdown(content)
    elif ext in (".yml", ".yaml"):
        return parse_yaml(content)
    elif ext == ".json":
        return parse_json_file(content)
    elif name.startswith("dockerfile") or name == "dockerfile":
        return parse_dockerfile(content)
    elif name.startswith(".env") or ext == ".env":
        return parse_env(content)
    elif ext == ".sql":
        return parse_sql(content)
    elif ext == ".proto":
        return parse_proto(content)
    else:
        return None


def is_parseable(file_path: str | Path) -> bool:
    """Check if a file can be parsed by the document parsers."""
    file_path = Path(file_path)
    ext = file_path.suffix.lower()
    name = file_path.name.lower()
    return (
        ext in PARSER_MAP
        or name.startswith("dockerfile")
        or name.startswith(".env")
    )


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file_path>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    result = parse_document(file_path)
    if result is None:
        print(f"⚠️  Unsupported file type: {file_path.suffix}")
        sys.exit(1)

    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
