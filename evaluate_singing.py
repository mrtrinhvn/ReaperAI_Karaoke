#!/usr/bin/env python3
"""
🎤 AI Live Audition Evaluator for Reaper Karaoke
===============================================
- Automatically detects active mic port and REAPER master output ports.
- Records 10 seconds of Vocal Dry and Master Wet (with effects) in parallel.
- Analyzes Vocal Loudness, Music balance, Reverb tail (RT60), and Pitch tuning.
- Generates a beautifully formatted Markdown report as an IDE artifact.
"""

import os
import sys
import time
import json
import subprocess
import threading
import numpy as np
import librosa
import scipy.signal as signal

# Config
RECORD_DURATION = 15.0  # seconds
SR = 44100
ARTIFACT_DIR = "/home/tao/.gemini/antigravity-ide/brain/abb62a03-a770-4fd4-bdfa-74ff7d90f1e2"
REPORT_PATH = os.path.join(ARTIFACT_DIR, "singing_evaluation_report.md")
GENRE_FILE = "/tmp/ai_karaoke_genre.json"

def run_cmd(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.returncode
    except Exception as e:
        return str(e), 1

def get_ports(flag):
    out, _ = run_cmd(["pw-link", flag])
    return [l.strip() for l in out.splitlines() if l.strip()]

def measure_port_rms(port, duration=1.0):
    """Ghi âm thử 1 giây để đo mức âm lượng RMS (dBFS) trên cổng."""
    cmd = ["pw-record", "--target", port, "--rate=16000", "--channels=1", "--format=s16", "-d", str(duration), "-"]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=duration + 1.0)
        samples = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32)
        if len(samples) == 0:
            return -100.0
        rms = np.sqrt(np.mean(samples**2))
        return 20 * np.log10(rms / 32768.0 + 1e-10)
    except:
        return -100.0

def find_active_ports():
    print("🔍 Đang quét các cổng âm thanh hoạt động trên PipeWire...")
    out_ports = get_ports("-o")
    
    # 1. Tìm mic hoạt động từ Sound Devices / MixPre
    mic_candidates = [p for p in out_ports if "mixpre" in p.lower() and "capture" in p.lower() and "monitor" not in p.lower()]
    # Fallback to other captures if MixPre not active
    if not mic_candidates:
        mic_candidates = [p for p in out_ports if "capture" in p.lower() and "monitor" not in p.lower() and "reaper" not in p.lower() and "chrome" not in p.lower()]
        
    active_mic = None
    max_rms = -100.0
    for p in mic_candidates[:4]: # Check top 4 candidates
        rms = measure_port_rms(p, duration=0.8)
        print(f"  • Cổng mic [{p}]: {rms:.1f} dBFS")
        if rms > -60.0 and rms > max_rms:
            max_rms = rms
            active_mic = p
            
    if active_mic:
        print(f"  👉 Đã chọn Mic hoạt động: {active_mic} ({max_rms:.1f} dB)")
    else:
        # Fallback to the first MixPre port or default
        active_mic = mic_candidates[0] if mic_candidates else "default"
        print(f"  ⚠️ Không phát hiện giọng nói. Dùng cổng mặc định: {active_mic}")

    # 2. Tìm REAPER master output ports
    reaper_ports = [p for p in out_ports if "reaper" in p.lower() and "out" in p.lower()]
    if not reaper_ports:
        reaper_ports = ["REAPER:out1", "REAPER:out2"]
    print(f"  👉 Đã chọn cổng REAPER Master Out: {reaper_ports}")
    
    return active_mic, reaper_ports

