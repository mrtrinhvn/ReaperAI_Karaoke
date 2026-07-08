#!/usr/bin/env python3
import subprocess, time, json, os
import numpy as np

CALIB_FILE = "/tmp/ai_karaoke_calib.json"
SAMPLE_RATE = 48000
CHANNELS = 1
RECORD_SEC = 5
CHUNK_BYTES = SAMPLE_RATE * 2 * RECORD_SEC

def analyze_vocal(samples):
    # Dùng numpy để phân tích phổ (FFT)
    # Chia làm 3 dải: Bass (0-300Hz), Mid (300-3000Hz), Treble (3000Hz+)
    fft = np.fft.rfft(samples)
    fft_mag = np.abs(fft)
    freqs = np.fft.rfftfreq(len(samples), 1.0/SAMPLE_RATE)
    
    bass_idx = np.where((freqs >= 80) & (freqs <= 300))[0]
    mid_idx = np.where((freqs > 300) & (freqs <= 3000))[0]
    treb_idx = np.where((freqs > 3000) & (freqs <= 12000))[0]
    
    bass_energy = np.sum(fft_mag[bass_idx])
    mid_energy = np.sum(fft_mag[mid_idx])
    treb_energy = np.sum(fft_mag[treb_idx])
    
    total = bass_energy + mid_energy + treb_energy
    if total == 0: return {}
    
    b_ratio = bass_energy / total
    m_ratio = mid_energy / total
    t_ratio = treb_energy / total
    
    calib = {}
    
    # Logic Kỹ sư âm thanh (DSP Heuristics):
    
    # 1. Nếu Bass quá nhiều (>35%), giọng bị đục (muddy) -> Cắt Low-mid
    if b_ratio > 0.35:
        calib["eq_band_2_gain_db"] = -4.0 # Notch 300Hz mạnh
    elif b_ratio < 0.15:
        calib["eq_band_2_gain_db"] = 0.0  # Không cắt để giữ độ ấm
        
    # 2. Nếu Treble quá ít (<15%), giọng bị tối -> Boost High-shelf (Air)
    if t_ratio < 0.15:
        calib["eq_band_4_gain_db"] = 3.5  # Boost mạnh treble
    elif t_ratio > 0.30:
        calib["eq_band_4_gain_db"] = 0.5  # Giảm độ chói
        
    # 3. Phân tích độ sắc (Presence)
    if m_ratio < 0.40:
        calib["eq_band_3_gain_db"] = 4.0  # Boost 2.5kHz để cắt xuyên mix
        
    return calib

