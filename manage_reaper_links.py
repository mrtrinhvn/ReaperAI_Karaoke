#!/usr/bin/env python3
"""
🔌 REAPER Connection Manager
=============================
- Chờ REAPER xuất hiện trên PipeWire (không cần REAPER mở trước)
- Nối đúng thiết bị: MixPre→REAPER in3/in4, Browser→REAPER in1/in2
- Chặn kết nối trái phép (webcam, loa ngẫu nhiên) vào REAPER
- Lưu cấu hình vào ~/.config/ai-karaoke-links.json
"""
import subprocess, json, os, time, sys, threading

CONFIG_FILE = os.path.expanduser("~/.config/ai-karaoke-links.json")
POLL_INTERVAL = 2.0

DEFAULT_CONFIG = {
    "music_sources": ["firefox", "chrom", "brave", "opera", "vivaldi", "edge"],
    "vocal_source": ["MixPre", "USB Audio", "USB Composite"],
    "reaper_music_in": ["REAPER:in1", "REAPER:in2"],
    "reaper_vocal_in": ["REAPER:in3", "REAPER:in4"],
}


def load_env_overrides():
    music_l = "REAPER:in1"
    music_r = "REAPER:in2"
    vocal_l = "REAPER:in3"
    vocal_r = "REAPER:in4"
    try:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k == "REAPER_MUSIC_IN_L": music_l = v
                        elif k == "REAPER_MUSIC_IN_R": music_r = v
                        elif k == "REAPER_VOCAL_IN_L": vocal_l = v
                        elif k == "REAPER_VOCAL_IN_R": vocal_r = v
    except Exception as e:
        print(f"Lỗi đọc cấu hình cổng từ .env trong manage_reaper_links.py: {e}")
    return [music_l, music_r], [vocal_l, vocal_r]


