# 🎤 Hướng dẫn Tích hợp Auto-Tune (Nhận diện Tone Tự động)

Hệ thống AI Karaoke đã được tích hợp bộ **Real-time Key Detector** bằng thư viện `librosa`.
Mỗi khi bạn phát một bài beat trên trình duyệt, AI sẽ tự động phân tích phổ âm thanh (Chromagram) và tìm ra Tone (Key & Scale) của bài hát trong thời gian thực.

Tuy nhiên, do REAPER đóng kín các thông số của plugin mặc định *ReaTune*, AI không thể tự động vặn núm chỉnh Tone trong ReaTune được. 

Để tự động hóa hoàn toàn việc Auto-tune khớp với bài hát, bạn hãy làm theo 2 bước sau:

## 1. Cài đặt thư viện Python (Nếu chưa có)
AI Key Detector yêu cầu `librosa` để phân tích âm nhạc:
```bash
pip3 install librosa
```

## 2. Cài đặt Plugin Auto-Tune (Khuyên dùng)
Bạn cần 1 plugin VST3 / LV2 hỗ trợ nhận lệnh đổi Tone từ bên ngoài. Dưới đây là các phương án tốt nhất:

### Phương án A: Dùng Graillon 2 (Bản Miễn Phí - Dành cho mọi HĐH)
**Graillon 2** của hãng Auburn Sounds là plugin Auto-tune chất lượng cực cao, hoàn toàn miễn phí, và độ trễ thấp (Live).
1. Truy cập: [Auburn Sounds Graillon](https://www.auburnsounds.com/products/Graillon.html)
2. Tải bản Free Edition dành cho Linux (hoặc Windows/Mac tùy hệ điều hành của bạn).
3. Giải nén và chép file `Graillon 2.vst3` vào thư mục plugin của REAPER:
   - Linux: `~/.vst3/` hoặc `/usr/lib/vst3/`
   - Windows: `C:\Program Files\Common Files\VST3\`
4. Mở REAPER, mở track **VOCAL**, xóa ReaTune đi và thêm **Graillon 2** vào.
5. Khi script `start_karaoke.sh` chạy, nó sẽ tự động tìm thấy Graillon 2 và điều khiển các núm Note/Scale của Graillon 2 cho bạn!

### Phương án B: Dùng x42-autotune (LV2 - Cực nhanh cho Linux)
Dành riêng cho người dùng Linux, bạn có thể cài plugin `Fat1` (x42-autotune) có sẵn trong kho phần mềm:
```bash
sudo apt update
sudo apt install x42-plugins
```
Sau đó vào REAPER, thêm plugin tên là **Fat1** (hoặc x42-autotune) vào track VOCAL.

### Phương án C: Dùng MAutoPitch
Bạn cũng có thể tải bộ cài của **MeldaProduction** và sử dụng **MAutoPitch** (Miễn phí). Lua bridge cũng hỗ trợ tự động vặn các núm `Root` và `Scale` của plugin này.

---

## 🎉 Cách hoạt động
Khi bạn chạy `./start_karaoke.sh`:
- Script `realtime_key_ai.py` sẽ tự động bắt đầu nghe nhạc.
- Trên Terminal, bạn sẽ thấy dòng chữ xanh báo hiệu Tone nhạc được nhận dạng: `🎹 Detected Tone: C Major (Độ tự tin: 0.85)`.
- Lua Bridge (bên trong REAPER) sẽ lập tức chuyển Scale trong Graillon 2 / MAutoPitch thành C Major.
- Giọng hát của bạn tự động được căn chỉnh đúng 100% nốt nhạc!
