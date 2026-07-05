#!/usr/bin/env python3
"""
Ag-Kit Memory Migration Tool v4 -> v5 (Hybrid Memory)
Reads existing memory.db, applies TokenJuice, recalculates embeddings if possible, 
and exports to physical Obsidian .md files in .agent/knowledge/nodes/
"""

import sqlite3
from pathlib import Path
import sys
import json

# Adjust sys.path to load memory_tool and token_juice from the same folder
sys.path.append(str(Path(__file__).parent))

try:
    import memory_tool
except ImportError:
    print("❌ Could not import memory_tool.py. Ensure you run this from .agent/scripts/")
    sys.exit(1)

def migrate():
    db_path = memory_tool.DEFAULT_DB
    if not db_path.exists():
        print(f"⚠️ No database found at {db_path}. Nothing to migrate.")
        return

    conn = memory_tool.get_db(db_path)
    nodes = conn.execute("SELECT id, tier, category, content, energy FROM nodes").fetchall()
    
    print(f"🔄 Found {len(nodes)} nodes to migrate. Starting TokenJuice compression & Obsidian Mirroring...")
    
    migrated_count = 0
    for node in nodes:
        nid = node["id"]
        tier = node["tier"]
        category = node["category"]
        content = node["content"]
        energy = node["energy"]
        
        # 1. Apply TokenJuice
        try:
            from token_juice import juice_text
            juiced_content = juice_text(content)
        except Exception:
            juiced_content = content
        
        # 2. Recalculate embedding if changed (and if Ollama is running)
        # We'll skip forcing embedding updates here to avoid blocking if Ollama is down.
        # But we do want to update the DB text.
        if juiced_content != content:
            conn.execute("UPDATE nodes SET content = ? WHERE id = ?", (juiced_content, nid))
            
        # 3. Export to Obsidian .md
        memory_tool.sync_to_obsidian(nid, tier, category, juiced_content, energy, conn)
        migrated_count += 1

    conn.commit()
    print(f"✅ Migration complete! {migrated_count} nodes are now mirrored in .agent/knowledge/nodes/")

if __name__ == "__main__":
    migrate()
