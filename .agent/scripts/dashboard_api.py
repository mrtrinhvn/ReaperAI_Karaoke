#!/usr/bin/env python3
"""
dashboard_api.py — AG-KIT Dashboard Data API

Serves graph.db data as JSON for the HTML dashboard.
Lightweight HTTP server, no dependencies beyond stdlib.

Usage:
  python3 dashboard_api.py [--port 7842] [--db .agent/memory/graph.db]
"""

import json
import sqlite3
import sys
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

DEFAULT_PORT = 7842
DEFAULT_DB = ".agent/memory/graph.db"


def get_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def query_overview(conn):
    """Get system overview stats."""
    stats = {}
    for table, query in [
        ("symbols", "SELECT COUNT(*) FROM symbols"),
        ("edges", "SELECT COUNT(*) FROM struct_edges"),
        ("routes", "SELECT COUNT(*) FROM routes"),
        ("memory_nodes", "SELECT COUNT(*) FROM nodes"),
        ("memory_vectors", "SELECT COUNT(*) FROM nodes WHERE embedding IS NOT NULL"),
    ]:
        try:
            stats[table] = conn.execute(query).fetchone()[0]
        except:
            stats[table] = 0

    # Symbol breakdown
    stats["symbol_kinds"] = [
        dict(r) for r in conn.execute(
            "SELECT kind, COUNT(*) as count FROM symbols GROUP BY kind ORDER BY count DESC"
        ).fetchall()
    ]

    # Layer breakdown
    stats["layers"] = [
        dict(r) for r in conn.execute(
            "SELECT COALESCE(layer, 'unknown') as layer, COUNT(*) as count "
            "FROM symbols GROUP BY layer ORDER BY count DESC"
        ).fetchall()
    ]

    return stats


def query_graph_nodes(conn, limit=200):
    """Get symbols + edges for force-directed graph."""
    symbols = conn.execute(
        "SELECT id, name, kind, file_path, layer, line_start FROM symbols "
        "ORDER BY id LIMIT ?", (limit,)
    ).fetchall()

    edges = conn.execute(
        "SELECT from_symbol, to_symbol, relation FROM struct_edges"
    ).fetchall()

    # Build file groups
    file_groups = {}
    for s in symbols:
        fp = s["file_path"]
        if fp not in file_groups:
            file_groups[fp] = []
        file_groups[fp].append(s["id"])

    nodes = []
    for s in symbols:
        nodes.append({
            "id": s["id"],
            "name": s["name"],
            "kind": s["kind"],
            "file": os.path.basename(s["file_path"]) if s["file_path"] else "",
            "file_path": s["file_path"] or "",
            "layer": s["layer"] or "unknown",
            "line": s["line_start"] or 0,
        })

    links = [{"source": e["from_symbol"], "target": e["to_symbol"], "relation": e["relation"]} for e in edges]

    return {"nodes": nodes, "links": links, "files": {k: len(v) for k, v in file_groups.items()}}


def query_routes(conn):
    """Get all API routes."""
    rows = conn.execute(
        "SELECT method, path, framework, file_path FROM routes ORDER BY path"
    ).fetchall()
    return [dict(r) for r in rows]


def query_memory(conn):
    """Get memory nodes (without embeddings)."""
    rows = conn.execute(
        "SELECT id, content, category, tier, energy, tags, created_at, updated_at "
        "FROM nodes ORDER BY energy DESC, updated_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def query_files(conn):
    """Get file-level summary."""
    rows = conn.execute(
        "SELECT file_path, COUNT(*) as symbols, "
        "GROUP_CONCAT(DISTINCT kind) as kinds "
        "FROM symbols GROUP BY file_path ORDER BY symbols DESC"
    ).fetchall()
    return [dict(r) for r in rows]


class DashboardHandler(SimpleHTTPRequestHandler):
    db_path = DEFAULT_DB
    dashboard_dir = None

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # API routes
        if path.startswith("/api/"):
            self.send_json_response(path, params)
            return

        # Serve dashboard HTML
        if path == "/" or path == "/index.html":
            self.serve_dashboard()
            return

        # Default: 404
        self.send_error(404, "Not Found")

    def send_json_response(self, path, params):
        conn = get_db(self.db_path)
        try:
            if path == "/api/overview":
                data = query_overview(conn)
            elif path == "/api/graph":
                limit = int(params.get("limit", [200])[0])
                data = query_graph_nodes(conn, limit)
            elif path == "/api/routes":
                data = query_routes(conn)
            elif path == "/api/memory":
                data = query_memory(conn)
            elif path == "/api/files":
                data = query_files(conn)
            else:
                self.send_error(404, "Unknown API endpoint")
                return
        finally:
            conn.close()

        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def serve_dashboard(self):
        html_path = Path(self.dashboard_dir) / "dashboard.html"
        if not html_path.exists():
            self.send_error(404, "dashboard.html not found")
            return
        body = html_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # Silence logs


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AG-KIT Dashboard Server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--db", default=DEFAULT_DB)
    args = parser.parse_args()

    DashboardHandler.db_path = args.db
    DashboardHandler.dashboard_dir = str(Path(__file__).parent)

    server = HTTPServer(("127.0.0.1", args.port), DashboardHandler)
    print(f"🌐 AG-KIT Dashboard: http://localhost:{args.port}")
    print(f"📊 Database: {args.db}")
    print(f"   Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
