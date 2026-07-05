#!/bin/bash
# ============================================================================
# 🔌 auto_route_browser_to_reaper.sh
# Tự động nối dây âm thanh từ Browser (Firefox/Chrome) vào REAPER 
# qua PipeWire trên Linux.
# ============================================================================
# Cách dùng: bash auto_route_browser_to_reaper.sh
# ============================================================================

echo "🔌 AI Karaoke — Auto Audio Router"
echo "=================================="
echo ""

# Tìm REAPER input ports
echo "🔍 Đang tìm REAPER input ports..."
REAPER_INPUTS=$(pw-link -i 2>/dev/null | grep -i "reaper" | head -10)

if [ -z "$REAPER_INPUTS" ]; then
    echo "❌ Không tìm thấy REAPER đang chạy trong PipeWire!"
    echo "   Hãy chắc chắn REAPER đã mở và đang dùng ALSA/PipeWire."
    exit 1
fi

echo "✅ Tìm thấy REAPER inputs:"
echo "$REAPER_INPUTS"
echo ""

# Tìm Browser output ports (Firefox hoặc Chrome)
echo "🔍 Đang tìm Browser audio outputs..."
BROWSER_OUTPUTS=$(pw-link -o 2>/dev/null | grep -iE "(firefox|chrom)" | head -10)

if [ -z "$BROWSER_OUTPUTS" ]; then
    echo "⚠️  Không tìm thấy trình duyệt đang phát âm thanh."
    echo "   Hãy mở YouTube và bật một video/bài hát trước khi chạy script này."
    echo ""
    echo "💡 Mẹo: Trình duyệt chỉ xuất hiện trong PipeWire khi đang thực sự phát âm thanh."
    exit 1
fi

echo "✅ Tìm thấy Browser outputs:"
echo "$BROWSER_OUTPUTS"
echo ""

# Lấy 2 port output đầu tiên của browser (FL, FR)
BROWSER_FL=$(echo "$BROWSER_OUTPUTS" | head -1)
BROWSER_FR=$(echo "$BROWSER_OUTPUTS" | head -2 | tail -1)

# Lấy REAPER input ports 3 & 4 (hoặc bất kỳ input có sẵn)
# REAPER inputs thường có tên dạng: reaper:in3, reaper:in4
REAPER_IN3=$(echo "$REAPER_INPUTS" | grep -E "(in3|input_3|In 3)" | head -1)
REAPER_IN4=$(echo "$REAPER_INPUTS" | grep -E "(in4|input_4|In 4)" | head -1)

# Nếu không tìm thấy in3/in4, dùng 2 input đầu tiên chưa được dùng
if [ -z "$REAPER_IN3" ] || [ -z "$REAPER_IN4" ]; then
    echo "⚠️  Không tìm thấy Input 3/4 cụ thể. Sẽ thử nối vào input có sẵn."
    REAPER_IN3=$(echo "$REAPER_INPUTS" | head -3 | tail -1)
    REAPER_IN4=$(echo "$REAPER_INPUTS" | head -4 | tail -1)
fi

if [ -z "$REAPER_IN3" ] || [ -z "$REAPER_IN4" ]; then
    echo "❌ Không đủ REAPER input ports để nối."
    echo ""
    echo "📋 Danh sách tất cả input ports:"
    pw-link -i 2>/dev/null | grep -i "reaper"
    echo ""
    echo "📋 Danh sách tất cả output ports:"
    pw-link -o 2>/dev/null | grep -iE "(firefox|chrom)"
    exit 1
fi

echo "🔗 Đang nối dây..."
echo "   Browser FL → REAPER: $BROWSER_FL → $REAPER_IN3"
pw-link "$BROWSER_FL" "$REAPER_IN3" 2>/dev/null && echo "   ✅ FL connected!" || echo "   ⚠️ FL: đã nối hoặc lỗi"

echo "   Browser FR → REAPER: $BROWSER_FR → $REAPER_IN4"
pw-link "$BROWSER_FR" "$REAPER_IN4" 2>/dev/null && echo "   ✅ FR connected!" || echo "   ⚠️ FR: đã nối hoặc lỗi"

echo ""
echo "🎤 XONG! Bây giờ bạn có thể:"
echo "   1. Mở YouTube, bật nhạc Karaoke"
echo "   2. Cầm mic MixPre-6 và HÁT!"
echo ""
echo "💡 Nếu không nghe thấy nhạc từ YouTube trong REAPER,"
echo "   hãy kiểm tra lại track NHẠC NỀN có đang nhận Input 3/4 không."
echo "   Hoặc mở qpwgraph bằng lệnh:"
echo "   flatpak run org.rncbc.qpwgraph"
