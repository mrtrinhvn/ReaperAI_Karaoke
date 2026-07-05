#!/usr/bin/env python3
"""
memory_mcp_server.py — Ag-Kit Memory MCP Server (Option B - Vector Ready)

Exposes the Two-Tier Memory (graph.db) as native MCP tools to Antigravity AI.
AI can call these tools directly without any shell commands or bootstrap.
It uses Ollama locally to automatically generate vector embeddings for semantic search.

Tools:
  memory_save     — Save a hot node immediately (auto embeds)
  memory_search   — Search nodes by keyword + cosine similarity
  memory_link     — Create edge between two nodes
  memory_graph    — Show node connections
  memory_hot      — List hot (working memory) nodes
  memory_cold     — List cold (consolidated) nodes
  memory_consolidate — Merge old hot nodes into cold summaries
  memory_status   — DB stats (node counts, tiers)

Protocol: MCP stdio (JSON-RPC 2.0)
Run: python3 .agent/scripts/memory_mcp_server.py [--db PATH]
"""

import sys
import json
import sqlite3
import argparse
import urllib.request
import struct
import math
from pathlib import Path
from datetime import datetime, timedelta

# ─── Default DB path: resolve relative to this script ──────────────────────
DEFAULT_DB = Path(__file__).parent.parent / "memory" / "graph.db"
VALID_CATEGORIES = {"user_pref", "decision", "error", "pattern", "context", "general"}


# ─── Waterfall Embedding Engine (Ollama → Model2Vec → None) ───────────────────

_local_model_cache = None

def _try_ollama(text: str) -> bytes:
    """Tier 1: Ollama nomic-embed-text (best quality, requires Ollama running)."""
    try:
        import os
        base_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434").rstrip('/')
        req = urllib.request.Request(
            f"{base_url}/api/embed",
            json.dumps({"model": "nomic-embed-text", "input": text}).encode('utf-8')
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode('utf-8'))
            floats = data.get("embeddings", [[]])[0]
            if not floats: return None
            return struct.pack(f"{len(floats)}f", *floats)
    except Exception:
        return None

def _try_local_model(text: str) -> bytes:
    """Tier 2: Model2Vec static embeddings (CPU-only, auto-installed, ~5MB)."""
    global _local_model_cache
    try:
        from model2vec import StaticModel
        if _local_model_cache is None:
            _local_model_cache = StaticModel.from_pretrained("minishlab/potion-base-8M")
        vec = _local_model_cache.encode(text)
        return struct.pack(f"{len(vec)}f", *vec.tolist())
    except ImportError:
        try:
            import subprocess
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "model2vec"],
                capture_output=True, timeout=60
            )
            from model2vec import StaticModel
            _local_model_cache = StaticModel.from_pretrained("minishlab/potion-base-8M")
            vec = _local_model_cache.encode(text)
            return struct.pack(f"{len(vec)}f", *vec.tolist())
        except Exception:
            return None
    except Exception:
        return None

def get_embedding(text: str) -> bytes:
    """Waterfall: Ollama → Model2Vec → None (graceful degradation)."""
    emb = _try_ollama(text)
    if emb: return emb
    emb = _try_local_model(text)
    if emb: return emb
    return None


# ─── BM25 Helper ──────────────────────────────────────────────────────────────

def bm25_score(query_terms: list, doc: str, avg_dl: float, k1=1.5, b=0.75) -> float:
    """Simple single-document BM25 scoring."""
    doc_terms = doc.lower().split()
    dl = len(doc_terms)
    if dl == 0 or avg_dl == 0: return 0.0
    score = 0.0
    for term in query_terms:
        tf = doc_terms.count(term)
        if tf == 0: continue
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * dl / avg_dl)
        score += numerator / denominator
    return score

