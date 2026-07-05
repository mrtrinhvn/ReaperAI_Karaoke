"""
ai_karaoke_controller.py

Đóng vai trò là cầu nối để AI (hoặc các tập lệnh tự động) có thể can thiệp vào REAPER
thông qua giao thức OSC (Open Sound Control) nhằm điều chỉnh EQ, Volume tùy theo giọng hát.

Cài đặt thư viện:
pip install python-osc
"""
import time
from pythonosc import udp_client

# Cấu hình OSC client gửi tới REAPER (Mặc định REAPER nhận OSC ở port 8000)
IP = "127.0.0.1"
PORT = 8000

client = udp_client.SimpleUDPClient(IP, PORT)

def set_track_volume(track_num, volume_normalized):
    """
    Điều chỉnh volume của track.
    volume_normalized: 0.0 (âm vô cực) đến 1.0 (+12dB)
    0.716 tương đương khoảng 0dB.
    """
    client.send_message(f"/track/{track_num}/volume", volume_normalized)
    print(f"🔊 Đã set volume Track {track_num} = {volume_normalized:.2f}")

def toggle_fx(track_num, fx_num, bypass=False):
    """Bật tắt FX (Effect)"""
    val = 1.0 if bypass else 0.0
    client.send_message(f"/track/{track_num}/fx/{fx_num}/bypass", val)
    state = "TẮT" if bypass else "BẬT"
    print(f"🎛️ Đã {state} FX số {fx_num} trên Track {track_num}")

def tweak_reverb_wet(track_num, fx_num, wet_amount):
    """
    Giả lập việc AI tự động tinh chỉnh Reverb tùy theo thể loại nhạc.
    (Đòi hỏi thiết lập Custom OSC trong REAPER, ví dụ gửi tới tham số cụ thể)
    """
    # Ví dụ gửi tham số FX (tham số số 4 thường là Wet trong ReaVerbate)
    client.send_message(f"/track/{track_num}/fx/{fx_num}/fxparam/4/value", wet_amount)
    print(f"💦 Đã chỉnh Reverb Wet (Độ vang) = {wet_amount * 100}%")

def ai_auto_mix():
    print("🤖 AI đang bắt đầu phân tích và thiết lập Auto-Mix...")
    time.sleep(1)
    
    print("\n--- 1. Cân bằng âm lượng (Gain Staging) ---")
    print("- Hạ nhẹ nhạc nền (Track 2) để giọng hát nổi bật...")
    set_track_volume(2, 0.6) # Giảm xuống dưới 0dB
    time.sleep(0.5)
    
    print("\n--- 2. Kích hoạt & Tinh chỉnh FX cho giọng hát (Track 1) ---")
    print("- Bật Reverb & Delay...")
    toggle_fx(1, 3, bypass=False) # FX 3 (Delay)
    toggle_fx(1, 4, bypass=False) # FX 4 (Reverb)
    time.sleep(0.5)
    print("- Phân tích: Giọng hát đang hơi mỏng, tăng độ vang (Wet) lên 40%...")
    tweak_reverb_wet(1, 4, 0.4)
    
    print("\n✅ Hoàn tất quá trình Auto-Mix của AI! Bạn có thể bắt đầu hát.")

if __name__ == "__main__":
    ai_auto_mix()