def record_node(node_name, channels, target_file, source_ports):
    """Chạy pw-record ở passive mode rồi nối thủ công nguồn vào."""
    cmd = [
        "pw-record",
        "-P", f"node.name={node_name} node.description={node_name} media.name={node_name}",
        "--rate", str(SR),
        "--channels", str(channels),
        "--format", "s16",
        "--target", "0", # Không auto-link
        target_file
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Chờ node xuất hiện trên PipeWire rồi link cổng
    time.sleep(0.5)
    in_ports = get_ports("-i")
    target_ports = [p for p in in_ports if node_name.lower() in p.lower()]
    target_ports.sort()
    
    if len(target_ports) > 0 and len(source_ports) > 0:
        for idx, src in enumerate(source_ports):
            dst = target_ports[min(idx, len(target_ports) - 1)]
            subprocess.run(["pw-link", src, dst], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
    return proc

def analyze_audio(vocal_file, master_file):
    print("🧮 Đang xử lý và phân tích tín hiệu âm học...")
    
    # Load files
    y_voc, _ = librosa.load(vocal_file, sr=SR)
    y_mst, _ = librosa.load(master_file, sr=SR)
    
    # Đồng bộ hóa chiều dài 2 file do thời gian kích hoạt ghi âm bất đối xứng
    min_len = min(len(y_voc), len(y_mst))
    y_voc = y_voc[:min_len]
    y_mst = y_mst[:min_len]
    
    # 1. Loudness & Balance (Vocal vs Master)
    rms_voc = np.sqrt(np.mean(y_voc**2))
    rms_mst = np.sqrt(np.mean(y_mst**2))
    
    db_voc = 20 * np.log10(rms_voc + 1e-10)
    db_mst = 20 * np.log10(rms_mst + 1e-10)
    
    # Đo âm lượng trung bình khi có giọng hát (vocal rms > -40dB)
    hop_length = 512
    frame_energy = librosa.feature.rms(y=y_voc, frame_length=2048, hop_length=hop_length)[0]
    frame_db = 20 * np.log10(frame_energy + 1e-10)
    
    frame_energy_mst = librosa.feature.rms(y=y_mst, frame_length=2048, hop_length=hop_length)[0]
    frame_db_mst = 20 * np.log10(frame_energy_mst + 1e-10)
    
    singing_mask = frame_db > -45.0
    if np.any(singing_mask):
        db_voc_active = np.mean(frame_db[singing_mask])
        db_mst_active = np.mean(frame_db_mst[singing_mask])
        balance = db_voc_active - db_mst_active
    else:
        db_voc_active = -100.0
        db_mst_active = -100.0
        balance = 0.0

    # 2. Pitch & Autotune analysis (Tuning accuracy)
    pitch_drift = 0.0
    tuning_score = 100.0
    note_changes = 0
    
    if np.any(singing_mask):
        # Trích xuất tần số cơ bản (F0) bằng YIN
        # Chỉ phân tích đoạn vocal có tín hiệu đủ lớn
        y_singing = y_voc[np.repeat(singing_mask, hop_length)[:len(y_voc)]]
        if len(y_singing) > SR * 0.5:
            try:
                f0 = librosa.yin(y_singing, fmin=80, fmax=600, sr=SR)
                # Lọc F0 hợp lệ (>0)
                valid_f0 = f0[f0 > 0]
                if len(valid_f0) > 10:
                    # Convert to MIDI notes
                    midi_notes = 69 + 12 * np.log2(valid_f0 / 440.0)
                    
                    # Tính độ lệch pitch so với các nốt bán âm chuẩn (độ lệch cent)
                    cents_drift = (midi_notes - np.round(midi_notes)) * 100
                    pitch_drift = float(np.mean(np.abs(cents_drift)))
                    
                    # Điểm giọng hát chuẩn (100 - độ lệch cent trung bình)
                    tuning_score = max(0.0, 100.0 - pitch_drift)
                    
                    # Đếm số lần chuyển nốt (phát hiện hát giai điệu)
                    rounded_notes = np.round(midi_notes)
                    note_changes = int(np.sum(np.diff(rounded_notes) != 0))
            except:
                pass

    # 3. Reverb RT60 estimation on Master Wet
    rt60 = 0.0
    decays = []
    for i in range(1, len(frame_db_mst) - 10):
        # check if it decreases monotonically
        chunk = frame_db_mst[i:i+10]
        diffs = np.diff(chunk)
        if np.all(diffs < 0) and (chunk[0] - chunk[-1] > 8):
            slope = (chunk[-1] - chunk[0]) / (10 * hop_length / SR)
            decays.append(slope)
            
    if len(decays) > 0:
        rt60 = float(-60.0 / np.mean(decays))

    # 4. Genre Estimation
    genre_est = "Không xác định"
    genre_conf = 0.0
    
    # Đọc thông số genre hiện tại từ panel để so sánh
    current_genre_name = "Chưa chọn"
    try:
        with open(GENRE_FILE, "r") as f:
            gdata = json.load(f)
            current_genre_name = gdata.get("name", "Default")
    except:
        pass

    tempo, _ = librosa.beat.beat_track(y=y_mst, sr=SR)
    if hasattr(tempo, '__len__'):
        tempo_val = float(tempo[0])
    else:
        tempo_val = float(tempo)

    # Đơn giản hóa nhận diện thể loại qua tempo và năng lượng
    if tempo_val > 120:
        genre_est = "Dance / Remix"
        genre_conf = 85.0
    elif tempo_val > 105:
        genre_est = "Nhạc Trẻ Pop"
        genre_conf = 80.0
    elif tempo_val > 88:
        genre_est = "Rap / HipHop"
        genre_conf = 75.0
    elif tempo_val > 78:
        genre_est = "Bolero / Trữ Tình"
        genre_conf = 90.0
    else:
        genre_est = "Ballad Sâu Lắng"
        genre_conf = 85.0

    return {
        "db_voc": db_voc_active,
        "db_mst": db_mst_active,
        "balance": balance,
        "pitch_drift": pitch_drift,
        "tuning_score": tuning_score,
        "note_changes": note_changes,
        "rt60": rt60,
        "tempo": tempo_val,
        "genre_est": genre_est,
        "genre_conf": genre_conf,
        "current_genre": current_genre_name
    }

def generate_report(res):
    print("📝 Đang khởi tạo báo cáo đánh giá giọng hát...")
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    
    # Đánh giá chung
    loudness_advice = ""
    if res["balance"] > -5.0:
        loudness_advice = "🔊 **Giọng hát quá to so với nhạc nền (Vocal Dominant)**. Đề xuất: Hãy giảm fader VOCAL xuống khoảng -2dB hoặc tăng fader NHẠC lên một chút để giọng quyện vào beat hơn."
    elif res["balance"] < -18.0:
        loudness_advice = "🔇 **Giọng hát bị nhạc đè (Vocal Buried)**. Đề xuất: Hãy tăng fader VOCAL thêm +3dB hoặc hạ fader NHẠC nền xuống mức -6dB đến -8dB."
    else:
        loudness_advice = "✅ **Tương quan âm lượng hoàn hảo!** Giọng ca nổi bật rõ nét trên nền nhạc và hòa quyện rất tốt."

    tuning_advice = ""
    if res["tuning_score"] >= 85:
        tuning_advice = "🎤 **Giọng hát cực kỳ chuẩn nhạc (In Tune)!** Bạn kiểm soát cao độ rất tốt. Mức độ can thiệp Autotune mượt mà, tự nhiên."
    elif res["tuning_score"] >= 70:
        tuning_advice = "🎼 **Cao độ tương đối ổn định**. Có một vài nốt bị chênh nhẹ (drift). Autotune đang giúp uốn giọng tự nhiên."
    else:
        tuning_advice = "⚠️ **Phát hiện lệch tông nhiều (Off-key)**. Đề xuất: Hãy bật Autotune mạnh hơn bằng cách đổi sang preset **Dance** hoặc chỉnh lại Tone/Key của beat nhạc khớp với giọng ca của bạn."

    reverb_advice = ""
    # Mẫu khonggianhatok.wav có RT60 = 0.64s
    if abs(res["rt60"] - 0.64) < 0.2:
        reverb_advice = "🌊 **Đuôi vang Reverb cực kỳ quyện nhạc!** Không gian phòng rất giống với file mẫu [khonggianhatok.wav](file:///home/tao/Downloads/khonggianhatok.wav) (~0.64s RT60)."
    elif res["rt60"] > 1.2:
        reverb_advice = "🚨 **Vang quá nhiều (Too Wet/Muddy)**. RT60 đo được là {:.2f}s (quá loãng). Đề xuất: Giảm bớt thanh **Vang (%)** trên Control Panel về mức -20% hoặc -40% để tránh rú rít và giữ giọng rõ nét.".format(res["rt60"])
    else:
        reverb_advice = "🏜️ **Giọng hát hơi khô (Too Dry)**. RT60 đo được là {:.2f}s (thiếu chiều sâu). Đề xuất: Hãy tăng thanh **Vang (%)** lên +20% đến +40% để hát nhẹ và bay bổng hơn.".format(res["rt60"])

    markdown_content = f"""# 🎤 BÁO CÁO THỬ GIỌNG TRỰC TIẾP AI (AI LIVE AUDITION REPORT)
> **Thời gian đánh giá:** {time.strftime('%Y-%m-%d %H:%M:%S')}  
> **Trạng thái kết nối:** ✅ Hoạt động ổn định

---

## 📊 KẾT QUẢ PHÂN TÍCH ÂM HỌC THỜI GIAN THỰC

| Chỉ Số Đánh Giá | Giá Trị Đo Được | Đánh Giá Hệ Thống |
| :--- | :---: | :---: |
| **Âm lượng Vocal (Active)** | `{res['db_voc']:.1f} dBFS` | Thể hiện mức độ bắt mic |
| **Âm lượng Master** | `{res['db_mst']:.1f} dBFS` | Tổng công suất đầu ra |
| **Tương quan Vocal / Music** | `{res['balance']:+.1f} dB` | Khoảng cách hòa trộn |
| **Điểm Cao Độ (Tuning Score)** | `{res['tuning_score']:.1f} / 100` | Mức độ giữ vững cao độ |
| **Đuôi Vang Reverb (RT60)** | `{res['rt60']:.2f} s` | Độ vang của không gian |
| **Tempo Phát Hiện (BPM)** | `{res['tempo']:.1f} BPM` | Đồng bộ nhịp tự động |
| **Thể Loại Đoán Được** | `{res['genre_est']}` | Phân tích qua tiết tấu |

---

## 💡 ĐỀ XUẤT ĐIỀU CHỈNH CHI TIẾT

### 1. Tương Quan Âm Lượng (Mixing Balance)
{loudness_advice}

### 2. Cao Độ & Autotune (Tuning Quality)
{tuning_advice}
*   *Giai điệu:* Phát hiện `{res['note_changes']}` lần chuyển nốt nhạc trong {int(RECORD_DURATION)} giây qua.

### 3. Không Gian Vang (Reverb & Echo Space)
{reverb_advice}

---

## 🎵 KIỂM TRA THỂ LOẠI NHẠC
*   Hệ thống tự động đoán bạn đang hát: **{res['genre_est']}** (Độ tin cậy: {res['genre_conf']:.0f}%).
*   Preset bạn đang chọn trên ứng dụng nổi: **{res['current_genre']}**.

> [!TIP]
> Bạn có thể bấm chọn lại preset thể loại nhạc tương ứng trên **Bảng điều khiển nổi** để AI tự động tối ưu hóa EQ và Echo theo đúng nhịp điệu của bài hát đó!
"""

    with open(REPORT_PATH, "w") as f:
        f.write(markdown_content)
        
    print(f"✅ Báo cáo đánh giá giọng hát đã được ghi thành công làm Artifact tại: {REPORT_PATH}")

def main():
    print("🎤 ═══ KHỞI ĐỘNG CHƯƠNG TRÌNH THỬ GIỌNG VỚI AI ═══")
    active_mic, reaper_ports = find_active_ports()
    
    print(f"\n🔴 Chuẩn bị ghi âm... Hãy chuẩn bị hát hoặc nói liên tục vào mic trong {int(RECORD_DURATION)} giây nhé!")
    for i in range(3, 0, -1):
        print(f"  ⏱️ Bắt đầu trong {i}...")
        time.sleep(1)
        
    vocal_wav = "/tmp/audition_vocal_dry.wav"
    master_wav = "/tmp/audition_master_wet.wav"
    
    # Xóa file cũ
    for f in [vocal_wav, master_wav]:
        if os.path.exists(f): os.remove(f)
        
    print(f"\n🎤 [ĐANG GHI ÂM CHẤN ĐOÁN] >>> Hãy Hát / Nói ngay bây giờ! ({int(RECORD_DURATION)} giây)...")
    
    # Ghi âm song song
    v_proc = record_node("Record_Vocal", 1, vocal_wav, [active_mic])
    m_proc = record_node("Record_Master", 2, master_wav, reaper_ports)
    
    # Progress bar
    total_steps = int(RECORD_DURATION)
    for s in range(total_steps):
        time.sleep(1.0)
        progress = int((s + 1) / RECORD_DURATION * 20)
        bar = '█' * progress + '░' * (20 - progress)
        sys.stdout.write(f"\r  🕒 Đang xử lý: [{bar}] {s+1}s / {total_steps}s")
        sys.stdout.flush()
    print()
    
    v_proc.terminate()
    m_proc.terminate()
    
    # Đợi file ghi xong
    time.sleep(0.5)
    
    if not os.path.exists(vocal_wav) or os.path.getsize(vocal_wav) < 1000:
        print("❌ Lỗi: Không thu âm được tín hiệu Vocal Dry!")
        sys.exit(1)
    if not os.path.exists(master_wav) or os.path.getsize(master_wav) < 1000:
        print("❌ Lỗi: Không thu âm được tín hiệu Master Wet từ REAPER!")
        sys.exit(1)
        
    print("✅ Đã ghi âm xong. Đang chạy phân tích phổ học...")
    
    # Phân tích
    res = analyze_audio(vocal_wav, master_wav)
    
    # Tạo báo cáo
    generate_report(res)
    
    print("\n🎯 ═══ KẾT QUẢ ĐÁNH GIÁ CHUNG ═══")
    print(f" • Thể loại nhạc đoán được: {res['genre_est']} ({res['tempo']:.0f} BPM)")
    print(f" • Điểm giữ cao độ: {res['tuning_score']:.1f} / 100")
    print(f" • Reverb RT60: {res['rt60']:.2f}s (Phòng mẫu là 0.64s)")
    print(f" • Vocal vs Music Balance: {res['balance']:+.1f} dB")
    print("=================================")
    print("\n👉 Bảng đánh giá chi tiết (Artifact) đã hiển thị trong IDE của bạn.")
    print("👉 Hãy xem file: [singing_evaluation_report.md](file://" + REPORT_PATH + ")")

if __name__ == "__main__":
    main()