def load_config():
    music_ports, vocal_ports = load_env_overrides()
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
            cfg["reaper_music_in"] = music_ports
            cfg["reaper_vocal_in"] = vocal_ports
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        cfg = DEFAULT_CONFIG.copy()
        cfg["reaper_music_in"] = music_ports
        cfg["reaper_vocal_in"] = vocal_ports
        save_config(cfg)
        return cfg


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def run_pw(args, timeout=3):
    try:
        r = subprocess.run(["pw-link"] + args, capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.returncode
    except Exception:
        return "", 1


def get_all_ports(flag):
    out, _ = run_pw([flag])
    return [l.strip() for l in out.splitlines() if l.strip()]


def get_links():
    out, _ = run_pw(["-l"])
    links = []
    src = None
    for line in out.splitlines():
        if not line.startswith(" ") and not line.startswith("\t"):
            src = line.strip()
        elif src and "|-->" in line:
            dst = line.replace("|-->", "").strip()
            links.append((src, dst))
    return links


def is_reaper_running():
    ports = get_all_ports("-o") + get_all_ports("-i")
    return any("REAPER:" in p for p in ports)


def pw_link(src, dst):
    _, rc = run_pw([src, dst])
    if rc == 0:
        print(f"  ✅ {src} → {dst}")
    return rc == 0


def pw_unlink(src, dst):
    _, rc = run_pw(["-d", src, dst])
    if rc == 0:
        print(f"  🔌 Ngắt: {src} → {dst}")
    return rc == 0


def block_unauthorized(cfg=None):
    """Ngắt tất cả kết nối vào REAPER ngoài whitelist."""
    if cfg is None:
        cfg = load_config()
    allowed = (
        cfg["music_sources"] +
        cfg["vocal_source"] +
        # Thêm tên kỹ thuật của các thiết bị phổ biến
        ["Sound_Devices", "MixPre", "MixPre-6",
         "Beat_AI", "Vocal_AI", "Key_AI", "Master_AI", "ai_karaoke",
         "sfx_play", "pw-play"]
    )
    links = get_links()
    blocked = 0
    for src, dst in links:
        if "REAPER:" not in dst:
            continue
        if not any(kw.lower() in src.lower() for kw in allowed):
            print(f"  🚫 Chặn: {src} → {dst}")
            pw_unlink(src, dst)
            blocked += 1

    # Chặn riêng: mic (alsa_input) không được vào REAPER music in (in1/in2)
    music_ins = set(cfg.get("reaper_music_in", ["REAPER:in1", "REAPER:in2"]))
    for src, dst in links:
        if dst in music_ins and src.startswith("alsa_input."):
            # Kiểm tra đây có phải browser không (browser cũng có thể là alsa)
            is_browser = any(kw.lower() in src.lower() for kw in cfg["music_sources"])
            if not is_browser:
                print(f"  🔔 Mic vào nhạc-in (sai kênh!): {src} → {dst}")
                pw_unlink(src, dst)
                blocked += 1

    # ⚠️ ANTI-FEEDBACK bất điều kiện: Monitor ports KHÔNG BAO GIỜ vào REAPER
    # alsa_output.*:monitor_* là loopback của loa, nối vào REAPER → "ò ò"
    for src, dst in links:
        if ":monitor_" in src.lower() and "REAPER:" in dst:
            print(f"  🔇 Ngắt monitor→REAPER (feedback!): {src} → {dst}")
            pw_unlink(src, dst)
            blocked += 1

    if blocked:
        print(f"  → Đã chặn {blocked} kết nối trái phép.")
    return blocked



def setup_connections(cfg=None, verbose=True):
    """Thiết lập kết nối REAPER đúng theo cấu hình."""
    if cfg is None:
        cfg = load_config()
    if verbose:
        print("\n🎛️  Thiết lập kết nối REAPER...")

    outputs = get_all_ports("-o")
    connected = 0

    # Nhạc nền (Browser → REAPER in1/in2)
    music_ports = []
    for kw in cfg["music_sources"]:
        for port in outputs:
            if kw.lower() in port.lower():
                music_ports.append(port)
        if len(music_ports) >= 2:
            break

    if music_ports:
        for i, reaper_in in enumerate(cfg["reaper_music_in"]):
            if i < len(music_ports):
                if pw_link(music_ports[i], reaper_in):
                    connected += 1
    else:
        if verbose:
            print("  ℹ️  Chưa thấy nhạc nền (Browser). Bật nhạc trên trình duyệt trước.")

    # Mic (MixPre/USB → REAPER in3/in4)
    # Lấy tất cả các port capture thực sự (alsa_input.*:capture_*) của thiết bị vocal
    # loại bỏ monitor ports (alsa_output.*:monitor_*) để tránh gây feedback loop
    mic_ports = []
    for kw in cfg["vocal_source"]:
        for port in outputs:
            is_capture = ":capture_" in port.lower() or "alsa_input." in port.lower()
            is_monitor = ":monitor_" in port.lower()
            if kw.lower() in port.lower() and is_capture and not is_monitor:
                if port not in mic_ports:
                    mic_ports.append(port)
        # Sắp xếp các cổng để FL/FR, L/R có thứ tự ổn định
        if mic_ports:
            mic_ports.sort()
            break

    if mic_ports:
        target_map = {}
        if len(mic_ports) == 1:
            # Chỉ có 1 cổng thì nối vào cả hai
            for reaper_in in cfg["reaper_vocal_in"]:
                target_map[reaper_in] = mic_ports[0]
        else:
            # Có từ 2 cổng trở lên, map 1-1 tương ứng với REAPER vocal inputs
            for i, reaper_in in enumerate(cfg["reaper_vocal_in"]):
                if i < len(mic_ports):
                    target_map[reaper_in] = mic_ports[i]

        # Thực thi kết nối và dọn dẹp kết nối sai
        links = get_links()
        for reaper_in, target_src in target_map.items():
            # Tìm xem reaper_in này đang kết nối với nguồn nào
            current_srcs = [src for src, dst in links if dst == reaper_in]
            
            # Nếu chưa kết nối với target_src thì kết nối
            if target_src not in current_srcs:
                if pw_link(target_src, reaper_in):
                    connected += 1
            
            # Ngắt các nguồn kết nối sai khác tới cổng reaper_in này
            for src in current_srcs:
                # Chỉ ngắt nếu nguồn đó thuộc dải thiết bị vocal của chúng ta nhưng không phải target_src
                if src != target_src and any(kw.lower() in src.lower() for kw in cfg["vocal_source"]):
                    pw_unlink(src, reaper_in)
    else:
        if verbose:
            print("  ℹ️  Chưa thấy mic (MixPre/USB). Cắm mic vào rồi chạy lại nếu cần.")

    if verbose:
        print(f"  → Tổng: {connected} kết nối đã thiết lập.\n")
    return connected


def watch_loop(stop_event=None):
    """Vòng lặp liên tục theo dõi và bảo vệ kết nối REAPER."""
    was_running = False
    print("👁️  Connection watchdog đang chạy (chặn auto-link)...")
    while not (stop_event and stop_event.is_set()):
        running = is_reaper_running()
        if running and not was_running:
            print("\n🎵 REAPER xuất hiện! Đang cấu hình kết nối...")
            time.sleep(1.5)
            block_unauthorized()
            setup_connections()
            was_running = True
        elif running:
            # Định kỳ kiểm tra kết nối trái phép mới
            block_unauthorized()
        elif not running and was_running:
            print("\n⚠️  REAPER đã đóng. Tiếp tục theo dõi...")
            was_running = False
        time.sleep(POLL_INTERVAL)


def watch_background():
    """Chạy watchdog trong background thread. Trả về stop_event."""
    stop = threading.Event()
    t = threading.Thread(target=watch_loop, args=(stop,), daemon=True)
    t.start()
    return stop


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--watch"
    if arg == "--block":
        block_unauthorized()
    elif arg == "--connect":
        setup_connections()
    elif arg == "--watch":
        try:
            watch_loop()
        except KeyboardInterrupt:
            print("\n🛑 Connection manager dừng.")
    else:
        print("Usage: manage_reaper_links.py [--watch|--block|--connect]")
