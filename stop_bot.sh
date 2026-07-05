#!/bin/bash
# stop_bot.sh - Hạ cánh an toàn (Remoat + LazyGravity standard)

echo "🛑 Đang tắt toàn bộ trạm điều hành Agentic..."

# Gọi script hạ cánh tiêu chuẩn (Agent-Defined)
bash .agent/scripts/receptionist_down.sh

echo "✅ Đã dọn dẹp xong."
