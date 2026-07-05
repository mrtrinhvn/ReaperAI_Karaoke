import sys
import time
import subprocess
import threading
import numpy as np
import pyaudio

# Pipewire Node name
NODE_NAME = "Master_AI"
STATUS_FILE = "/tmp/ai_karaoke_master_status.txt"

running = True

def passive_link(src_port, dest_port):
    """Nối 2 cổng audio (chỉ nối nếu chưa nối)."""
    try:
        subprocess.run(["pw-link", src_port, dest_port], capture_output=True, timeout=2)
    except: pass

def get_reaper_master_ports():
    """Tìm cổng đầu ra của REAPER (out1 hoặc out2)."""
    try:
        res = subprocess.run(["pw-link", "-o"], capture_output=True, text=True, timeout=3)
        ports = []
        for l in res.stdout.splitlines():
            if "reaper" in l.lower() and "out" in l.lower():
                ports.append(l.strip())
        return ports
    except:
        return []

def find_recorder_port(pid, retries=10):
    """Tìm input port của pw-record process vừa tạo."""
    for _ in range(retries):
        time.sleep(0.3)
        try:
            result = subprocess.run(
                ["pw-link", "-i"], capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if "master_ai" in line.lower() or "pw-record" in line.lower() or "pw-cat" in line.lower():
                    return line
        except Exception:
            pass
    return None

def auto_connect_master(rec_port):
    """Liên tục kiểm tra và nối REAPER master output vào Master_AI."""
    connected = False
    while running:
        if not connected:
            master_ports = get_reaper_master_ports()
            if master_ports:
                for p in master_ports:
                    print(f"🔗 Tự động nối Master: {p} → {rec_port}")
                    passive_link(p, rec_port)
                connected = True
        time.sleep(2)

def main():
    global running
    print(f"Khởi động Master AI Monitor...")
    
    # Bật pw-record để phân tích Master
    import os
    env = os.environ.copy()
    env["PIPEWIRE_CLIENT_NAME"] = NODE_NAME
    
    proc = subprocess.Popen(
        ["pw-record", "--target", "auto", "--latency=512", "--rate=48000", "--channels=1", "--format=f32", "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=env
    )
    
    rec_port = find_recorder_port(proc.pid)
    if rec_port:
        threading.Thread(target=auto_connect_master, args=(rec_port,), daemon=True).start()
    else:
        print("⚠️ Không tìm thấy port của Master_AI!")

    try:
        while running:
            data = proc.stdout.read(4096 * 4) # 4096 samples f32
            if not data:
                break
                
            samples = np.frombuffer(data, dtype=np.float32)
            if len(samples) == 0: continue
            
            # Tính toán RMS và Peak
            rms = np.sqrt(np.mean(samples**2))
            rms_db = 20 * np.log10(rms + 1e-10)
            peak = np.max(np.abs(samples))
            peak_db = 20 * np.log10(peak + 1e-10)
            
            status = "OK"
            if peak_db > -0.5:
                status = "OVERLOAD"
            
            with open(STATUS_FILE, "w") as f:
                f.write(status)
                
    except KeyboardInterrupt:
        print("Stopping Master AI...")
    finally:
        running = False
        proc.terminate()
        try:
            with open(STATUS_FILE, "w") as f:
                f.write("OK")
        except: pass

if __name__ == "__main__":
    main()
