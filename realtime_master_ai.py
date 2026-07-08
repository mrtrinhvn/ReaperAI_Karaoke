import sys
import time
import subprocess
import threading
import numpy as np

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

def find_recorder_ports(pid, retries=10):
    """Tìm các input port của pw-record process vừa tạo."""
    for _ in range(retries):
        time.sleep(0.3)
        try:
            result = subprocess.run(
                ["pw-link", "-i"], capture_output=True, text=True, timeout=3
            )
            ports = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if "master_ai" in line.lower() or "pw-record" in line.lower() or "pw-cat" in line.lower():
                    if line not in ports:
                        ports.append(line)
            if ports:
                ports.sort()
                return ports
        except Exception:
            pass
    return []

def auto_connect_master(rec_ports):
    """Liên tục kiểm tra và nối REAPER master output vào Master_AI theo đúng kênh L/R."""
    connected = False
    while running:
        if not connected:
            master_ports = get_reaper_master_ports()
            if master_ports and rec_ports:
                master_ports.sort()
                # Nối L -> L, R -> R để tránh chồng kênh
                if len(rec_ports) == 1:
                    for p in master_ports:
                        passive_link(p, rec_ports[0])
                else:
                    if len(master_ports) >= 2 and len(rec_ports) >= 2:
                        passive_link(master_ports[0], rec_ports[0])
                        passive_link(master_ports[1], rec_ports[1])
                    else:
                        for idx, p in enumerate(master_ports):
                            target_port = rec_ports[min(idx, len(rec_ports)-1)]
                            passive_link(p, target_port)
                connected = True
        time.sleep(2)

def main():
    global running
    print(f"Khởi động Master AI Monitor (Stereo)...")
    
    # Bật pw-record để phân tích Master (đặt là 2 channels stereo để tránh gộp mono làm tăng db và báo overload giả)
    import os
    env = os.environ.copy()
    env["PIPEWIRE_CLIENT_NAME"] = NODE_NAME
    
    proc = subprocess.Popen(
        ["pw-record", "-P", "node.name=Master_AI node.description=Master_AI media.name=Master_AI", "--target", "0", "--rate=48000", "--channels=2", "--format=f32", "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=env
    )
    
    rec_ports = find_recorder_ports(proc.pid)
    if rec_ports:
        threading.Thread(target=auto_connect_master, args=(rec_ports,), daemon=True).start()
    else:
        print("⚠️ Không tìm thấy port của Master_AI!")
 
    try:
        while running:
            # 4096 frames * 4 bytes/sample * 2 channels = 32768 bytes
            data = proc.stdout.read(4096 * 4 * 2) 
            if not data:
                break
                
            samples = np.frombuffer(data, dtype=np.float32)
            if len(samples) == 0: continue
            
            # Tính toán RMS và Peak trên các kênh độc lập
            rms = np.sqrt(np.mean(samples**2))
            rms_db = 20 * np.log10(rms + 1e-10)
            peak = np.max(np.abs(samples))
            peak_db = 20 * np.log10(peak + 1e-10)
            
            status = "OK"
            # Ngưỡng báo quá tải kỹ thuật số (clipping) chuẩn chuyên nghiệp là 0.0 dBFS.
            if peak_db >= 0.0:
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