def cosine_similarity(v1: bytes, v2: bytes) -> float:
    if not v1 or not v2: return 0.0
    try:
        f1 = struct.unpack(f"{len(v1)//4}f", v1)
        f2 = struct.unpack(f"{len(v2)//4}f", v2)
        dot = sum(a * b for a, b in zip(f1, f2))
        norm1 = math.sqrt(sum(a * a for a in f1))
        norm2 = math.sqrt(sum(b * b for b in f2))
        if norm1 == 0 or norm2 == 0: return 0.0
        return dot / (norm1 * norm2)
    except Exception:
        return 0.0


# ─── DB ────────────────────────────────────────────────────────────────────
def resolve_db_path(args: dict, fallback_db: Path) -> Path:
    workspace_path = args.get("workspace_path")
    if workspace_path:
        return Path(workspace_path) / ".agent" / "memory" / "graph.db"
    return fallback_db

def get_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS nodes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            content     TEXT NOT NULL,
            category    TEXT NOT NULL DEFAULT 'general',
            energy      INTEGER NOT NULL DEFAULT 100,
            tier        TEXT NOT NULL DEFAULT 'hot',
            source_ids  TEXT,
            embedding   BLOB,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS edges (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            from_node   INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
            to_node     INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
            relation    TEXT NOT NULL DEFAULT 'related_to',
            created_at  TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_nodes_tier     ON nodes(tier);
        CREATE INDEX IF NOT EXISTS idx_nodes_category ON nodes(category);
        CREATE INDEX IF NOT EXISTS idx_nodes_energy   ON nodes(energy);
        CREATE INDEX IF NOT EXISTS idx_edges_from     ON edges(from_node);
    """)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(nodes)").fetchall()]
    for col, typedef in [("tier", "TEXT DEFAULT 'hot'"), ("source_ids", "TEXT"), ("embedding", "BLOB"), ("valid_from", "TEXT"), ("ended", "TEXT"), ("tags", "TEXT")]:
        if col not in cols:
            conn.execute(f"ALTER TABLE nodes ADD COLUMN {col} {typedef}")
            
    cols_edges = [r[1] for r in conn.execute("PRAGMA table_info(edges)").fetchall()]
    for col, typedef in [("valid_from", "TEXT"), ("ended", "TEXT")]:
        if col not in cols_edges:
            conn.execute(f"ALTER TABLE edges ADD COLUMN {col} {typedef}")
    conn.commit()


# ─── Tool Implementations ──────────────────────────────────────────────────

def tool_memory_save(args: dict, fallback_db: Path) -> str:
    db = resolve_db_path(args, fallback_db)
    content = args.get("content", "").strip()
    if not content: return "❌ content is required"
    category = args.get("category", "general")
    if category not in VALID_CATEGORIES: category = "general"
    
    now = datetime.now().isoformat()
    emb = get_embedding(content)
    
    tags_str = json.dumps(args.get("tags", []))
    valid_from = args.get("valid_from", now)
    ended = args.get("ended")

    conn = get_db(db)
    cur = conn.execute(
        "INSERT INTO nodes (content, category, energy, tier, embedding, tags, valid_from, ended, created_at, updated_at) VALUES (?, ?, 100, 'hot', ?, ?, ?, ?, ?, ?)",
        (content, category, emb, tags_str, valid_from, ended, now, now)
    )
    conn.commit()
    conn.close()
    
    emb_status = "✨[Vector]" if emb else "⚠️[No-Vector]"
    return f"✅ {emb_status} Saved hot node #{cur.lastrowid} [{category}]: {content[:80]}"


def tool_memory_search(args: dict, fallback_db: Path) -> str:
    db = resolve_db_path(args, fallback_db)
    keyword = args.get("keyword", "").strip()
    if not keyword: return "❌ keyword is required"
    tier = args.get("tier")
    limit = int(args.get("limit", 8))
    tier_filter = f"AND tier = '{tier}'" if tier in ("hot", "cold") else ""
    
    conn = get_db(db)
    
    # 1. Exact match (highest priority)
    exact_rows = conn.execute(
        f"SELECT id, tier, category, energy, content, created_at, tags, valid_from, ended FROM nodes WHERE content LIKE ? {tier_filter} ORDER BY energy DESC LIMIT ?",
        (f"%{keyword}%", limit)
    ).fetchall()
    
    results = []
    seen = set()
    for r in exact_rows:
        seen.add(r["id"])
        results.append({"row": r, "score": 1.0, "match": "exact"})

    # 2. Hybrid search: BM25 + Semantic cosine similarity
    query_emb = get_embedding(keyword)
    query_terms = keyword.lower().split()
    
    all_nodes = conn.execute(
        f"SELECT id, tier, category, energy, content, created_at, embedding, tags, valid_from, ended FROM nodes WHERE 1=1 {tier_filter}"
    ).fetchall()
    
    # Compute avg document length for BM25
    avg_dl = sum(len(r["content"].split()) for r in all_nodes) / max(len(all_nodes), 1)
    
    for r in all_nodes:
        if r["id"] in seen: continue
        
        # BM25 score
        bm25 = bm25_score(query_terms, r["content"], avg_dl)
        
        # Cosine similarity (if embeddings available)
        cosine = 0.0
        if query_emb and r["embedding"]:
            cosine = cosine_similarity(query_emb, r["embedding"])
        
        # Hybrid: weighted combination
        hybrid = 0.4 * min(bm25 / 3.0, 1.0) + 0.6 * cosine  # normalize BM25 to ~[0,1]
        
        if hybrid > 0.35 or bm25 > 1.0:
            match_detail = f"hybrid bm25={bm25:.2f} cos={cosine:.2f}"
            results.append({"row": dict(r), "score": hybrid, "match": match_detail})

    results.sort(key=lambda x: (x["score"], x["row"]["energy"]), reverse=True)
    results = results[:limit]

    if not results:
        conn.close()
        return f"🔍 No results for '{keyword}'"

    ids = [res["row"]["id"] for res in results]
    if ids:
        conn.execute(
            f"UPDATE nodes SET energy=MIN(100,energy+10), updated_at=? WHERE id IN ({','.join('?'*len(ids))})",
            [datetime.now().isoformat()] + ids
        )
        conn.commit()
    conn.close()

    lines = [f"🔍 Found {len(results)} result(s) for '{keyword}':\n"]
    for res in results:
        r = dict(res["row"])
        icon = "🔥" if r["tier"] == "hot" else "❄️"
        expired_flag = "🚨[QUÁ HẠN] " if r.get("ended") else ""
        tags_raw = r.get("tags")
        tags_str = f" {tags_raw}" if tags_raw and tags_raw not in ("[]", None) else ""
        lines.append(f"{icon} #{r['id']} [{r['category']}]{tags_str} ⚡{r['energy']} ({res['match']}) — {expired_flag}{r['content'][:150]}")
    return "\n".join(lines)


def tool_memory_link(args: dict, fallback_db: Path) -> str:
    db = resolve_db_path(args, fallback_db)
    from_id = args.get("from_id")
    to_id = args.get("to_id")
    relation = args.get("relation", "related_to")
    if not from_id or not to_id: return "❌ from_id and to_id are required"
    now = datetime.now().isoformat()
    conn = get_db(db)
    a = conn.execute("SELECT content FROM nodes WHERE id=?", (from_id,)).fetchone()
    b = conn.execute("SELECT content FROM nodes WHERE id=?", (to_id,)).fetchone()
    if not a or not b:
        conn.close()
        return f"❌ Node #{from_id} or #{to_id} not found"
    valid_from = args.get("valid_from", now)
    ended = args.get("ended")
    conn.execute(
        "INSERT INTO edges (from_node, to_node, relation, valid_from, ended, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (from_id, to_id, relation, valid_from, ended, now)
    )
    conn.commit()
    conn.close()
    return f"🔗 #{from_id} --[{relation}]--> #{to_id}\n  From: {a['content'][:60]}\n  To: {b['content'][:60]}"


def tool_memory_graph(args: dict, fallback_db: Path) -> str:
    db = resolve_db_path(args, fallback_db)
    node_id = args.get("node_id")
    if not node_id: return "❌ node_id is required"
    conn = get_db(db)
    node = conn.execute("SELECT * FROM nodes WHERE id=?", (node_id,)).fetchone()
    if not node:
        conn.close()
        return f"❌ Node #{node_id} not found"
    out = [f"🕸️ Node #{node['id']} [{node['tier'].upper()}] [{node['category']}] ⚡{node['energy']}"]
    out.append(f"   {node['content'][:200]}\n")
    outgoing = conn.execute("SELECT e.relation, e.to_node, n.content FROM edges e JOIN nodes n ON e.to_node=n.id WHERE e.from_node=?", (node_id,)).fetchall()
    if outgoing:
        out.append(f"→ OUTGOING ({len(outgoing)}):")
        for e in outgoing: out.append(f"  --[{e['relation']}]--> #{e['to_node']}: {e['content'][:80]}")
    incoming = conn.execute("SELECT e.relation, e.from_node, n.content FROM edges e JOIN nodes n ON e.from_node=n.id WHERE e.to_node=?", (node_id,)).fetchall()
    if incoming:
        out.append(f"\n← INCOMING ({len(incoming)}):")
        for e in incoming: out.append(f"  #{e['from_node']}: {e['content'][:80]} --[{e['relation']}]-->")
    conn.close()
    return "\n".join(out)


def tool_memory_fetch_pointers(args: dict, fallback_db: Path) -> str:
    db = resolve_db_path(args, fallback_db)
    ids = args.get("ids", [])
    if not ids or not isinstance(ids, list):
        return "❌ 'ids' must be a non-empty array of integers"
    
    placeholders = ",".join("?" * len(ids))
    conn = get_db(db)
    rows = conn.execute(
        f"SELECT id, content, tags, valid_from, ended FROM nodes WHERE id IN ({placeholders})",
        ids
    ).fetchall()
    conn.close()
    
    if not rows:
        return "❌ No nodes found for given pointers."
    
    out = ["📦 Fetched Memory Pointers (Raw Context):\n"]
    for r in rows:
        expired = f" (🚨 ENDED: {r['ended']})" if r["ended"] else ""
        out.append(f"--- [Pointer: #{r['id']}]{expired} ---")
        out.append(r["content"] + "\n")
    return "\n".join(out)


def tool_memory_hot(args: dict, fallback_db: Path) -> str:
    db = resolve_db_path(args, fallback_db)
    limit = int(args.get("limit", 10))
    conn = get_db(db)
    rows = conn.execute(
        "SELECT id, category, energy, content, embedding, created_at FROM nodes WHERE tier='hot' ORDER BY energy DESC, updated_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    if not rows: return "🔥 No hot nodes yet."
    lines = [f"🔥 HOT nodes ({len(rows)}):\n"]
    for r in rows:
        lines.append(f"  {'✨' if r['embedding'] else '  '}#{r['id']} [{r['category']}] ⚡{r['energy']} 📅{r['created_at'][:10]}")
        lines.append(f"     {r['content'][:120]}")
    return "\n".join(lines)


def tool_memory_cold(args: dict, fallback_db: Path) -> str:
    db = resolve_db_path(args, fallback_db)
    limit = int(args.get("limit", 10))
    conn = get_db(db)
    rows = conn.execute(
        "SELECT id, category, energy, content, source_ids, updated_at FROM nodes WHERE tier='cold' ORDER BY energy DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    if not rows: return "❄️ No cold nodes yet."
    lines = [f"❄️ COLD nodes ({len(rows)} consolidated):\n"]
    for r in rows:
        srcs = len(json.loads(r["source_ids"] or "[]"))
        lines.append(f"  #{r['id']} [{r['category']}] ⚡{r['energy']} (from {srcs} hot nodes)")
        lines.append(f"     {r['content'][:200]}")
    return "\n".join(lines)


def tool_memory_consolidate(args: dict, fallback_db: Path) -> str:
    db = resolve_db_path(args, fallback_db)
    days = int(args.get("days", 7))
    category = args.get("category")
    threshold = (datetime.now() - timedelta(days=days)).isoformat()
    cat_filter = f"AND category='{category}'" if category else ""
    
    conn = get_db(db)
    hot_rows = conn.execute(
        f"SELECT id, content, category FROM nodes WHERE tier='hot' AND updated_at<? {cat_filter} ORDER BY category, energy DESC",
        (threshold,)
    ).fetchall()
    
    if not hot_rows:
        conn.close()
        return f"⚡ No hot nodes older than {days} days to consolidate."
    
    from collections import defaultdict
    groups = defaultdict(list)
    for r in hot_rows:
        groups[r["category"]].append(r)
        
    results = []
    now = datetime.now().isoformat()
    for cat, nodes in groups.items():
        node_ids = [r["id"] for r in nodes]
        merged = "\n".join(f"• {r['content'][:200]}" for r in nodes[:20])
        summary = f"[Consolidated {len(nodes)} nodes — {cat}]\n{merged}"
        
        emb = get_embedding(summary)
        
        cur = conn.execute(
            "INSERT INTO nodes (content, category, energy, tier, source_ids, embedding, created_at, updated_at) VALUES (?, ?, 80, 'cold', ?, ?, ?, ?)",
            (summary, cat, json.dumps(node_ids), emb, now, now)
        )
        cold_id = cur.lastrowid
        for nid in node_ids:
            conn.execute("INSERT INTO edges (from_node, to_node, relation, created_at) VALUES (?, ?, 'consolidated_into', ?)", (nid, cold_id, now))
            conn.execute("UPDATE nodes SET energy=MAX(0, energy-40) WHERE id=?", (nid,))
        results.append(f"❄️ [{cat}] merged {len(nodes)} hot nodes → cold #{cold_id}")
    
    conn.commit()
    conn.close()
    return "\n".join(results) + f"\n\n✅ Done. Summary vectors calculated."


def tool_memory_status(args: dict, fallback_db: Path) -> str:
    db = resolve_db_path(args, fallback_db)
    conn = get_db(db)
    total = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    hot = conn.execute("SELECT COUNT(*) FROM nodes WHERE tier='hot'").fetchone()[0]
    cold = conn.execute("SELECT COUNT(*) FROM nodes WHERE tier='cold'").fetchone()[0]
    vecs = conn.execute("SELECT COUNT(*) FROM nodes WHERE embedding IS NOT NULL").fetchone()[0]
    edges = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    cats = conn.execute("SELECT category, COUNT(*) n FROM nodes GROUP BY category ORDER BY n DESC").fetchall()
    conn.close()
    lines = [
        f"🧠 Memory Graph Status",
        f"   DB: {db}",
        f"   Nodes: {total} total (🔥{hot} hot | ❄️{cold} cold | ✨{vecs} vector embeddings)",
        f"   Edges: {edges}",
        f"   Categories: " + ", ".join(f"{r['category']}({r['n']})" for r in cats)
    ]
    return "\n".join(lines)


# ─── MCP Protocol (stdio JSON-RPC 2.0) ────────────────────────────────────

TOOLS = {
    "memory_save": {
        "description": "Save an important piece of knowledge as a hot memory node. Will automatically generate vector embeddings.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_path": {"type": "string", "description": "Local workspace root path to avoid cross-project contamination"},
                "content": {"type": "string", "description": "The knowledge to save"},
                "category": {"type": "string", "enum": list(VALID_CATEGORIES), "description": "Category of knowledge"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "N-Dimensional space tags (e.g. ['UI', 'ChungKhoan'])"},
                "valid_from": {"type": "string", "description": "(Temporal) ISO DateTime when this fact became valid. Defaults to now."},
                "ended": {"type": "string", "description": "(Temporal) ISO DateTime when this fact expired/ended."}
            },
            "required": ["content"]
        }
    },
    "memory_search": {
        "description": "Search memory graph by keyword. Uses Semantic Cosine Similarity search under the hood.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_path": {"type": "string", "description": "Local workspace root path"},
                "keyword": {"type": "string", "description": "Keyword to search"},
                "tier": {"type": "string", "enum": ["hot", "cold"], "description": "Search only in hot or cold tier"},
                "limit": {"type": "integer", "description": "Max results (default 8)"}
            },
            "required": ["keyword"]
        }
    },
    "memory_link": {
        "description": "Create a relationship (edge) between two memory nodes.",
        "inputSchema": {"type": "object", "properties": {"workspace_path": {"type": "string"}, "from_id": {"type": "integer"}, "to_id": {"type": "integer"}, "relation": {"type": "string"}, "valid_from": {"type": "string"}, "ended": {"type": "string"}}, "required": ["from_id", "to_id"]}
    },
    "memory_fetch_pointers": {
        "description": "Fetch 100% raw verbatim content for an array of node IDs (Pointer-based lazy loading context).",
        "inputSchema": {"type": "object", "properties": {"workspace_path": {"type": "string"}, "ids": {"type": "array", "items": {"type": "integer"}}}, "required": ["ids"]}
    },
    "memory_graph": {"description": "Show all edges (incoming and outgoing) for a node.", "inputSchema": {"type": "object", "properties": {"workspace_path": {"type": "string"}, "node_id": {"type": "integer"}}, "required": ["node_id"]}},
    "memory_hot": {"description": "List hot (working memory) nodes.", "inputSchema": {"type": "object", "properties": {"workspace_path": {"type": "string"}, "limit": {"type": "integer"}}}},
    "memory_cold": {"description": "List cold (consolidated long-term memory) nodes.", "inputSchema": {"type": "object", "properties": {"workspace_path": {"type": "string"}, "limit": {"type": "integer"}}}},
    "memory_consolidate": {"description": "Merge old hot nodes into cold consolidated summaries.", "inputSchema": {"type": "object", "properties": {"workspace_path": {"type": "string"}, "days": {"type": "integer"}, "category": {"type": "string"}}}},
    "memory_status": {"description": "Show memory graph statistics.", "inputSchema": {"type": "object", "properties": {"workspace_path": {"type": "string"}}}}
}

TOOL_FNS = {
    "memory_save": tool_memory_save, "memory_search": tool_memory_search,
    "memory_link": tool_memory_link, "memory_graph": tool_memory_graph,
    "memory_hot": tool_memory_hot, "memory_cold": tool_memory_cold,
    "memory_consolidate": tool_memory_consolidate, "memory_status": tool_memory_status,
    "memory_fetch_pointers": tool_memory_fetch_pointers,
}

def send(obj: dict):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

def handle(req: dict, db: Path):
    method = req.get("method", "")
    req_id = req.get("id")

    if method == "initialize":
        send({"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "ag-kit-memory", "version": "1.0.1"}}})
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": req_id, "result": {"tools": [{"name": name, **info} for name, info in TOOLS.items()]}})
    elif method == "tools/call":
        name = req.get("params", {}).get("name", "")
        args = req.get("params", {}).get("arguments", {})
        fn = TOOL_FNS.get(name)
        if fn:
            try:
                result_text = fn(args, db)
                send({"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": result_text}], "isError": False}})
            except Exception as e:
                send({"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"❌ Error: {e}"}], "isError": True}})
        else:
            send({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Tool not found: {name}"}})
    elif method == "notifications/initialized":
        pass
    else:
        if req_id is not None:
            send({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}})

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=str(DEFAULT_DB))
    args = p.parse_args()
    db = Path(args.db)
    
    # Ensure DB ready
    conn = get_db(db)
    conn.close()

    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            req = json.loads(line)
            handle(req, db)
        except json.JSONDecodeError: pass
        except Exception as e: sys.stderr.write(f"[memory_mcp] Error: {e}\n")

if __name__ == "__main__":
    main()
