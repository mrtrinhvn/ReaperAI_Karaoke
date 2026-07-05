#!/usr/bin/env python3
"""
memory_tool.py — Ag-Kit Two-Tier Memory System (Option B)

TIER 1 (HOT) — Working Memory: Fast write/read, exact + semantic search
  Save immediately: `save "content" --category decision`
  Search: `search "keyword"` (uses both LIKE and Cosine Similarity if model present)
  List hot nodes: `hot`

TIER 2 (COLD) — Long-term Memory: Consolidated summaries
  Consolidate hot → cold: `consolidate [--category X] [--days 7]`
  Search cold tier: `cold` | `search "kw" --tier cold`

EMBEDDINGS (Option B - Dual-Model Coordination):
  Automatically calls local Ollama `nomic-embed-text` during save & search.
  No external libraries required (pure python struct/math).
"""

import argparse
import sqlite3
import json
import urllib.request
import struct
import math
from pathlib import Path
from datetime import datetime, timedelta

try:
    from token_juice import juice_text
except ImportError:
    def juice_text(text, *args): return text

def sync_to_obsidian(node_id, tier, category, content, energy, conn=None):
    nodes_dir = Path(DEFAULT_DB).parent.parent / "knowledge" / "nodes"
    nodes_dir.mkdir(parents=True, exist_ok=True)
    
    edges_text = ""
    if conn:
        out_edges = conn.execute("SELECT relation, to_node FROM edges WHERE from_node=?", (node_id,)).fetchall()
        in_edges = conn.execute("SELECT relation, from_node FROM edges WHERE to_node=?", (node_id,)).fetchall()
        if out_edges or in_edges:
            edges_text += "\n\n## Quan hệ (Relations)\n"
            for e in out_edges: edges_text += f"- [{e['relation']}] -> [[Node_{e['to_node']}]]\n"
            for e in in_edges: edges_text += f"- <- [{e['relation']}] [[Node_{e['from_node']}]]\n"

    md_content = f"---\nid: {node_id}\ntier: {tier}\ncategory: {category}\nenergy: {energy}\n---\n\n# Node {node_id}: {category}\n\n{content}\n{edges_text}\n"
    file_path = nodes_dir / f"Node_{node_id}.md"
    file_path.write_text(md_content, encoding='utf-8')

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

def cosine_similarity(v1: bytes, v2: bytes) -> float:
    """Computes cosine similarity between two byte-packed float vectors."""
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


# ─── DB Setup ─────────────────────────────────────────────────────────────────

