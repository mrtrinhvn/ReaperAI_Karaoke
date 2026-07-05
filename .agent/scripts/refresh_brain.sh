#!/bin/bash
# refresh_brain.sh — Tầng 1 Memory: Rebuild codebase index for the current project
# Usage: bash .agent/scripts/refresh_brain.sh [root_dir]
# Output: .agent/cache/repomap.json

set -e
ROOT="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT="$ROOT/.agent/cache/repomap.json"

echo "🧠 Refreshing Codebase Brain (Tầng 1)..."
echo "   Root: $(realpath $ROOT)"
echo "   Output: $OUTPUT"

python3 "$SCRIPT_DIR/repomap.py" "$ROOT" --output "$OUTPUT" --max-files 200

echo ""
echo "✅ Codebase index updated at: $OUTPUT"
echo "   AI agents can now read this file instead of re-scanning the entire codebase."
echo ""

# AG-KIT V5 Memory Migration / Setup Hook
MEMORY_DB="$ROOT/.agent/memory/graph.db"
if [ -f "$MEMORY_DB" ]; then
    echo "🔄 Đang kiểm tra và đồng bộ SQLite sang AG-KIT V5 (Obsidian Mirroring)..."
    python3 "$SCRIPT_DIR/migrate_memory_v4.py"
else
    echo "✨ Thiết lập thư mục Ký ức vật lý cho AG-KIT V5..."
    mkdir -p "$ROOT/.agent/knowledge/nodes"
fi

echo ""
echo "📌 Next: Run memory_tool.py to access Tầng 2 (Working Memory Graph)"
