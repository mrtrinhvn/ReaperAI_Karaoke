#!/bin/bash
# ============================================================================
# 🎤 start_karaoke.sh v2 — One-click Karaoke Launcher (Passive Mode)
# ============================================================================
# Không gây xáo trộn kết nối trên qpwgraph!
#   1. Nạp Lua bridge vào REAPER (real-time FX control + BPM sync)
#   2. Kiểm tra Browser → REAPER (CHỈ nối nếu chưa có)
#   3. Khởi động AI Vocal Analyzer (passive — không auto-link)
# ============================================================================

DIR="$(cd "$(dirname "$0")" && pwd)"

# Thử đọc .env để cấu hình cổng nhạc nền của REAPER
REAPER_MUSIC_IN_L="REAPER:in1"
REAPER_MUSIC_IN_R="REAPER:in2"
if [ -f "$DIR/.env" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        # Bỏ qua dòng comment và dòng trống
        if [[ ! "$line" =~ ^# ]] && [[ "$line" =~ = ]]; then
            key=$(echo "$line" | cut -d'=' -f1 | tr -d '[:space:]')
            val=$(echo "$line" | cut -d'=' -f2- | tr -d '[:space:]' | tr -d '"' | tr -d "'")
            if [ "$key" = "REAPER_MUSIC_IN_L" ]; then REAPER_MUSIC_IN_L="$val"; fi
            if [ "$key" = "REAPER_MUSIC_IN_R" ]; then REAPER_MUSIC_IN_R="$val"; fi
        fi
    done < "$DIR/.env"
fi

echo "🎤 ═══════════════════════════════════════"
echo "   AI KARAOKE PRO v4 — Launcher"
echo "   (Passive Mode — Không xáo trộn routing)"
echo "═══════════════════════════════════════════"
echo ""

# Clean up any orphaned/zombie background AI processes from previous runs
echo "🧹 Đang dọn dẹp các tiến trình AI chạy ẩn từ lần trước..."
pkill -f "realtime_vocal_ai.py"
pkill -f "realtime_bpm_ai.py"
pkill -f "realtime_key_ai.py"
pkill -f "realtime_master_ai.py"
pkill -f "karaoke_app.py"
killall -9 pw-record pw-play 2>/dev/null || true
sleep 0.5

# Step 0: Ép hệ thống âm thanh PipeWire sử dụng Buffer Size an toàn (512 samples) để chống nổ loẹt xoẹt
echo "⚙️ Tối ưu hóa bộ đệm âm thanh (Buffer Size: 512 samples) chống nổ tiếng..."
pw-metadata -n settings 0 clock.force-quantum 512
sleep 0.2

# Step 1: Khởi động Connection Watchdog (chạy nền — không cần REAPER mở trước)
echo ""
echo "🔌 Connection Watchdog (Định tuyến kết nối tự động)..."
python3 "$DIR/manage_reaper_links.py" --watch &
LINK_PID=$!
echo "   ✅ Watchdog đang chạy (PID $LINK_PID) — tự nối khi REAPER xuất hiện"
echo "   🚫 Không còn tự kết nối webcam/lóa linh tinh nữa!"
echo ""
sleep 1

# Step 2: Nạp Lua bridge nếu REAPER đang chạy (watchdog sẽ xử lý nếu chưa)
if pgrep -x reaper > /dev/null 2>&1; then
    echo "🌉 REAPER đã chạy sẵn. Nạp AI FX Bridge v3..."
    /opt/REAPER/reaper -nonewinst "$DIR/realtime_fx_bridge.lua" &
    sleep 2
    echo "   ✅ AI FX Bridge đã được gửi tới REAPER."
else
    echo "🔔 REAPER chưa mở — Watchdog sẽ tự nối khi bạn mở REAPER."
    echo "   → Mở REAPER bất kỳ lúc nào, hệ thống sẽ tự cấu hình!"  
fi

# Step 3: Check (nhưng KHÔNG tự nối) Browser audio
# Chỉ nối nếu chưa có kết nối sẵn
echo ""
echo "🔌 Kiểm tra Browser → REAPER..."

BROWSER_FL=$(pw-link -o 2>/dev/null | grep -iE "(firefox|chrom|brave|opera|edge|vivaldi)" | head -1)
if [ -n "$BROWSER_FL" ]; then
    # Kiểm tra đã có kết nối Browser → REAPER chưa
    EXISTING=$(pw-link -l 2>/dev/null | grep -A1 "$BROWSER_FL" | grep -i "REAPER")
    if [ -n "$EXISTING" ]; then
        echo "   ✅ Browser đã được nối sẵn → REAPER. Không thay đổi."
    else
        echo "   ⚡ Đang tự động kết nối Browser → REAPER..."
        BROWSER_FR=$(pw-link -o 2>/dev/null | grep -iE "(firefox|chrom|brave|opera|edge|vivaldi)" | head -2 | tail -1)
        pw-link "$BROWSER_FL" "$REAPER_MUSIC_IN_L" 2>/dev/null && echo "   ✅ Kết nối Browser FL → $REAPER_MUSIC_IN_L"
        [ -n "$BROWSER_FR" ] && pw-link "$BROWSER_FR" "$REAPER_MUSIC_IN_R" 2>/dev/null && echo "   ✅ Kết nối Browser FR → $REAPER_MUSIC_IN_R"
    fi
else
    echo "   ⚠️ Không tìm thấy Browser đang phát nhạc (Firefox, Chrome, Brave...)."
    echo "   → BẠN LƯU Ý: Phải mở Youtube và bấm PLAY để nhạc kêu lên thì hệ thống mới tìm thấy được!"
    echo "   → Hãy bật nhạc trước, rồi chạy lại lệnh ./start_karaoke.sh nhé."
fi

# Step 4: Start Floating Control Panel (App nổi)
echo ""
echo "📱 Khởi động Bảng điều khiển nổi..."
python3 "$DIR/karaoke_app.py" &
PANEL_PID=$!
sleep 1
echo "   ✅ Bảng điều khiển (Always on Top) đã chạy."
echo "   → Bấm các nút trên bảng để đổi nhanh thể loại nhạc!"

# Step 5: Start the real-time analyzer (PASSIVE MODE)
echo ""
echo "🎤 Khởi động AI Vocal Analyzer (passive mode)..."
echo "   ★ pw-record khởi động với --target 0 (không xáo trộn)"
echo "   (Nhấn Ctrl+C để dừng tất cả)"
echo ""
sleep 1

# Cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Đang dừng tất cả..."
    kill $PANEL_PID 2>/dev/null
    kill $BPM_PID 2>/dev/null
    kill $KEY_PID 2>/dev/null
    kill $MASTER_PID 2>/dev/null
    kill $LINK_PID 2>/dev/null
    killall -9 pw-record pw-play 2>/dev/null || true
    # Reset PipeWire buffer size về tự động
    pw-metadata -n settings 0 clock.force-quantum 0
    echo "   ✅ Ứng dụng nổi và AI đã dừng"
    echo "   ✅ Kết nối qpwgraph không bị ảnh hưởng"
}
trap cleanup EXIT

echo "🎵 Khởi động AI BPM Detector (Auto-Detect)..."
python3 "$DIR/realtime_bpm_ai.py" &
BPM_PID=$!

echo "🎹 Khởi động AI Key Detector (Tone/Scale)..."
python3 "$DIR/realtime_key_ai.py" &
KEY_PID=$!

echo "🎧 Khởi động AI Master Monitor (Clipping Detect)..."
python3 "$DIR/realtime_master_ai.py" &
MASTER_PID=$!

python3 "$DIR/realtime_vocal_ai.py" "$@"


