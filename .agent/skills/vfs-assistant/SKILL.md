---
name: vfs-assistant
description: "Virtual File System (VFS) for token-efficient code analysis. Knowledge Graph with 21 node types, 35 edge types, Hybrid Search (BM25+TF-IDF+RRF+Rerank), Incremental Analysis, Document Parsers, Context Builder, Impact Analyzer, and Layer Auto-Detection. All gaps from Semble + Understand-Anything audit resolved."
---

# VFS Assistant Skill v2.2 — Final

> Synthesis of [Semble](https://github.com/MinishLab/semble) + [Understand-Anything](https://github.com/Lum1104/Understand-Anything) + ag-kit. All 7 audit gaps resolved.

## Architecture: 8 Scripts, 3568 Lines, Zero External Dependencies

| # | Script | Lines | Source | Purpose |
|---|--------|-------|--------|---------|
| 1 | `vfs_parser.py` | 155 | ag-kit | Tree-sitter AST signature extraction |
| 2 | `schema.py` | 634 | UA | 21 node types, 35 edges, alias system, 4-tier validation |
| 3 | `graph_builder.py` | 660 | ag-kit+UA | Project scanner + doc parsers + **layer auto-detection** |
| 4 | `graph_search.py` | 682 | Semble | BM25+TF-IDF+RRF + **rerank + saturation + function boost + token savings** |
| 5 | `graph_incremental.py` | 492 | UA | SHA-256 fingerprint, incremental rebuild |
| 6 | `doc_parsers.py` | 412 | UA | MD/YAML/JSON/SQL/Proto/Docker/.env parsers |
| 7 | `graph_context.py` | 247 | UA | **KG→Agent bridge** (search→1-hop→prompt) |
| 8 | `graph_impact.py` | 286 | UA | **Diff→Impact→Risk** assessment |

## Resolved Gaps (7/7 ✅)

| Gap | Source | Resolution |
|-----|--------|-----------|
| Rerank Penalties | Semble `penalties.py` | Test/compat/examples demoted 0.3x |
| File Saturation | Semble `penalties.py` | Max 1 result/file, 0.5x decay |
| Function-Level Precision | Semble `chunking/core.py` | Function/class nodes get 3x name boost |
| Context Builder | UA `context-builder.ts` | `graph_context.py` — search→expand→format |
| Impact Analyzer | UA `diff-analyzer.ts` | `graph_impact.py` — blast radius + risk |
| Token Savings Stats | Semble `stats.py` | Live savings bar in search output |
| Layer Auto-Detection | UA `onboard-builder.ts` | 8 layers auto-detected from path patterns |

## CLI Commands

```bash
ag-kit brain               # Full: Index → Graph → Brain
ag-kit graph --stats       # Quick overview
ag-kit graph --full        # Force full rebuild
ag-kit graph --diff        # Show changes since last build
ag-kit search "query"      # Hybrid search + rerank + savings
ag-kit context "query"     # KG→Agent context bridge
ag-kit impact              # Diff impact analysis
```

## Search Features (v2.2)

- **Hybrid**: BM25 keyword + TF-IDF semantic + RRF fusion
- **Alpha auto-detect**: Symbol query (α=0.3) vs NL query (α=0.5)
- **Rerank penalties**: Test files ×0.3, compat dirs ×0.3, re-exports ×0.5
- **File saturation**: Max 1 chunk/file, then ×0.5 decay
- **Function-level**: Function/class nodes boosted 3× over file nodes
- **Line ranges**: Results show `L17-20` for functions/classes
- **Token savings**: Live bar showing chars saved vs full file reads

## Context Builder

```bash

## When to Activate

- Virtual File System (VFS) for token-efficient code analysis. Knowledge Graph with 21 node types, 35 edge types, Hybrid S
- Need guidance on: Architecture: 8 Scripts, 3568 Lines, Zero External Dependencies
- Need guidance on: Resolved Gaps (7/7 ✅)
- Need guidance on: CLI Commands
- Need guidance on: Search Features (v2.2)
- Writing or reviewing bash code


# Full markdown for LLM
python3 .../graph_context.py graph.json "booking flow"

# Compact for prompt injection (token-efficient)
python3 .../graph_context.py graph.json "booking flow" --compact
```

**Flow**: Query → Search top-15 → 1-hop expand → Collect layers → Format markdown/compact

## Impact Analyzer

```bash
# Auto-detect from git
python3 .../graph_impact.py graph.json

# Specify files
python3 .../graph_impact.py graph.json --files "src/a.ts,src/b.ts"
```

**Output**: Changed nodes → Affected nodes → Impacted layers → Risk level

## Layer Auto-Detection

Detects 8 architectural layers from path patterns:

| Layer | Patterns | Example |
|-------|----------|---------|
| Frontend / UI | `frontend/`, `src/components/`, `src/pages/` | 275 nodes |
| Backend / Server | `server/`, `server-node/`, `api/`, `services/` | 3341 nodes |
| Configuration | `config/`, `.env`, `tsconfig`, `package.json` | 10 nodes |
| Infrastructure | `docker`, `.github/`, `deploy/`, `terraform/` | 3 nodes |
| Documentation | `docs/`, `README`, `CHANGELOG` | 208 nodes |
| Testing | `test/`, `__tests__/`, `.test.`, `.spec.` | 469 nodes |
| Data / Models | `models/`, `schemas/`, `migrations/`, `prisma/` | 1 nodes |
| Tools / Scripts | `tools/`, `scripts/`, `bin/`, `utils/` | 1547 nodes |

## Knowledge Graph Schema

**Node Types (21):** `file`, `function`, `class`, `module`, `concept`, `config`, `document`, `service`, `table`, `endpoint`, `pipeline`, `schema`, `resource`, `domain`, `flow`, `step`, `article`, `entity`, `topic`, `claim`, `source`

**Edge Types (35):** `imports`, `exports`, `contains`, `inherits`, `implements`, `calls`, `depends_on`, `tested_by`, `configures`, `deploys`, `documents`, `defines`, and 23 more.

## Intent-Based Usage

| Intent | Command |
|--------|---------|
| Find a function | `ag-kit search "functionName"` |
| Map project | `ag-kit graph --stats` |
| Get context for AI | `ag-kit context "what I'm working on" --compact` |
| Assess change risk | `ag-kit impact --files "path/to/changed.ts"` |
| Incremental update | `ag-kit graph --diff` |
| Full rebuild | `ag-kit graph --full` |
