#!/usr/bin/env python3
"""
🎵 AI Real-time BPM Detector (Genre-Guided)
==================================================
Lắng nghe nhạc nền và tự động phát hiện tempo (BPM) bằng thuật toán Aubio.
Dùng thông tin Thể loại (Genre) để sửa lỗi nhận diện sai (gấp đôi / chia nửa).
"""
import subprocess, struct, sys, os, time, signal, threading, json
import numpy as np
import aubio

SAMPLE_RATE = 48000
CHANNELS = 1
CHUNK_SAMPLES = 512
CHUNK_BYTES = CHUNK_SAMPLES * CHANNELS * 2
BPM_FILE = "/tmp/ai_karaoke_bpm.txt"
GENRE_FILE = "/tmp/ai_karaoke_genre.json"

running = True
current_bpm = 120.0

def find_recorder_port(pid, retries=15):
    for _ in range(retries):
        time.sleep(0.3)
        try:
            res = subprocess.run(["pw-link", "-i"], capture_output=True, text=True)
            for l in res.stdout.splitlines():
                if "beat_ai" in l.lower() or "pw-record" in l.lower() or "pw-cat" in l.lower():
                    return l.strip()
        except: pass
    return None

def find_browser_ports():
    try:
        res = subprocess.run(["pw-link", "-o"], capture_output=True, text=True)
        ports = []
        for l in res.stdout.splitlines():
            l = l.strip()
            if any(b in l.lower() for b in ["firefox", "chrom", "brave", "opera", "edge", "vivaldi"]):
                ports.append(l)
        return ports
    except:
        return []

def passive_link(src, dst):
    try: subprocess.run(["pw-link", src, dst], capture_output=True)
    except: pass

def get_genre_suggested_bpm():
    try:
        with open(GENRE_FILE, "r") as f:
            data = json.load(f)
            return data.get("bpm_suggest", 120.0)
    except:
        return 120.0

def auto_connect_browser(rec_port):
    """Liên tục kiểm tra và nối trình duyệt vào Beat_AI nếu có."""
    connected_ports = set()
    while running:
        browsers = find_browser_ports()
        for b in browsers:
            if b not in connected_ports:
                print(f"🔗 Tự động nối nhạc: {b} → {rec_port}")
                passive_link(b, rec_port)
                connected_ports.add(b)
        time.sleep(2)

def correct_bpm(raw_bpm, suggested_bpm):
    """Sửa lỗi BPM bằng cách tìm tỷ lệ (multiplier) gần đúng nhất với thể loại."""
    if suggested_bpm <= 0: return raw_bpm
    multipliers = [0.5, 0.666, 1.0, 1.333, 1.5, 2.0]
    best_bpm = raw_bpm
    min_diff = 999
    
    for m in multipliers:
        actual = raw_bpm / m
        diff = abs(actual - suggested_bpm)
        if diff < min_diff:
            min_diff = diff
            best_bpm = actual
            
    # Giới hạn không cho lệch quá ±25% so với suggested
    if best_bpm > suggested_bpm * 1.25 or best_bpm < suggested_bpm * 0.75:
        return suggested_bpm
    return best_bpm

def main():
    global running, current_bpm
    print("🥁 Khởi động AI BPM Detector (Có định hướng thể loại)...")
    
    cmd = [
        "pw-record", 
        "-P", "node.name=Beat_AI node.description=Beat_AI media.name=Beat_AI",
        "--rate", str(SAMPLE_RATE), "--channels", str(CHANNELS),
        "--format", "s16", "--latency", "1024", "--target", "0", "-"
    ]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        env=dict(os.environ, PIPEWIRE_CLIENT_NAME="Beat_AI")
    )
    
    rec_port = find_recorder_port(proc.pid)
    if rec_port:
        threading.Thread(target=auto_connect_browser, args=(rec_port,), daemon=True).start()
    else:
        print("⚠️ Không tìm thấy port của Beat_AI!")

    tempo_detector = aubio.tempo("default", 1024, CHUNK_SAMPLES, SAMPLE_RATE)
    beats = []
    last_write = 0
    
    try:
        while running:
            raw = proc.stdout.read(CHUNK_BYTES)
            if not raw or len(raw) < CHUNK_BYTES: break
                
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Tính RMS để biết nhạc có đang phát không
            rms = np.sqrt(np.mean(samples**2))
            is_music_playing = bool(rms > 0.002) # Giảm ngưỡng cực nhạy (-54dB) để không bị ngắt vang khi nhạc nhỏ
            
            # Phải phân tích BPM trên MỌI khung hình để Aubio không bị lỡ nhịp
            is_beat = tempo_detector(samples)
            if is_beat:
                raw_bpm = tempo_detector.get_bpm()
                if 40 <= raw_bpm <= 240:
                    suggested = get_genre_suggested_bpm()
                    corrected_bpm = correct_bpm(raw_bpm, suggested)
                    beats.append(corrected_bpm)
                    if len(beats) > 8: beats.pop(0)
                    current_bpm = sum(beats) / len(beats)
            
            now = time.time()
            if now - last_write > 1.0:
                try:
                    with open(GENRE_FILE, "r") as f: data = json.load(f)
                except: data = {}
                data["is_music_playing"] = is_music_playing
                data["timestamp"] = now
                
                # Cập nhật BPM vào JSON
                if len(beats) > 0:
                    data["bpm_override"] = current_bpm
                    sys.stdout.write(f"\r\033[93m🎵 Auto-BPM: {current_bpm:.1f} (Raw: {raw_bpm:.1f}, Thể loại: {suggested})\033[0m   ")
                    sys.stdout.flush()
                
                with open(GENRE_FILE, "w") as f: json.dump(data, f)
                last_write = now
    except KeyboardInterrupt: pass
    finally:
        running = False
        proc.terminate()

if __name__ == "__main__":
    main()
