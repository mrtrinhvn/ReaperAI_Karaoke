#!/bin/bash

# --- Antigravity Unified Receptionist (Port Fusion Edition) ---
# Trạm gác hợp nhất: AG Gateway Bot + Portal Bridge (HUD)

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

mkdir -p .agent/logs

# 0. NVM/Node PATH Resolution for GUI Execution
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
if [ -f "$HOME/.bashrc" ]; then
    source "$HOME/.bashrc" >/dev/null 2>&1 || true
fi
if [ -s "$HOME/.nvm/nvm.sh" ]; then
    source "$HOME/.nvm/nvm.sh" >/dev/null 2>&1 || true
fi
if [ -s "$HOME/.bun/_bun" ]; then
    export PATH="$HOME/.bun/bin:$PATH"
fi

# 1. Load Cấu hình Tĩnh từ .env
if [ -f .env ]; then
    source .env
fi

export PROJECT_NAME=${PROJECT_NAME:-"UnknownProject"}

echo "════════════════════════════════════════════════════"
echo "  🏢 AG GATEWAY - TRUYỀN TIN TELEGRAM"
echo "════════════════════════════════════════════════════"

# 2. Khởi động AG Gateway Bot (Trợ lý Telegram)
echo "[1/1] 🤖 Đang đánh thức Truyền tin Telegram... "
BOT_PID_FILE=".agent/logs/.ag_gateway_bot.pid"

if [ -f "bot/index.ts" ]; then
    TARGET_FILE="bot/index.ts"
elif [ -f "src/index.ts" ]; then
    TARGET_FILE="src/index.ts"
else
    echo "❌ Lỗi: Hệ thống chưa được uốn nắn Gateway (Thiếu src/index.ts hoặc bot/index.ts). Vui lòng gõ lệnh: npx ag-kit init-gateway"
    exit 1
fi

pkill -f "tsx $TARGET_FILE" 2>/dev/null
pkill -f "node $TARGET_FILE" 2>/dev/null

if [ -f "$BOT_PID_FILE" ]; then
    kill -9 $(cat "$BOT_PID_FILE") 2>/dev/null
fi
sleep 1

setsid bash -c "while true; do 
    echo \"\$(date): Khởi động Bot tại $TARGET_FILE...\" >> .agent/logs/bot_interaction.log
    npx tsx $TARGET_FILE >> .agent/logs/bot_interaction.log 2>&1
    EXIT_CODE=\$?
    if [ \$EXIT_CODE -eq 0 ]; then break; fi
    echo \"\$(date): Bot sụp đổ (Code: \$EXIT_CODE). Khởi động lại sau 5s...\" >> .agent/logs/bot_interaction.log
    sleep 5
done" > /dev/null 2>&1 &
echo $! > "$BOT_PID_FILE"
echo "      ✅ Truyền tin Telegram đã lên sóng (PID: $(cat "$BOT_PID_FILE"))"
echo "✅ HOÀN TẤT. Hệ thống chạy ngầm, bạn có thể tắt Terminal này!"
