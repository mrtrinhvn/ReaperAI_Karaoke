#!/usr/bin/env python3
"""
🎤 Karaoke Control Panel — Web UI + Genre Presets
==================================================
HTTP server phục vụ giao diện chọn thể loại nhạc.
Ghi preset ra /tmp/ai_karaoke_genre.json → Python AI đọc → REAPER áp dụng.

Chạy: python3 karaoke_control.py
Mở: http://localhost:8888
"""
import json, os, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs

GENRE_FILE = "/tmp/ai_karaoke_genre.json"
BPM_FILE = "/tmp/ai_karaoke_bpm.txt"
CMD_FILE = "/tmp/ai_karaoke_commands.json"
PORT = 8888

# ═══════════════════════════════════════════════════
# 🎵 GENRE PRESETS — Tinh chỉnh cho từng thể loại
# ═══════════════════════════════════════════════════
PRESETS = {
    "bolero": {
        "name": "Bolero & Trữ tình",
        "emoji": "🌹",
        "color": "#e74c3c",
        "gradient": "linear-gradient(135deg, #e74c3c, #c0392b)",
        "desc": "Chậm rãi, da diết — reverb ấm, delay dài, giọng mượt",
        "bpm_suggest": 85,
        # Vocal FX
        "eq_mud_cut": -2.0,         # Cắt mud nhẹ (giữ body ấm)
        "eq_presence_boost": 2.0,   # Boost vừa (không chói)
        "eq_air_boost": 1.5,        # Air nhẹ
        "comp_ratio": 0.20,         # Nén nhẹ (giữ dynamics tự nhiên)
        "comp_thresh": 0.55,
        "delay_fraction": 0.75,     # Dotted 1/8 (bay bổng)
        "delay_volume": 0.25,       # Delay rõ
        "delay_feedback": 0.05,     # 1 lần nhại + chút đuôi mờ
        "reverb_room": 0.60,        # Phòng lớn (lãng mạn)
        "reverb_wet": 0.32,         # Nhiều reverb
        "reverb_damp": 0.45,        # Ít hấp thụ → vang dài
        "reverb_width": 0.80,
        "chorus_mix": 0.05,         # Chorus siêu mỏng
        "duck_intensity": 0.8,      # Ducking vừa (nhạc nền quan trọng)
    },
    "dan_ca": {
        "name": "Dân ca & Nhạc đỏ",
        "emoji": "🎋",
        "color": "#27ae60",
        "gradient": "linear-gradient(135deg, #27ae60, #2ecc71)",
        "desc": "Tự nhiên, trong trẻo — ít hiệu ứng, giọng rõ ràng",
        "bpm_suggest": 100,
        "eq_mud_cut": -1.0,
        "eq_presence_boost": 3.0,   # Boost mạnh (giọng cần rõ lời)
        "eq_air_boost": 1.0,
        "comp_ratio": 0.22,
        "comp_thresh": 0.52,
        "delay_fraction": 0.5,      # 1/8 note (gọn)
        "delay_volume": 0.15,       # Delay nhỏ
        "delay_feedback": 0.0,
        "reverb_room": 0.35,        # Phòng nhỏ (tự nhiên)
        "reverb_wet": 0.20,
        "reverb_damp": 0.60,        # Hấp thụ nhiều → gọn
        "reverb_width": 0.65,
        "chorus_mix": 0.04,
        "duck_intensity": 0.6,
    },
    "nhac_tre": {
        "name": "Nhạc trẻ (V-Pop)",
        "emoji": "🎤",
        "color": "#9b59b6",
        "gradient": "linear-gradient(135deg, #9b59b6, #8e44ad)",
        "desc": "Hiện đại, sáng — nén mạnh, EQ sắc, reverb vừa",
        "bpm_suggest": 120,
        "eq_mud_cut": -3.0,         # Cắt mud mạnh
        "eq_presence_boost": 4.0,   # Boost mạnh (giọng nổi bật)
        "eq_air_boost": 3.0,        # Nhiều air (sáng)
        "comp_ratio": 0.30,         # Nén mạnh
        "comp_thresh": 0.48,
        "delay_fraction": 0.75,
        "delay_volume": 0.20,
        "delay_feedback": 0.0,
        "reverb_room": 0.40,
        "reverb_wet": 0.22,
        "reverb_damp": 0.55,
        "reverb_width": 0.75,
        "chorus_mix": 0.06,
        "duck_intensity": 1.0,
    },
    "ballad": {
        "name": "Ballad & Slow",
        "emoji": "💫",
        "color": "#2980b9",
        "gradient": "linear-gradient(135deg, #2980b9, #3498db)",
        "desc": "Bay bổng, lãng mạn — reverb rộng, chorus dày",
        "bpm_suggest": 75,
        "eq_mud_cut": -2.0,
        "eq_presence_boost": 2.5,
        "eq_air_boost": 2.5,
        "comp_ratio": 0.18,
        "comp_thresh": 0.55,
        "delay_fraction": 0.75,
        "delay_volume": 0.28,
        "delay_feedback": 0.08,     # Chút đuôi mờ → lãng mạn
        "reverb_room": 0.65,        # Phòng rất lớn
        "reverb_wet": 0.35,         # Nhiều reverb
        "reverb_damp": 0.40,
        "reverb_width": 0.85,
        "chorus_mix": 0.07,         # Chorus mượt
        "duck_intensity": 0.7,
    },
    "rap": {
        "name": "Rap & Hip-hop",
        "emoji": "🎧",
        "color": "#e67e22",
        "gradient": "linear-gradient(135deg, #e67e22, #d35400)",
        "desc": "Khô, nén chặt — gần không reverb, giọng sắc",
        "bpm_suggest": 95,
        "eq_mud_cut": -4.0,         # Cắt mud rất mạnh
        "eq_presence_boost": 5.0,   # Boost cực mạnh (rõ lời rap)
        "eq_air_boost": 2.0,
        "comp_ratio": 0.40,         # Nén rất mạnh
        "comp_thresh": 0.42,
        "delay_fraction": 0.25,     # 1/16 note (rất ngắn)
        "delay_volume": 0.10,       # Rất nhỏ
        "delay_feedback": 0.0,
        "reverb_room": 0.20,        # Phòng rất nhỏ
        "reverb_wet": 0.12,         # Gần khô
        "reverb_damp": 0.70,
        "reverb_width": 0.50,
        "chorus_mix": 0.03,         # Gần không chorus
        "duck_intensity": 1.2,      # Ducking mạnh (rap cần nghe rõ)
    },
    "dance": {
        "name": "Dance & EDM",
        "emoji": "🪩",
        "color": "#1abc9c",
        "gradient": "linear-gradient(135deg, #1abc9c, #16a085)",
        "desc": "Năng lượng cao — nén mạnh, vang ngắn, sáng chói",
        "bpm_suggest": 128,
        "eq_mud_cut": -3.0,
        "eq_presence_boost": 3.5,
        "eq_air_boost": 3.5,
        "comp_ratio": 0.35,
        "comp_thresh": 0.45,
        "delay_fraction": 0.5,      # 1/8 note (gọn với tempo nhanh)
        "delay_volume": 0.18,
        "delay_feedback": 0.0,
        "reverb_room": 0.25,
        "reverb_wet": 0.18,
        "reverb_damp": 0.65,
        "reverb_width": 0.70,
        "chorus_mix": 0.06,
        "duck_intensity": 1.0,
    },
}