def get_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS nodes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            content         TEXT NOT NULL,
            category        TEXT NOT NULL DEFAULT 'general',
            energy          INTEGER NOT NULL DEFAULT 100,
            tier            TEXT NOT NULL DEFAULT 'hot',
            source_ids      TEXT,           
            embedding       BLOB,           
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS edges (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            from_node   INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
            to_node     INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
            relation    TEXT NOT NULL DEFAULT 'related_to',
            created_at  TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_nodes_category ON nodes(category);
        CREATE INDEX IF NOT EXISTS idx_nodes_tier     ON nodes(tier);
        CREATE INDEX IF NOT EXISTS idx_nodes_energy   ON nodes(energy);
        CREATE INDEX IF NOT EXISTS idx_edges_from     ON edges(from_node);
        CREATE INDEX IF NOT EXISTS idx_edges_to       ON edges(to_node);
    """)
    # Live migration
    cols = [r[1] for r in conn.execute("PRAGMA table_info(nodes)").fetchall()]
    for col, typedef in [("tier", "TEXT DEFAULT 'hot'"), ("source_ids", "TEXT"), ("embedding", "BLOB")]:
        if col not in cols:
            conn.execute(f"ALTER TABLE nodes ADD COLUMN {col} {typedef}")
    conn.commit()


# ─── HOT TIER ─────────────────────────────────────────────────────────────────

def cmd_save(args, conn):
    now = datetime.now().isoformat()
    category = args.category if args.category in VALID_CATEGORIES else "general"
    
    juiced_content = juice_text(args.content)
    emb = get_embedding(juiced_content)
    
    cur = conn.execute(
        "INSERT INTO nodes (content, category, energy, tier, embedding, created_at, updated_at) VALUES (?, ?, 100, 'hot', ?, ?, ?)",
        (juiced_content, category, emb, now, now)
    )
    node_id = cur.lastrowid
    conn.commit()
    
    sync_to_obsidian(node_id, 'hot', category, juiced_content, 100, conn)
    
    emb_status = "✨[Vector]" if emb else "⚠️[No-Vector]"
    print(f"✅ {emb_status} Saved hot node #{node_id} [{category}]: {juiced_content[:80]}")


def cmd_hot(args, conn):
    rows = conn.execute(
        "SELECT id, category, energy, content, embedding, created_at FROM nodes WHERE tier='hot' ORDER BY energy DESC, updated_at DESC LIMIT ?",
        (args.limit,)
    ).fetchall()
    print(f"🔥 HOT nodes ({len(rows)} shown):\n")
    for r in rows:
        v_mark = "✨" if r["embedding"] else " "
        print(f" {v_mark}#{r['id']} [{r['category']}] ⚡{r['energy']} 📅{r['created_at'][:10]}")
        print(f"     {r['content'][:120]}\n")


# ─── CONSOLIDATION (Hot → Cold) ───────────────────────────────────────────────

def cmd_consolidate(args, conn):
    threshold_date = (datetime.now() - timedelta(days=args.days)).isoformat()
    cat_filter = f"AND category = '{args.category}'" if args.category else ""

    hot_rows = conn.execute(
        f"SELECT id, content, category FROM nodes WHERE tier='hot' AND updated_at < ? {cat_filter} ORDER BY category, energy DESC",
        (threshold_date,)
    ).fetchall()

    if not hot_rows:
        print(f"⚡ No hot nodes older than {args.days} days to consolidate.")
        return

    from collections import defaultdict
    groups = defaultdict(list)
    for r in hot_rows:
        groups[r["category"]].append(r)

    consolidated_count = 0
    now = datetime.now().isoformat()

    for category, nodes in groups.items():
        if len(nodes) < 2 and not args.force:
            continue

        node_ids = [r["id"] for r in nodes]
        merged = "\n".join(f"• {r['content'][:200]}" for r in nodes[:20])
        summary = f"[Consolidated {len(nodes)} nodes — {category}]\n{merged}"

        juiced_summary = juice_text(summary)
        emb = get_embedding(juiced_summary)

        cur = conn.execute(
            "INSERT INTO nodes (content, category, energy, tier, source_ids, embedding, created_at, updated_at) VALUES (?, ?, 80, 'cold', ?, ?, ?, ?)",
            (juiced_summary, category, json.dumps(node_ids), emb, now, now)
        )
        cold_id = cur.lastrowid

        for nid in node_ids:
            conn.execute(
                "INSERT INTO edges (from_node, to_node, relation, created_at) VALUES (?, ?, 'consolidated_into', ?)",
                (nid, cold_id, now)
            )
            conn.execute("UPDATE nodes SET energy = MAX(0, energy - 40) WHERE id = ?", (nid,))

        sync_to_obsidian(cold_id, 'cold', category, juiced_summary, 80, conn)

        consolidated_count += 1
        print(f"❄️  [COLD] '{category}': merged {len(nodes)} hot nodes → #{cold_id}")

    conn.commit()
    print(f"\n✅ Consolidation complete. Run `gc` to cleanup dead hot nodes.")


# ─── COLD TIER ────────────────────────────────────────────────────────────────

def cmd_cold(args, conn):
    rows = conn.execute(
        "SELECT id, category, energy, content, source_ids, updated_at FROM nodes WHERE tier='cold' ORDER BY energy DESC, updated_at DESC LIMIT ?",
        (args.limit,)
    ).fetchall()
    print(f"❄️  COLD nodes ({len(rows)} shown):\n")
    for r in rows:
        sources = json.loads(r["source_ids"] or "[]")
        print(f"  #{r['id']} [{r['category']}] ⚡{r['energy']} (from {len(sources)} hot nodes)")
        print(f"     {r['content'][:200]}\n")


# ─── GRAPH (Edges) ────────────────────────────────────────────────────────────

def cmd_link(args, conn):
    now = datetime.now().isoformat()
    a = conn.execute("SELECT id, content FROM nodes WHERE id = ?", (args.from_id,)).fetchone()
    b = conn.execute("SELECT id, content FROM nodes WHERE id = ?", (args.to_id,)).fetchone()
    if not a or not b:
        print(f"❌ Node #{args.from_id} or #{args.to_id} not found.")
        return
    conn.execute(
        "INSERT INTO edges (from_node, to_node, relation, created_at) VALUES (?, ?, ?, ?)",
        (args.from_id, args.to_id, args.relation, now)
    )
    conn.commit()
    print(f"🔗 Linked: #{args.from_id} --[{args.relation}]--> #{args.to_id}")


def cmd_graph(args, conn):
    node = conn.execute("SELECT * FROM nodes WHERE id = ?", (args.node_id,)).fetchone()
    if not node:
        print(f"❌ Node #{args.node_id} not found.")
        return
    print(f"🕸️  Graph around Node #{args.node_id} [{node['tier'].upper()}]:\n")
    print(f"  📌 #{node['id']} [{node['category']}] ⚡{node['energy']} — {node['content'][:150]}\n")

    outgoing = conn.execute("SELECT e.relation, e.to_node, n.content FROM edges e JOIN nodes n ON e.to_node=n.id WHERE e.from_node=?", (args.node_id,)).fetchall()
    if outgoing:
        print(f"  → OUT ({len(outgoing)}):")
        for e in outgoing: print(f"     --[{e['relation']}]--> #{e['to_node']}: {e['content'][:80]}")

    incoming = conn.execute("SELECT e.relation, e.from_node, n.content FROM edges e JOIN nodes n ON e.from_node=n.id WHERE e.to_node=?", (args.node_id,)).fetchall()
    if incoming:
        print(f"\n  ← IN ({len(incoming)}):")
        for e in incoming: print(f"     #{e['from_node']}: {e['content'][:80]} --[{e['relation']}]-->")


# ─── SEARCH ───────────────────────────────────────────────────────────────────

def cmd_search(args, conn):
    keyword = args.keyword.strip()
    tier_filter = f"AND tier = '{args.tier}'" if args.tier else ""
    
    # 1. Exact Match Search
    exact_rows = conn.execute(
        f"SELECT id, tier, category, energy, content, created_at FROM nodes WHERE content LIKE ? {tier_filter} ORDER BY energy DESC LIMIT ?",
        (f"%{keyword}%", args.limit)
    ).fetchall()

    results = []
    seen = set()

    for r in exact_rows:
        seen.add(r["id"])
        results.append({"row": r, "score": 1.0, "match": "exact"})

    # 2. Semantic Search (Cosine Similarity)
    query_emb = get_embedding(keyword)
    if query_emb:
        all_nodes = conn.execute(
            f"SELECT id, tier, category, energy, content, created_at, embedding FROM nodes WHERE embedding IS NOT NULL {tier_filter}"
        ).fetchall()
        for r in all_nodes:
            if r["id"] in seen: continue
            sim = cosine_similarity(query_emb, r["embedding"])
            if sim > 0.60:
                results.append({"row": dict(r), "score": sim, "match": f"semantic: {sim:.2f}"})

    # Sort & Limit
    results.sort(key=lambda x: (x["score"], x["row"]["energy"]), reverse=True)
    results = results[:args.limit]

    tier_label = f" [{args.tier.upper()}]" if args.tier else ""
    if not results:
        print(f"🔍 No results for '{keyword}'{tier_label}")
        return

    print(f"🔍 Found {len(results)} result(s) for '{keyword}'{tier_label}:\n")
    for res in results:
        r = res["row"]
        tier_icon = "🔥" if r["tier"] == "hot" else "❄️"
        print(f"  {tier_icon} #{r['id']} [{r['category']}] ⚡{r['energy']} ({res['match']}) — {r['content'][:120]}")

    ids = [res["row"]["id"] for res in results]
    if ids:
        conn.execute(
            f"UPDATE nodes SET energy = MIN(100, energy + 10), updated_at = ? WHERE id IN ({','.join('?'*len(ids))})",
            [datetime.now().isoformat()] + ids
        )
        conn.commit()


# ─── GC & LIST (Truncated Logic) ──────────────────────────────────────────────

def cmd_gc(args, conn):
    threshold = (datetime.now() - timedelta(days=args.days)).isoformat()
    conn.execute("UPDATE nodes SET energy = energy - 15 WHERE updated_at < ? AND tier = 'hot'", (threshold,))
    cur = conn.execute("DELETE FROM nodes WHERE energy <= 0")
    conn.commit()
    print(f"🗑️  GC: {cur.rowcount} dead nodes removed.")

def cmd_list(args, conn):
    rows = conn.execute("SELECT id, tier, category, energy, content FROM nodes ORDER BY energy DESC LIMIT ?", (args.limit,)).fetchall()
    hot_c = sum(1 for r in rows if r["tier"] == "hot")
    print(f"📋 {hot_c} hot 🔥 | {len(rows)-hot_c} cold ❄️")
    for r in rows:
        print(f"  #{r['id']} [{r['category']}] ⚡{r['energy']} — {r['content'][:80]}")

def cmd_export(args, conn):
    tier_filter = f"WHERE tier = '{args.tier}'" if args.tier else ""
    nodes = conn.execute(f"SELECT id, content, category, tier, energy, source_ids, created_at FROM nodes {tier_filter}").fetchall()
    edges = conn.execute("SELECT * FROM edges").fetchall()
    f = Path(args.output or ".agent/memory/export.json")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"nodes": [dict(r) for r in nodes], "edges": [dict(r) for r in edges]}, indent=2, ensure_ascii=False))
    print(f"✅ Exported {len(nodes)} nodes to {f}")


# ─── Continuous Learning (auto-extract rules from patterns) ────────────────────

def cmd_learn(args, conn):
    """Extract patterns/decisions from memory → generate learned rules."""
    # Collect recent high-energy patterns and decisions
    rows = conn.execute(
        "SELECT id, category, content, energy, created_at FROM nodes "
        "WHERE category IN ('pattern', 'decision', 'error') AND energy >= 50 "
        "ORDER BY energy DESC, updated_at DESC LIMIT 30"
    ).fetchall()

    if len(rows) < 2:
        print("ℹ️  Chưa đủ dữ liệu để học. Cần ít nhất 2 nodes (pattern/decision/error) với energy >= 50.")
        return

    # Group by category
    groups = {}
    for r in rows:
        cat = r["category"]
        if cat not in groups:
            groups[cat] = []
        groups[cat].append(r)

    # Generate rules file
    knowledge_dir = Path(args.db).parent.parent / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    output_file = knowledge_dir / "learned_rules.md"

    lines = [
        "# Learned Rules (Auto-generated)",
        f"> Extracted from {len(rows)} memory nodes on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "> DO NOT EDIT — will be regenerated by `memory_tool.py learn`",
        "",
    ]

    if "decision" in groups:
        lines.append("## Decisions")
        for r in groups["decision"]:
            lines.append(f"- **[{r['created_at'][:10]}]** {r['content'][:200]}")
        lines.append("")

    if "pattern" in groups:
        lines.append("## Patterns")
        for r in groups["pattern"]:
            lines.append(f"- {r['content'][:200]}")
        lines.append("")

    if "error" in groups:
        lines.append("## Known Issues & Fixes")
        for r in groups["error"]:
            lines.append(f"- ⚠️ {r['content'][:200]}")
        lines.append("")

    output_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"📚 Learned {len(rows)} rules → {output_file}")
    for cat, items in groups.items():
        print(f"   {cat}: {len(items)} entries")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=str(DEFAULT_DB))
    sub = p.add_subparsers(dest="cmd")

    ps = sub.add_parser("save")
    ps.add_argument("content")
    ps.add_argument("--category", "-c", default="general")

    pf = sub.add_parser("search")
    pf.add_argument("keyword")
    pf.add_argument("--limit", "-n", type=int, default=10)
    pf.add_argument("--tier", choices=["hot", "cold"], default=None)

    sub.add_parser("hot").add_argument("--limit", "-n", type=int, default=20)
    sub.add_parser("cold").add_argument("--limit", "-n", type=int, default=20)
    sub.add_parser("list").add_argument("--limit", "-n", type=int, default=20)
    
    pl = sub.add_parser("link")
    pl.add_argument("from_id", type=int); pl.add_argument("to_id", type=int); pl.add_argument("--relation", "-r", default="related_to")
    
    sub.add_parser("graph").add_argument("node_id", type=int)
    
    pcon = sub.add_parser("consolidate")
    pcon.add_argument("--days", type=int, default=7); pcon.add_argument("--category", default=None); pcon.add_argument("--force", action="store_true")
    
    sub.add_parser("gc").add_argument("--days", type=int, default=30)
    
    pex = sub.add_parser("export")
    pex.add_argument("--output", "-o", default=None); pex.add_argument("--tier", default=None)

    sub.add_parser("learn")

    args = p.parse_args()
    if not args.cmd: return p.print_help()

    conn = get_db(Path(args.db))
    try:
        globals()["cmd_"+args.cmd](args, conn)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