def main():
    PROGRESS_FILE = "/tmp/ai_karaoke_calib_progress.json"
    RECORD_SEC = 5.0
    MAX_TIMEOUT = 30.0
    
    def write_progress(status, seconds):
        try:
            with open(PROGRESS_FILE, "w") as f:
                json.dump({
                    "status": status,
                    "seconds": round(seconds, 1),
                    "target_seconds": RECORD_SEC,
                    "progress": min(1.0, round(seconds / RECORD_SEC, 2))
                }, f)
        except:
            pass

    print("🎙️ Khởi động lấy mẫu giọng hát (tự động bỏ qua khoảng lặng)...")
    write_progress("waiting", 0.0)
    
    cmd = [
        "pw-record", 
        "-P", "node.description='AI Vocal Snapshot'",
        "--rate", str(SAMPLE_RATE), "--channels", str(CHANNELS),
        "--format", "s16", "--target", "0", "-"
    ]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        env=dict(os.environ, PIPEWIRE_CLIENT_NAME="Calibrate_AI")
    )
    
    time.sleep(0.5)
    
    # Link Mic in to this recorder
    try:
        res = subprocess.run(["pw-link", "-o"], capture_output=True, text=True)
        mic_port = None
        for l in res.stdout.splitlines():
            if "alsa_input" in l.lower() and "capture" in l.lower():
                mic_port = l.strip()
                break
        
        res2 = subprocess.run(["pw-link", "-i"], capture_output=True, text=True)
        rec_port = None
        for l in res2.stdout.splitlines():
            if "calibrate_ai" in l.lower() or "pw-record" in l.lower():
                rec_port = l.strip()
                break
                
        if mic_port and rec_port:
            subprocess.run(["pw-link", mic_port, rec_port], capture_output=True)
    except: pass

    # Đọc non-blocking
    import fcntl
    flags = fcntl.fcntl(proc.stdout, fcntl.F_GETFL)
    fcntl.fcntl(proc.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    
    start_time = time.time()
    accumulated_seconds = 0.0
    raw = b""
    CHUNK_SIZE = 4096 # 2048 samples = ~0.042 giây
    
    try:
        while accumulated_seconds < RECORD_SEC:
            elapsed = time.time() - start_time
            if elapsed > MAX_TIMEOUT:
                print("\n⚠️ Quá thời gian lấy mẫu (30 giây). Kết thúc.")
                write_progress("timeout", accumulated_seconds)
                proc.terminate()
                return
                
            try:
                chunk = proc.stdout.read(CHUNK_SIZE)
                if chunk and len(chunk) > 0:
                    samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
                    rms = np.sqrt(np.mean(samples**2)) if len(samples) > 0 else 0.0
                    
                    # Ngưỡng phát hiện tiếng hát: 0.012 (~ -38dBFS)
                    if rms > 0.012:
                        raw += chunk
                        accumulated_seconds += len(chunk) / (SAMPLE_RATE * 2.0)
                        write_progress("recording", accumulated_seconds)
                        sys.stdout.write(f"\r🎙️ Đang thu âm: {accumulated_seconds:.1f}s / {RECORD_SEC:.1f}s ({20*np.log10(rms+1e-5):.1f} dB)")
                        sys.stdout.flush()
                    else:
                        write_progress("waiting", accumulated_seconds)
                        sys.stdout.write(f"\r🎙️ Hãy hát vào mic: {accumulated_seconds:.1f}s / {RECORD_SEC:.1f}s (Chờ giọng hát...)  ")
                        sys.stdout.flush()
                else:
                    time.sleep(0.01)
            except BlockingIOError:
                time.sleep(0.01)
            except Exception:
                time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n🛑 Bị dừng bởi người dùng.")
        write_progress("error", accumulated_seconds)
        proc.terminate()
        return
        
    proc.terminate()
    
    if len(raw) < 1000:
        print("\nKhông thu đủ âm thanh giọng hát!")
        calib = {"eq_band_2_gain_db": 0.0, "eq_band_3_gain_db": 0.0, "eq_band_4_gain_db": 0.0}
        write_progress("error", accumulated_seconds)
    else:
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        calib = analyze_vocal(samples)
        write_progress("done", accumulated_seconds)
    
    calib["timestamp"] = time.time()
    
    # Lưu kết quả
    with open(CALIB_FILE, "w") as f:
        json.dump(calib, f)
        
    print("\n" + "="*50)
    print("✅ ĐÃ PHÂN TÍCH GIỌNG THÀNH CÔNG!")
    print("="*50)
    print("THÔNG SỐ TRƯỚC / SAU KHI CHỈNH (EQ BANDS):")
    
    mud_change = calib.get('eq_band_2_gain_db', 0.0)
    pres_change = calib.get('eq_band_3_gain_db', 0.0)
    air_change = calib.get('eq_band_4_gain_db', 0.0)
    
    # Base values từ setup_karaoke.lua
    print(f" • Bùn đục (Low-mid 300Hz): -3.0 dB ➔ {(-3.0 + mud_change):.1f} dB (Thay đổi: {mud_change:+.1f} dB)")
    print(f" • Sắc nét (Presence 2.5kHz): +3.0 dB ➔ {(3.0 + pres_change):.1f} dB (Thay đổi: {pres_change:+.1f} dB)")
    print(f" • Bông xốp (Air 12kHz):    +2.5 dB ➔ {(2.5 + air_change):.1f} dB (Thay đổi: {air_change:+.1f} dB)")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