# ═══════════════════════════════════════════════════
# HTTP Server
# ═══════════════════════════════════════════════════
class KaraokeHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_path = os.path.join(os.path.dirname(__file__), "karaoke_control.html")
            with open(html_path, "r", encoding="utf-8") as f:
                self.wfile.write(f.read().encode("utf-8"))

        elif self.path == "/api/presets":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(PRESETS, ensure_ascii=False).encode("utf-8"))

        elif self.path == "/api/status":
            status = {"genre": "nhac_tre", "bpm": 120}
            try:
                with open(GENRE_FILE, "r") as f:
                    data = json.load(f)
                    status["genre"] = data.get("genre", "nhac_tre")
            except: pass
            try:
                with open(BPM_FILE, "r") as f:
                    status["bpm"] = float(f.read().strip())
            except: pass
            try:
                with open(CMD_FILE, "r") as f:
                    cmd = json.load(f)
                    status["rms_db"] = cmd.get("rms_db", -60)
                    status["is_singing"] = cmd.get("is_singing", False)
            except: pass

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(status).encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")

        if self.path == "/api/genre":
            data = json.loads(body)
            genre = data.get("genre", "nhac_tre")
            if genre in PRESETS:
                preset = PRESETS[genre]
                result = {"genre": genre, "timestamp": time.time()}
                result.update(preset)
                with open(GENRE_FILE, "w") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                # Also update BPM suggestion
                with open(BPM_FILE, "w") as f:
                    f.write(str(preset["bpm_suggest"]))

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "genre": genre, "preset": preset}, ensure_ascii=False).encode("utf-8"))
            else:
                self.send_error(400, "Unknown genre")

        elif self.path == "/api/bpm":
            data = json.loads(body)
            bpm = data.get("bpm", 120)
            with open(BPM_FILE, "w") as f:
                f.write(str(bpm))
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "bpm": bpm}).encode("utf-8"))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # Quiet


if __name__ == "__main__":
    # Set default genre
    if not os.path.exists(GENRE_FILE):
        with open(GENRE_FILE, "w") as f:
            json.dump({"genre": "nhac_tre", **PRESETS["nhac_tre"]}, f, indent=2)

    server = HTTPServer(("0.0.0.0", PORT), KaraokeHandler)
    print(f"🎤 Karaoke Control Panel")
    print(f"   Mở trình duyệt: http://localhost:{PORT}")
    print(f"   Ctrl+C để dừng")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Đã dừng.")
