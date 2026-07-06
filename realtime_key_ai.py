#!/usr/bin/env python3
"""
🎹 AI Real-time Key Detector
==================================================
Lắng nghe nhạc nền (Beat_AI) qua PipeWire và sử dụng librosa
để phân tích Chromagram, xác định Tone/Key của bài hát.
Kết quả sẽ được ghi vào /tmp/ai_karaoke_key.json
"""
import subprocess, struct, sys, os, time, json
import numpy as np
import librosa
from collections import deque
import threading

SAMPLE_RATE = 22050  # Librosa default for faster processing
CHANNELS = 1
CHUNK_SAMPLES = 2048
CHUNK_BYTES = CHUNK_SAMPLES * 2 * CHANNELS
KEY_FILE = "/tmp/ai_karaoke_key.json"

running = True

# Krumhansl-Schmuckler key profiles
major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def find_recorder_port(pid, retries=15):
    for _ in range(retries):
        time.sleep(0.3)
        try:
            res = subprocess.run(["pw-link", "-i"], capture_output=True, text=True)
            for l in res.stdout.splitlines():
                if "beat_ai_key" in l.lower() or "pw-record" in l.lower():
                    return l.strip()
        except: pass
    return None

def auto_connect_browser(rec_port):
    """Liên tục kiểm tra và nối trình duyệt vào AI Key Detector."""
    connected_ports = set()
    while running:
        try:
            res = subprocess.run(["pw-link", "-o"], capture_output=True, text=True)
            for l in res.stdout.splitlines():
                b = l.strip()
                if any(x in b.lower() for x in ["firefox", "chrom", "brave", "opera", "edge"]):
                    if b not in connected_ports:
                        subprocess.run(["pw-link", b, rec_port], capture_output=True)
                        connected_ports.add(b)
        except: pass
        time.sleep(2)

def analyze_key(audio_buffer):
    """Tính toán Chromagram và Key."""
    if len(audio_buffer) == 0:
        return None
    
    y = np.concatenate(audio_buffer)
    # Nếu âm thanh quá nhỏ (im lặng), bỏ qua
    rms = np.sqrt(np.mean(y**2))
    if rms < 0.005:
        return None
        
    chroma = librosa.feature.chroma_cqt(y=y, sr=SAMPLE_RATE)
    chroma_sum = np.sum(chroma, axis=1)
    
    # Tính correlation (Pearson)
    maj_corrs = []
    min_corrs = []
    for i in range(12):
        shifted_maj = np.roll(major_profile, i)
        shifted_min = np.roll(minor_profile, i)
        maj_corrs.append(np.corrcoef(chroma_sum, shifted_maj)[0, 1])
        min_corrs.append(np.corrcoef(chroma_sum, shifted_min)[0, 1])
        
    best_maj = np.argmax(maj_corrs)
    best_min = np.argmax(min_corrs)
    
    if maj_corrs[best_maj] > min_corrs[best_min]:
        return {"note": notes[best_maj], "note_idx": int(best_maj), "scale": "Major", "confidence": float(maj_corrs[best_maj])}
    else:
        return {"note": notes[best_min], "note_idx": int(best_min), "scale": "Minor", "confidence": float(min_corrs[best_min])}

def main():
    global running
    print("🎹 Khởi động AI Key Detector (Phân tích Tone nhạc)...")
    
    cmd = [
        "pw-record", 
        "-P", "node.name=Beat_AI_Key node.description=Beat_AI_Key media.name=Beat_AI_Key",
        "--rate", str(SAMPLE_RATE), "--channels", str(CHANNELS),
        "--format", "s16", "--latency", "2048", "--target", "0", "-"
    ]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        env=dict(os.environ, PIPEWIRE_CLIENT_NAME="Beat_AI_Key")
    )
    
    rec_port = find_recorder_port(proc.pid)
    if rec_port:
        threading.Thread(target=auto_connect_browser, args=(rec_port,), daemon=True).start()
    else:
        print("⚠️ Không tìm thấy port của Beat_AI_Key!")
        
    # Lưu khoảng 6 giây âm thanh (6 * 22050 = ~132000 samples)
    max_chunks = int(SAMPLE_RATE * 6 / CHUNK_SAMPLES)
    buffer = deque(maxlen=max_chunks)
    
    last_analysis = time.time()
    current_key = None
    
    try:
        while running:
            raw = proc.stdout.read(CHUNK_BYTES)
            if not raw or len(raw) < CHUNK_BYTES: break
                
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            buffer.append(samples)
            
            now = time.time()
            # Cứ mỗi 3 giây phân tích Tone 1 lần
            if now - last_analysis > 3.0 and len(buffer) > max_chunks // 2:
                key_info = analyze_key(list(buffer))
                if key_info and key_info['confidence'] > 0.6:
                    # Chống nhiễu: Chỉ cập nhật nếu confidence cao
                    current_key = key_info
                    
                    sys.stdout.write(f"\r\033[96m🎹 Detected Tone: {current_key['note']} {current_key['scale']} (Độ tự tin: {current_key['confidence']:.2f})\033[0m   ")
                    sys.stdout.flush()
                    
                    # Ghi ra JSON cho Lua đọc
                    try:
                        with open(KEY_FILE, "r") as f: data = json.load(f)
                    except: data = {}
                    
                    data["root_note"] = current_key["note_idx"]
                    data["scale"] = current_key["scale"]
                    data["root_name"] = current_key["note"]
                    data["timestamp"] = now
                    with open(KEY_FILE, "w") as f: json.dump(data, f)
                    
                last_analysis = now
    except KeyboardInterrupt: pass
    finally:
        running = False
        proc.terminate()

if __name__ == "__main__":
    main()
