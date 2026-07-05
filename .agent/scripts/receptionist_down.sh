#!/bin/bash

# --- Antigravity Unified Shutdown (Port Fusion Edition) ---
# Dọn dẹp trạm gác Agentic Gateway.

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

if [ -f .env ]; then
    source .env
fi

BRIDGE_PORT=${BRIDGE_PORT:-9656}

echo "════════════════════════════════════════════════════"
echo "  🛑 ĐANG TẮT AG GATEWAY [$BRIDGE_PORT]..."
echo "════════════════════════════════════════════════════"

# 1. Tắt Portal Bridge
BRIDGE_PID_FILE=".agent/logs/.portal_bridge_${BRIDGE_PORT}.pid"
if [ -f "$BRIDGE_PID_FILE" ]; then
    kill $(cat "$BRIDGE_PID_FILE") 2>/dev/null && rm "$BRIDGE_PID_FILE"
    echo "✅ HUD Bridge đã tắt."
fi

# 2. Tắt Bot
BOT_PID_FILE=".agent/logs/.ag_gateway_bot.pid"
if [ -f "$BOT_PID_FILE" ]; then
    PID=$(cat "$BOT_PID_FILE")
    # Kill the whole process group for the bash loop
    pkill -P $PID 2>/dev/null
    kill $PID 2>/dev/null && rm "$BOT_PID_FILE"
    echo "✅ Bot Telegram đã tắt."
fi

echo "════════════════════════════════════════════════════"
echo "✅ HỆ THỐNG AG GATEWAY ĐĐA NGỦ."
echo "════════════════════════════════════════════════════"
