#!/bin/bash

# ==============================================================================
# BỘ LÕI KHỞI TẠO NÃO BỘ CỤC BỘ (LOCAL BRAIN BOOTSTRAPPER)
# ==============================================================================
# Kịch bản này được gọi khi khởi tạo dự án ag-kit mới để đảm bảo Hệ trọng số Model
# đã được tải và sẵn sàng cho môi trường Định Tuyến Offline (.env route_mode).

# Danh sách Kỹ năng/Vũ khí Hạng nặng được The Root Engine chỉ định (Tháng 4/2026)
CORE_MODELS=(
    "hf.co/mohusein/Nemotron-Orchestrator-8B-Claude-4.5-Opus-Distill-GGUF:iq4_nl"
    "hf.co/bartowski/Qwen2.5.1-Coder-7B-Instruct-GGUF:IQ4_XS"
    "nomic-embed-text:latest"
)

echo "🚀 [Local Brain Bootstrap] Kích hoạt tiến trình nạp hệ trọng số..."

# 1. Kiểm tra Ollama Core
if ! command -v ollama &> /dev/null
then
    echo "❌ [LỖI] Không tìm thấy 'ollama' trên hệ thống."
    echo "Vui lòng cài đặt tại: https://ollama.com/download"
    echo "Sau đó chạy lại script này."
    exit 1
fi

# 2. Kiểm tra nhịp tim Ollama Daemon
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "⏳ [CẢNH BÁO] Ollama Server chưa chạy định tuyến. Đang kích hoạt ngầm..."
    ollama serve >/dev/null 2>&1 &
    sleep 3
    
    if ! curl -s http://localhost:11434/api/tags > /dev/null; then
        echo "❌ [LỖI LÕI] Không thể khởi động Ollama Server ở port 11434."
        exit 1
    fi
    echo "✅ [Ollama Server] Đã nảy nhịp tim."
fi

# 3. Kéo mảng hệ trọng số
echo "📥 Đang bắt đầu quá trình trích xuất Vector từ Registry..."
for MODEL in "${CORE_MODELS[@]}"; do
    echo "---------------------------------------------------"
    echo "🔄 Đang Tải Não Bộ: $MODEL"
    # Lệnh pull của Ollama có thanh timeline để user theo dõi
    ollama pull "$MODEL"
    if [ $? -eq 0 ]; then
        echo "✅ [HOÀN TẤT] $MODEL đã đạn lên nòng."
    else
        echo "❌ [THẤT BẠI] Lỗi kết nối khi kéo $MODEL. Thử mạng hoặc VPN."
    fi
done

echo "==================================================="
echo "🎉 [BOOTSTRAP THÀNH CÔNG] Toàn bộ Não Bộ Cục Bộ đã có sẵn trong ổ cứng!"
echo "Bạn có thể thiết lập: AGENT_MODEL_MODE=local trong file .env để bóp cò."
echo "==================================================="
