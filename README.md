# 🎤 Hệ thống AI x REAPER Karaoke

Dự án này là minh chứng khái niệm (Proof of Concept) cho việc sử dụng AI hoặc mã kịch bản tự động để biến DAW REAPER thành một trạm hát Karaoke / Hát Livestream chuyên nghiệp, nhận âm thanh từ trình duyệt (YouTube) và xuất ra âm thanh mix hoàn hảo.

## 📁 Cấu trúc dự án
1. `setup_karaoke.lua`: Script chạy trực tiếp trong REAPER. Nó sẽ ngay lập tức tạo 2 track (Giọng hát & Nhạc nền), cấu hình đường dẫn thu âm và chèn sẵn chuỗi hiệu ứng (Vocal Chain: EQ, Comp, Delay, Reverb).
2. `ai_karaoke_controller.py`: Mã nguồn Python mô phỏng một AI Agent điều khiển quá trình mix nhạc (Auto-Mix) bằng giao thức OSC (Open Sound Control) không cần chạm tay vào chuột.

---

## 🛠️ Hướng dẫn cài đặt & Sử dụng (Trên hệ điều hành Linux - Pop!_OS)

### Bước 1: Khởi tạo Project tự động với Lua
1. Mở phần mềm **REAPER**.
2. Kéo thả file `setup_karaoke.lua` từ dự án này thẳng vào màn hình làm việc của REAPER, hoặc vào **Actions > Show action list... > New action > Load ReaScript** và chọn file này.
3. Chạy script. REAPER sẽ tự tạo 2 track: `🎙️ Vocal Mic` và `🎵 Nhạc nền (YouTube)`. Cả 2 đều tự động bật Record Monitoring (để bạn nghe được tiếng mình hát).

### Bước 2: Nối dây âm thanh từ YouTube (Firefox/Chrome) vào REAPER
Vì bạn đang dùng Linux (Pop!_OS mặc định dùng PipeWire), việc lấy âm thanh từ trình duyệt cực kỳ dễ:
1. Cài đặt công cụ nối dây âm thanh `qpwgraph` (nếu chưa có):
   ```bash
   sudo apt install qpwgraph
   ```
2. Mở YouTube, bật bài Karaoke bạn muốn hát.
3. Mở `qpwgraph`. Bạn sẽ thấy một "khối" hình chữ nhật đại diện cho Firefox/Chrome.
4. Nối 2 dây đầu ra của Firefox/Chrome vào ngõ vào **Input 3** và **Input 4** của REAPER.
   *(Track nhạc nền trong script đã được cấu hình sẵn để hứng âm thanh từ kênh 3/4 này).*
5. Giờ âm thanh YouTube sẽ chạy xuyên qua REAPER và bạn có thể hát cùng!

### Bước 3: Cho phép AI Agent tự động Mix & Điều khiển (OSC)
Để chạy file Python giúp AI điều chỉnh âm thanh, ta cần kích hoạt OSC trong REAPER:
1. Trong REAPER, nhấn `Ctrl + P` (Preferences) -> kéo xuống phần **Control/OSC/web**.
2. Nhấn **Add** -> Control surface mode chọn **OSC (Open Sound Control)**.
3. Đặt **Receive on port** là `8000`. Nhấn OK.
4. Mở Terminal, cài đặt thư viện cho Python:
   ```bash
   pip install python-osc
   ```
5. Chạy lệnh AI tự động căn chỉnh:
   ```bash
   python3 ai_karaoke_controller.py
   ```
6. Bạn sẽ thấy REAPER tự động nhảy thanh âm lượng của nhạc nền xuống một chút và kích hoạt độ vang của Reverb phù hợp!

---

## 🚀 Tương lai (Đo lường & Tinh chỉnh EQ tự động)
Để AI thực sự "đo lường" được phổ giọng hát và chỉnh EQ:
- Ta cần sử dụng thư viện **`reapy`** hoặc viết **ReaScript bằng Python/C++** để liên tục lấy mẫu dữ liệu (sample data) từ Peak/RMS của Track Giọng hát.
- Phân tích tần số đó bằng các thuật toán Fourier (FFT) trên Python.
- Dựa trên kết quả FFT (ví dụ phát hiện giọng bạn nhiều Bass), AI sẽ gửi lệnh qua OSC hoặc API để tự động cắt các dải băng tần thấp (Low Cut) trên plugin `ReaEQ`.
