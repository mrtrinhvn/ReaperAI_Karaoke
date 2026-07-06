#!/usr/bin/env python3
"""
🎤 Karaoke Control Panel — Floating Desktop App (GTK3)
======================================================
Ứng dụng nổi (Always on top) để chọn thể loại khi đang hát.
"""
import gi, json, os, time
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

GENRE_FILE = "/tmp/ai_karaoke_genre.json"
BPM_FILE = "/tmp/ai_karaoke_bpm.txt"
KEY_FILE = "/tmp/ai_karaoke_key.json"

PRESETS = {
    "bolero": {
        "name": "Bolero", 
        "emoji": "🌹", 
        "bpm_suggest": 85, 
        "color": "#e74c3c", 
        "delay_fraction": 0.5, "delay_volume": 0.18, "delay_feedback": 0.15, 
        "reverb_room": 0.65, "reverb_wet": 0.38, "reverb_damp": 0.50, "reverb_width": 0.80, 
        "chorus_mix": 0.15, "comp_ratio": 0.20, "comp_thresh": 0.55, "duck_intensity": 0.8, "saturation_amount": 0.15,
        "desc": (
            "<b>🌹 BOLERO (Trữ Tình - Sầu Lắng)</b>\n"
            "• <b>Tempo:</b> Chậm rãi (~85 BPM).\n"
            "• <b>Reverb:</b> Sâu &amp; Rộng (65% Room, 38% Wet) tạo chiều sâu sân khấu ảo.\n"
            "• <b>Delay:</b> Đuôi dài ấm áp (18% Volume, 15% Feedback, nhịp 1/2) hỗ trợ ngân hơi mượt mà.\n"
            "• <b>Đặc điểm:</b> Giọng ca hòa quyện đậm đà, rất nịnh giọng hát chậm, luyến láy."
        )
    },
    "dan_ca": {
        "name": "Dân ca / Ca cổ", 
        "emoji": "🎋", 
        "bpm_suggest": 100, 
        "color": "#27ae60", 
        "delay_fraction": 0.5, "delay_volume": 0.15, "delay_feedback": 0.10, 
        "reverb_room": 0.40, "reverb_wet": 0.35, "reverb_damp": 0.60, "reverb_width": 0.65, 
        "chorus_mix": 0.10, "comp_ratio": 0.22, "comp_thresh": 0.52, "duck_intensity": 0.6, "saturation_amount": 0.08,
        "desc": (
            "<b>🎋 DÂN CA / CA CỔ (Ngọt Ngào - Mộc Mạc)</b>\n"
            "• <b>Tempo:</b> Vừa phải (~100 BPM).\n"
            "• <b>Reverb:</b> Vừa tầm (40% Room, 35% Wet) bảo tồn sự tự nhiên mộc mạc của giọng ca.\n"
            "• <b>Delay:</b> Nhẹ dịu (15% Volume, 10% Feedback).\n"
            "• <b>Đặc điểm:</b> Khóa giọng theo <b>thang ngũ cung (Pentatonic)</b>, hạn chế Autotune mạnh (giới hạn depth 0.25) để tránh méo tiếng và giữ sự ngọt ngào truyền thống."
        )
    },
    "nhac_tre": {
        "name": "Nhạc trẻ", 
        "emoji": "🎤", 
        "bpm_suggest": 120, 
        "color": "#9b59b6", 
        "delay_fraction": 0.5, "delay_volume": 0.16, "delay_feedback": 0.12, 
        "reverb_room": 0.45, "reverb_wet": 0.32, "reverb_damp": 0.55, "reverb_width": 0.75, 
        "chorus_mix": 0.10, "comp_ratio": 0.30, "comp_thresh": 0.48, "duck_intensity": 1.0, "saturation_amount": 0.20,
        "desc": (
            "<b>🎤 NHẠC TRẺ (Pop/Ballad Hiện Đại)</b>\n"
            "• <b>Tempo:</b> Nhanh nhẹn (~120 BPM).\n"
            "• <b>Reverb:</b> Hiện đại, lung linh vừa đủ (45% Room, 32% Wet).\n"
            "• <b>Delay:</b> Đồng bộ nhịp (16% Volume, 12% Feedback).\n"
            "• <b>Đặc điểm:</b> Nén dynamic chặt (Ratio 0.30) kết hợp Autotune sắc nét để giọng hát bắt tai, hiện đại và nổi bật trên nền nhạc pop sôi động."
        )
    },
    "ballad": {
        "name": "Ballad", 
        "emoji": "💫", 
        "bpm_suggest": 75, 
        "color": "#2980b9", 
        "delay_fraction": 0.5, "delay_volume": 0.20, "delay_feedback": 0.18, 
        "reverb_room": 0.70, "reverb_wet": 0.42, "reverb_damp": 0.45, "reverb_width": 0.85, 
        "chorus_mix": 0.15, "comp_ratio": 0.18, "comp_thresh": 0.55, "duck_intensity": 0.9, "saturation_amount": 0.25,
        "desc": (
            "<b>💫 BALLAD (Bay Bổng - Cảm Xúc)</b>\n"
            "• <b>Tempo:</b> Chậm rãi (~75 BPM).\n"
            "• <b>Reverb:</b> Không gian rộng lớn (70% Room, 42% Wet) tạo cảm giác cực kỳ bay bổng, lung linh.\n"
            "• <b>Delay:</b> Sâu lắng (20% Volume, 18% Feedback) nâng đỡ các nốt cao ngâm dài.\n"
            "• <b>Đặc điểm:</b> Dành cho các bài hát tự sự cảm xúc, tôn giọng hát cao và ngân dài."
        )
    },
    "rap": {
        "name": "Rap", 
        "emoji": "🎧", 
        "bpm_suggest": 95, 
        "color": "#e67e22", 
        "delay_fraction": 0.25, "delay_volume": 0.08, "delay_feedback": 0.0, 
        "reverb_room": 0.20, "reverb_wet": 0.15, "reverb_damp": 0.70, "reverb_width": 0.50, 
        "chorus_mix": 0.0, "comp_ratio": 0.40, "comp_thresh": 0.42, "duck_intensity": 1.2, "saturation_amount": 0.35,
        "desc": (
            "<b>🎧 RAP (Khô Ráo - Rõ Lời - Sắc Nét)</b>\n"
            "• <b>Tempo:</b> Nhịp điệu dồn dập (~95 BPM).\n"
            "• <b>Reverb:</b> Rất ngắn &amp; Khô (20% Room, 15% Wet) để giữ nguyên chi tiết giọng đọc.\n"
            "• <b>Delay:</b> Hầu như không có (8% Volume, 0% Feedback).\n"
            "• <b>Đặc điểm:</b> Nén dynamic cực mạnh (Ratio 0.40) kết hợp ưu tiên dìm nhạc nền khi có tiếng nói (Ducking 1.2) giúp giọng hát đè lên beat rap sắc nét và uy lực."
        )
    },
    "dance": {
        "name": "Dance", 
        "emoji": "🪩", 
        "bpm_suggest": 128, 
        "color": "#1abc9c", 
        "delay_fraction": 0.5, "delay_volume": 0.12, "delay_feedback": 0.0, 
        "reverb_room": 0.25, "reverb_wet": 0.22, "reverb_damp": 0.65, "reverb_width": 0.70, 
        "chorus_mix": 0.15, "comp_ratio": 0.35, "comp_thresh": 0.45, "duck_intensity": 1.0, "saturation_amount": 0.30,
        "desc": (
            "<b>🪩 DANCE (Sôi Động - Điện Tử - Autotune Mạnh)</b>\n"
            "• <b>Tempo:</b> Rất nhanh (~128 BPM).\n"
            "• <b>Reverb:</b> Hạn chế tối đa (25% Room, 22% Wet) tránh gây đục tiếng trên beat nhanh.\n"
            "• <b>Delay:</b> Tắt nhanh (0% Feedback).\n"
            "• <b>Đặc điểm:</b> Autotune ở mức tối đa kết hợp Saturation (0.30) để tạo hiệu ứng giọng máy đặc trưng hòa vào nhạc điện tử vũ trường."
        )
    },
}

class KaraokeApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Karaoke AI Panel")
        self.set_border_width(10)
        self.set_default_size(320, 640)
        
        # Thiết lập: Luôn nổi trên cùng (Always on Top)
        self.set_keep_above(True)
        # Giữ nó cố định trên mọi workspaces
        self.stick()
        
        # Thiết lập biểu tượng (Icon) cho cửa sổ và Taskbar
        dir_path = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(dir_path, "karaoke_icon.png")
        if os.path.exists(icon_path):
            try:
                self.set_icon_from_file(icon_path)
            except Exception as e:
                print(f"Không thể nạp icon: {e}")
        
        # Tạo CSS tuỳ chỉnh (màu tối, bo góc)
        self.setup_css()

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.add(vbox)

        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        lbl = Gtk.Label(label="<span font='16' weight='bold' color='#a78bfa'>🎤 Chọn Thể Loại</span>", use_markup=True)
        lbl.set_hexpand(True)
        lbl.set_halign(Gtk.Align.START)
        header_box.pack_start(lbl, True, True, 0)
        
        settings_btn = Gtk.Button()
        settings_btn.get_style_context().add_class("settings-btn")
        settings_lbl = Gtk.Label(label="<span font='14'>⚙️</span>", use_markup=True)
        settings_btn.add(settings_lbl)
        settings_btn.connect("clicked", self.on_settings_clicked)
        header_box.pack_start(settings_btn, False, False, 0)
        
        vbox.pack_start(header_box, False, False, 0)
        
        # Lưới các nút bấm
        flowbox = Gtk.FlowBox()
        flowbox.set_valign(Gtk.Align.START)
        flowbox.set_max_children_per_line(2)
        flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        flowbox.set_row_spacing(10)
        flowbox.set_column_spacing(10)
        vbox.pack_start(flowbox, True, True, 0)

        self.buttons = {}
        
        # Init default genre file if missing
        if not os.path.exists(GENRE_FILE):
            self.save_genre("nhac_tre")

        current_saved = "nhac_tre"
        is_podcast = False
        autotune_enabled = True
        try:
            with open(GENRE_FILE, "r") as f:
                saved_data = json.load(f)
                current_saved = saved_data.get("genre", "nhac_tre")
                is_podcast = saved_data.get("force_podcast", False)
                autotune_enabled = saved_data.get("autotune_enabled", True)
        except: pass

        for key, p in PRESETS.items():
            btn = Gtk.Button()
            btn.get_style_context().add_class("genre-btn")
            btn.set_tooltip_markup(p["desc"])
            
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            emoji = Gtk.Label(label=f"<span font='24'>{p['emoji']}</span>", use_markup=True)
            name = Gtk.Label(label=f"<span font='11' weight='bold'>{p['name']}</span>", use_markup=True)
            box.pack_start(emoji, True, True, 0)
            box.pack_start(name, True, True, 0)
            
            btn.add(box)
            btn.connect("clicked", self.on_genre_clicked, key)
            
            if key == current_saved:
                btn.get_style_context().add_class("active-btn")
                
            self.buttons[key] = btn
            flowbox.insert(btn, -1)
            
        # BPM Section
        bpm_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bpm_lbl = Gtk.Label(label="<span font='10' color='#71717a'>BPM</span>", use_markup=True)
        bpm_box.pack_start(bpm_lbl, False, False, 0)
        
        self.bpm_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 60, 180, 1)
        self.bpm_scale.set_value(PRESETS.get(current_saved, PRESETS["nhac_tre"])["bpm_suggest"])
        self.bpm_scale.connect("value-changed", self.on_bpm_changed)
        bpm_box.pack_start(self.bpm_scale, True, True, 0)
        
        vbox.pack_start(bpm_box, False, False, 0)
        
        # Tone & AutoTune Section
        tone_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        tone_box.set_halign(Gtk.Align.CENTER)
        
        self.tone_lbl = Gtk.Label(label="<span font='11' weight='bold' color='#f39c12'>Tone: ---</span>", use_markup=True)
        tone_box.pack_start(self.tone_lbl, False, False, 10)
        
        at_lbl = Gtk.Label(label="<span font='10'>Auto-Tune</span>", use_markup=True)
        tone_box.pack_start(at_lbl, False, False, 0)
        
        self.autotune_toggle = Gtk.Switch()
        self.autotune_toggle.set_active(autotune_enabled)
        self.autotune_toggle.connect("notify::active", self.on_autotune_toggle)
        tone_box.pack_start(self.autotune_toggle, False, False, 0)
        
        vbox.pack_start(tone_box, False, False, 0)
        
        # Nút Phân tích giọng (Auto-Calibration)
        analyze_btn = Gtk.Button()
        analyze_btn.get_style_context().add_class("analyze-btn")
        analyze_lbl = Gtk.Label(label="<span font='11' weight='bold' color='#ffffff'>🎙️ Tự Động Phân Tích Giọng (5s)</span>", use_markup=True)
        analyze_btn.add(analyze_lbl)
        analyze_btn.connect("clicked", self.on_analyze_clicked)
        vbox.pack_start(analyze_btn, False, False, 0)
        
        # Nút Bật/Tắt chế độ MC / Podcast
        self.podcast_toggle = Gtk.Switch()
        self.podcast_toggle.set_active(is_podcast)
        self.podcast_toggle.connect("notify::active", self.on_podcast_toggle)
        
        toggle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        toggle_box.set_halign(Gtk.Align.CENTER)
        
        self.lbl_hat = Gtk.Label()
        self.lbl_podcast = Gtk.Label()
        
        toggle_box.pack_start(self.lbl_hat, False, False, 0)
        toggle_box.pack_start(self.podcast_toggle, False, False, 0)
        toggle_box.pack_start(self.lbl_podcast, False, False, 0)
        vbox.pack_start(toggle_box, False, False, 10)
        
        self.update_mode_labels(is_podcast) # Khởi tạo màu sắc ban đầu từ file lưu trữ
        
        # ═══ SOUNDBOARD SECTION (Livestream SFX) ═══
        sfx_title = Gtk.Label(label="<span font='10' weight='bold' color='#38bdf8'>🔊 Hiệu Ứng Âm Thanh Livestream</span>", use_markup=True)
        vbox.pack_start(sfx_title, False, False, 5)

        sfx_flow = Gtk.FlowBox()
        sfx_flow.set_valign(Gtk.Align.START)
        sfx_flow.set_max_children_per_line(3)
        sfx_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        sfx_flow.set_row_spacing(8)
        sfx_flow.set_column_spacing(8)
        vbox.pack_start(sfx_flow, False, False, 0)

        sfx_list = [
            ("Laughter 😆", "laughter.wav"),
            ("Applause 👏", "applause.wav"),
            ("Surprise 😮", "surprise.wav"),
            ("Booing 👎", "boo.wav"),
            ("ThumbsUp 👍", "thumbs_up.wav"),
            ("Airhorn 📣", "airhorn.wav"),
            ("Crickets 🦗", "crickets.wav"),
            ("Heart ❤️", "love.wav"),
            ("Message 💬", "message.wav")
        ]

        self.sfx_buttons = []
        for idx, (label, filename) in enumerate(sfx_list, 1):
            btn = Gtk.Button()
            btn.get_style_context().add_class("sfx-btn")
            
            grid = Gtk.Grid()
            grid.set_column_spacing(6)
            grid.set_valign(Gtk.Align.CENTER)
            
            num_lbl = Gtk.Label()
            num_lbl.set_markup(f"<span font='8' weight='bold' color='#00f0ff'>● {idx}</span>")
            num_lbl.set_halign(Gtk.Align.START)
            
            btn_lbl = Gtk.Label(label=f"<span font='9' weight='bold'>{label}</span>", use_markup=True)
            btn_lbl.set_halign(Gtk.Align.CENTER)
            btn_lbl.set_hexpand(True)
            
            grid.attach(num_lbl, 0, 0, 1, 1)
            grid.attach(btn_lbl, 1, 0, 1, 1)
            
            btn.add(grid)
            btn.connect("clicked", self.play_sfx, filename)
            sfx_flow.insert(btn, -1)
            self.sfx_buttons.append(btn)
            
        self.status_lbl = Gtk.Label(label="<span font='9' color='#71717a'>Sẵn sàng.</span>", use_markup=True)
        vbox.pack_start(self.status_lbl, False, False, 5)
        
        # Audio Connection Status
        conn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        conn_box.set_halign(Gtk.Align.CENTER)
        self.beat_conn_lbl = Gtk.Label(label="<span font='9'>🎵 Nhạc: Đang quét...</span>", use_markup=True)
        self.mic_conn_lbl = Gtk.Label(label="<span font='9'>🎤 Mic: Đang quét...</span>", use_markup=True)
        self.master_conn_lbl = Gtk.Label(label="<span font='9'>🎧 Master: Đang quét...</span>", use_markup=True)
        conn_box.pack_start(self.beat_conn_lbl, False, False, 0)
        conn_box.pack_start(self.mic_conn_lbl, False, False, 0)
        conn_box.pack_start(self.master_conn_lbl, False, False, 0)
        vbox.pack_start(conn_box, False, False, 10)

        # Biến cờ để tránh vòng lặp sự kiện (user kéo slider vs file update)
        self.user_sliding = False
        self.bpm_scale.connect("button-press-event", self.on_slider_press)
        self.bpm_scale.connect("button-release-event", self.on_slider_release)
        
        # Khởi chạy kiểm tra kết nối định kỳ
        GLib.timeout_add(2000, self.check_audio_connections)
        
        # Bắt đầu luồng kiểm tra BPM file tự động
        GLib.timeout_add(1000, self.check_bpm_file)
        
        # Khởi chạy kiểm tra Tone file định kỳ
        self.last_key_timestamp = 0
        GLib.timeout_add(500, self.check_key_file)
        
        # Kết nối sự kiện bàn phím cho 9 phím tắt SFX
        self.connect("key-press-event", self.on_key_press)

    def on_key_press(self, widget, event):
        keyval_name = Gdk.keyval_name(event.keyval)
        key_map = {
            '1': 0, 'KP_1': 0,
            '2': 1, 'KP_2': 1,
            '3': 2, 'KP_3': 2,
            '4': 3, 'KP_4': 3,
            '5': 4, 'KP_5': 4,
            '6': 5, 'KP_6': 5,
            '7': 6, 'KP_7': 6,
            '8': 7, 'KP_8': 7,
            '9': 8, 'KP_9': 8
        }
        if keyval_name in key_map:
            idx = key_map[keyval_name]
            if idx < len(self.sfx_buttons):
                btn = self.sfx_buttons[idx]
                btn.emit("clicked")
                return True
        return False

    def on_slider_press(self, widget, event):
        self.user_sliding = True
        return False

    def on_slider_release(self, widget, event):
        self.user_sliding = False
        return False
        
    def check_bpm_file(self):
        # Nếu người dùng đang tự tay kéo thanh trượt, không cập nhật tự động
        if self.user_sliding: return True
        try:
            with open(GENRE_FILE, "r") as f:
                data = json.load(f)
                if "bpm_override" in data:
                    new_bpm = float(data["bpm_override"])
                    if abs(self.bpm_scale.get_value() - new_bpm) > 1:
                        # Disable signals temporarily to avoid loop
                        self.bpm_scale.handler_block_by_func(self.on_bpm_changed)
                        self.bpm_scale.set_value(new_bpm)
                        self.bpm_scale.handler_unblock_by_func(self.on_bpm_changed)
        except: pass
        return True

    def check_key_file(self):
        try:
            with open(KEY_FILE, "r") as f:
                data = json.load(f)
                if "timestamp" in data and data["timestamp"] > self.last_key_timestamp:
                    self.last_key_timestamp = data["timestamp"]
                    note = data.get("root_name", "---")
                    scale = data.get("scale", "")
                    self.tone_lbl.set_markup(f"<span font='11' weight='bold' color='#f39c12'>Tone: {note} {scale}</span>")
        except: pass
        return True

    def check_audio_connections(self):
        try:
            import subprocess
            res = subprocess.run(["pw-link", "-l"], capture_output=True, text=True)
            lines = res.stdout.splitlines()
            
            has_beat = False
            has_mic = False
            has_master = False
            
            # Map of ports and their connections
            connections = {}
            current_src = ""
            for line in lines:
                if not line.startswith(" ") and not line.startswith("\t"):
                    current_src = line.strip()
                else:
                    dest = line.replace("|->", "").replace("|<-", "").strip()
                    if current_src:
                        if current_src not in connections:
                            connections[current_src] = []
                        connections[current_src].append(dest)
                        
            # Load selected sound devices
            sel_in = ""
            sel_out = ""
            try:
                with open(GENRE_FILE, "r") as f:
                    data = json.load(f)
                    sel_in = data.get("selected_input", "")
                    sel_out = data.get("selected_output", "")
            except: pass

            # Tìm các cổng của Mic_AI recorder
            mic_ai_ports = []
            try:
                res_i = subprocess.run(["pw-link", "-i"], capture_output=True, text=True, timeout=0.5)
                for line in res_i.stdout.splitlines():
                    line = line.strip()
                    if "mic_ai" in line.lower() or "pw-record" in line.lower() or "pw-cat" in line.lower():
                        if not any(x in line.lower() for x in ["beat_ai", "beat_ai_key", "master_ai"]):
                            mic_ai_ports.append(line)
            except: pass

            # Tự động kết nối & duy trì thiết bị đầu vào (Mic)
            if sel_in:
                capture_ports = []
                try:
                    res_o = subprocess.run(["pw-link", "-o"], capture_output=True, text=True, timeout=0.5)
                    capture_ports = [l.strip() for l in res_o.stdout.splitlines() if l.startswith(f"{sel_in}:")]
                except: pass
                
                if capture_ports:
                    target_map = {}
                    if len(capture_ports) == 1:
                        target_map[capture_ports[0]] = ["REAPER:in1", "REAPER:in2"] + mic_ai_ports
                    else:
                        target_map[capture_ports[0]] = ["REAPER:in1"] + mic_ai_ports
                        target_map[capture_ports[1]] = ["REAPER:in2"]
                        
                    for src_port, dests in target_map.items():
                        active_conns = connections.get(src_port, [])
                        for target_dest in dests:
                            if target_dest not in active_conns:
                                subprocess.run(["pw-link", src_port, target_dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                
                # Ngắt kết nối của các thiết bị đầu vào khác đang nối tới REAPER và mic_ai_ports
                for src_port, active_conns in list(connections.items()):
                    if src_port.startswith("alsa_input.") and not src_port.startswith(f"{sel_in}:"):
                        for dest in active_conns:
                            if dest in ["REAPER:in1", "REAPER:in2"] or dest in mic_ai_ports:
                                subprocess.run(["pw-link", "-d", src_port, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Tự động kết nối & duy trì thiết bị đầu ra (Speaker / Interface Out)
            if sel_out:
                playback_ports = []
                try:
                    res_play = subprocess.run(["pw-link", "-i"], capture_output=True, text=True, timeout=0.5)
                    playback_ports = [l.strip() for l in res_play.stdout.splitlines() if l.startswith(f"{sel_out}:")]
                except: pass
                
                if playback_ports:
                    target_map = {}
                    if len(playback_ports) == 1:
                        target_map["REAPER:out1"] = [playback_ports[0]]
                        target_map["REAPER:out2"] = [playback_ports[0]]
                    else:
                        target_map["REAPER:out1"] = [playback_ports[0]]
                        target_map["REAPER:out2"] = [playback_ports[1]]
                        
                    for src_port, dests in target_map.items():
                        active_conns = connections.get(src_port, [])
                        for target_dest in dests:
                            if target_dest not in active_conns:
                                subprocess.run(["pw-link", src_port, target_dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                
                # Ngắt kết nối của REAPER tới các thiết bị đầu ra khác
                for src_port, active_conns in list(connections.items()):
                    if src_port in ["REAPER:out1", "REAPER:out2"]:
                        for dest in active_conns:
                            if dest.startswith("alsa_output.") and not dest.startswith(f"{sel_out}:"):
                                subprocess.run(["pw-link", "-d", src_port, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Analyze connection states for UI indicators
            for src, dests in connections.items():
                src_lower = src.lower()
                for dest in dests:
                    dest_lower = dest.lower()
                    if "pw-record" in dest_lower or "beat_ai" in dest_lower or "mic_ai" in dest_lower or "master_ai" in dest_lower:
                        if "chrome" in src_lower or "firefox" in src_lower or "brave" in src_lower or "opera" in src_lower or "edge" in src_lower:
                            has_beat = True
                        if "alsa_input" in src_lower and "capture" in src_lower:
                            if sel_in:
                                if sel_in in src:
                                    has_mic = True
                            else:
                                has_mic = True
                        if "reaper" in src_lower and "out" in src_lower:
                            if sel_out:
                                if sel_out in dest:
                                    has_master = True
                            else:
                                has_master = True
            
            # Auto-route and isolate Browser to REAPER (prevent dual playback to system speakers)
            browser_ports = []
            for port in connections.keys():
                if any(x in port.lower() for x in ["firefox", "chrom", "brave", "opera", "edge", "vivaldi"]):
                    browser_ports.append(port)
                    
            if browser_ports:
                browser_ports.sort()
                for idx, bp in enumerate(browser_ports):
                    reaper_dest = "REAPER:in3" if (idx % 2 == 0) else "REAPER:in4"
                    bp_conns = connections.get(bp, [])
                    
                    # Connect to REAPER if missing
                    if reaper_dest not in bp_conns:
                        subprocess.run(["pw-link", bp, reaper_dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
                    # Disconnect from non-REAPER, non-AI destinations to prevent double audio (echo) through speakers
                    for dest in bp_conns:
                        if "REAPER" not in dest and "beat_ai" not in dest.lower() and "pw-record" not in dest.lower() and "beat_ai_key" not in dest.lower():
                            subprocess.run(["pw-link", "-d", bp, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            
            if has_beat:
                self.beat_conn_lbl.set_markup("<span font='9' color='#2ecc71'>🎵 Nhạc: Đã nối</span>")
            else:
                self.beat_conn_lbl.set_markup("<span font='9' color='#e74c3c'>🎵 Nhạc: Chưa có web</span>")
                
            if has_mic:
                self.mic_conn_lbl.set_markup("<span font='9' color='#2ecc71'>🎤 Mic: Đã nối</span>")
            else:
                self.mic_conn_lbl.set_markup("<span font='9' color='#e74c3c'>🎤 Mic: Chưa nối AI</span>")
                
            if has_master:
                # Kiểm tra trạng thái Master Clip
                master_status = "Đã nối"
                master_color = "#2ecc71"
                try:
                    with open("/tmp/ai_karaoke_master_status.txt", "r") as f:
                        if "OVERLOAD" in f.read():
                            master_status = "QUÁ TẢI!"
                            master_color = "#e74c3c"
                except: pass
                self.master_conn_lbl.set_markup(f"<span font='9' color='{master_color}'>🎧 Master: {master_status}</span>")
            else:
                self.master_conn_lbl.set_markup("<span font='9' color='#e74c3c'>🎧 Master: Chưa nối AI</span>")
                
        except: pass
        return True

    def setup_css(self):
        css = b"""
        window { background-color: #121218; }
        .genre-btn {
            background-color: #1f1f28;
            border-radius: 12px;
            border: 1px solid #333340;
            padding: 10px;
            color: #e4e4e7;
            transition: all 0.2s ease;
        }
        .genre-btn:hover { background-color: #2d2d3b; border-color: #a78bfa; }
        .active-btn {
            background-color: #3b2a5c;
            border: 2px solid #a78bfa;
            color: white;
        }
        .analyze-btn {
            background-color: #e67e22;
            border-radius: 8px;
            padding: 8px;
            transition: all 0.2s ease;
        }
        .analyze-btn:hover { background-color: #d35400; }
        .sfx-btn {
            background-color: #1a1a24;
            border-radius: 10px;
            border: 1px solid #2d2d3d;
            padding: 8px;
            color: #cbd5e1;
            transition: all 0.2s ease;
        }
        .sfx-btn:hover {
            background-color: #2e2e3e;
            border-color: #38bdf8;
            color: #ffffff;
        }
        .settings-btn {
            background-color: transparent;
            border: none;
            color: #a78bfa;
            padding: 4px;
            transition: all 0.2s ease;
        }
        .settings-btn:hover {
            color: #c084fc;
        }
        .settings-dialog {
            background-color: #121218;
            color: #cbd5e1;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_analyze_clicked(self, widget):
        self.status_lbl.set_markup("<span font='9' color='#f1c40f'>Đang thu âm &amp; phân tích (5s)... Hãy hát vào mic!</span>")
        # Run background script
        import subprocess
        dir_path = os.path.dirname(os.path.realpath(__file__))
        subprocess.Popen(["python3", os.path.join(dir_path, "auto_calibrate.py")])
        # Reset text after 6 seconds
        GLib.timeout_add(6000, lambda: self.status_lbl.set_markup("<span font='9' color='#2ecc71'>Đã tinh chỉnh EQ &amp; Reverb theo giọng bạn!</span>") or False)

    def save_genre(self, key):
        p = PRESETS.get(key, PRESETS["nhac_tre"])
        
        # Đọc dữ liệu cũ để giữ lại các cờ trạng thái quan trọng
        try:
            with open(GENRE_FILE, "r") as f: old_data = json.load(f)
        except: old_data = {}
        
        # Lưu toàn bộ thuộc tính của preset vào JSON để AI đọc được
        data = p.copy()
        data["genre"] = key
        data["timestamp"] = time.time()
        
        # Phục hồi các trạng thái đang chạy thực tế
        if "force_podcast" in old_data:
            data["force_podcast"] = old_data["force_podcast"]
        if "is_music_playing" in old_data:
            data["is_music_playing"] = old_data["is_music_playing"]
        if "bpm_override" in old_data:
            data["bpm_override"] = old_data["bpm_override"]
        else:
            data["bpm_override"] = p["bpm_suggest"]
            
        if "autotune_enabled" in old_data:
            data["autotune_enabled"] = old_data["autotune_enabled"]
            # Restore toggle state without triggering event
            self.autotune_toggle.handler_block_by_func(self.on_autotune_toggle)
            self.autotune_toggle.set_active(old_data["autotune_enabled"])
            self.autotune_toggle.handler_unblock_by_func(self.on_autotune_toggle)
        else:
            data["autotune_enabled"] = True
            
        try:
            with open(GENRE_FILE, "w") as f:
                json.dump(data, f)
        except: pass   
    def on_genre_clicked(self, widget, key):
        # Update styling
        for k, btn in self.buttons.items():
            btn.get_style_context().remove_class("active-btn")
        widget.get_style_context().add_class("active-btn")
        
        # Save genre
        self.save_genre(key)
        
        # NOTE: Không gọi self.bpm_scale.set_value() ở đây nữa
        # Để cho hàm check_bpm_file() tự động đồng bộ slider với BPM thật từ realtime_bpm_ai.py
            
    def on_bpm_changed(self, widget):
        if not self.user_sliding: return
        bpm = widget.get_value()
        try:
            with open(GENRE_FILE, "r") as f: data = json.load(f)
        except: data = {}
        data["bpm_override"] = bpm
        data["timestamp"] = time.time()
        with open(GENRE_FILE, "w") as f:
            json.dump(data, f)
            
    def update_mode_labels(self, is_podcast):
        if is_podcast:
            self.lbl_hat.set_markup("<span font='10' weight='bold' color='#52525b'>○ HÁT (TẮT)</span>")
            self.lbl_podcast.set_markup("<span font='10' weight='bold' color='#2ecc71'>● 🎙️ PODCAST (BẬT)</span>")
        else:
            self.lbl_hat.set_markup("<span font='10' weight='bold' color='#38bdf8'>● 🎤 HÁT (BẬT)</span>")
            self.lbl_podcast.set_markup("<span font='10' weight='bold' color='#52525b'>○ PODCAST (TẮT)</span>")

    def on_autotune_toggle(self, switch, gparam):
        is_active = switch.get_active()
        try:
            with open(GENRE_FILE, "r") as f: data = json.load(f)
        except: data = {}
        data["autotune_enabled"] = is_active
        data["timestamp"] = time.time()
        with open(GENRE_FILE, "w") as f:
            json.dump(data, f)

    def on_podcast_toggle(self, switch, gparam):
        is_podcast = switch.get_active()
        try:
            with open(GENRE_FILE, "r") as f: data = json.load(f)
        except: data = {}
        data["force_podcast"] = is_podcast
        data["timestamp"] = time.time()
        with open(GENRE_FILE, "w") as f:
            json.dump(data, f)
            
        self.update_mode_labels(is_podcast)
        # Reset lại status về Sẵn sàng để xóa đi dòng chữ báo trạng thái dài dòng
        self.status_lbl.set_markup("<span font='9' color='#71717a'>Sẵn sàng.</span>")

    def play_sfx(self, widget, filename):
        import subprocess
        import threading
        dir_path = os.path.dirname(os.path.realpath(__file__))
        filepath = os.path.join(dir_path, "sounds", filename)
        if os.path.exists(filepath):
            node_name = f"sfx_play_{int(time.time() * 1000)}"
            cmd = ["pw-play", "-P", f"{{ node.name = {node_name} }}", "--target", "0", filepath]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            def link_thread():
                start_time = time.time()
                while time.time() - start_time < 1.0:
                    try:
                        res = subprocess.run(["pw-link", "-o"], capture_output=True, text=True, timeout=0.5)
                        lines = res.stdout.splitlines()
                        matching_ports = [l.strip() for l in lines if node_name in l]
                        if matching_ports:
                            for port in matching_ports:
                                subprocess.run(["pw-link", port, "REAPER:in3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                subprocess.run(["pw-link", port, "REAPER:in4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            break
                    except:
                        pass
                    time.sleep(0.02)
            
            threading.Thread(target=link_thread, daemon=True).start()
            self.status_lbl.set_markup(f"<span font='9' color='#38bdf8'>🔊 Đang phát hiệu ứng: {filename}</span>")
            GLib.timeout_add(3000, lambda: self.status_lbl.set_markup("<span font='9' color='#71717a'>Sẵn sàng.</span>") or False)
        else:
            self.status_lbl.set_markup(f"<span font='9' color='#e74c3c'>⚠️ Lỗi: Không thấy file {filename}</span>")

    def get_audio_interfaces(self):
        import subprocess
        inputs = []
        outputs = []
        
        # Scan inputs (from pw-link -o)
        try:
            res = subprocess.run(["pw-link", "-o"], capture_output=True, text=True, timeout=1.0)
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.startswith("alsa_input."):
                    dev_id = line.split(":")[0]
                    if dev_id not in inputs:
                        inputs.append(dev_id)
        except: pass
            
        # Scan outputs (from pw-link -i)
        try:
            res = subprocess.run(["pw-link", "-i"], capture_output=True, text=True, timeout=1.0)
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.startswith("alsa_output."):
                    dev_id = line.split(":")[0]
                    if dev_id not in outputs:
                        outputs.append(dev_id)
        except: pass
            
        return inputs, outputs

    def get_device_friendly_name(self, dev_id):
        # Remove prefix
        clean = dev_id
        for prefix in ["alsa_input.", "alsa_output."]:
            if clean.startswith(prefix):
                clean = clean[len(prefix):]
                
        # Simplify known hardware strings
        clean = clean.replace("usb-", "").replace("pci-", "")
        parts = clean.replace(".", "_").replace("-", "_").split("_")
        
        filtered_parts = []
        for p in parts:
            if not p: continue
            if len(p) > 6 and any(c.isdigit() for c in p):
                continue
            if p.lower() in ["analog", "stereo", "hdmi", "digital", "sound", "devices", "capture", "playback"]:
                continue
            filtered_parts.append(p.capitalize())
            
        name = " ".join(filtered_parts)
        if not name:
            name = "Thiết bị mặc định"
            
        suffix = ""
        if "analog-stereo" in dev_id:
            suffix = " (Analog Stereo)"
        elif "hdmi-stereo" in dev_id:
            suffix = " (HDMI)"
            
        if dev_id.startswith("alsa_input"):
            return f"🎙️ {name}{suffix}"
        else:
            return f"🔊 {name}{suffix}"

    def on_settings_clicked(self, widget):
        dialog = Gtk.Dialog(
            title="Cấu Hình Thiết Bị Âm Thanh", 
            parent=self, 
            flags=0,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        )
        dialog.set_default_size(320, 200)
        dialog.get_style_context().add_class("settings-dialog")
        
        content_area = dialog.get_content_area()
        content_area.set_spacing(15)
        content_area.set_border_width(15)
        
        inputs, outputs = self.get_audio_interfaces()
        
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(15)
        
        # Input device
        lbl_in = Gtk.Label(label="<b>🎙️ Thiết bị Mic vào:</b>", use_markup=True)
        lbl_in.set_halign(Gtk.Align.START)
        grid.attach(lbl_in, 0, 0, 1, 1)
        
        combo_in = Gtk.ComboBoxText()
        combo_in.append_text("Không thay đổi (Giữ nguyên)")
        active_in_idx = 0
        
        saved_in = ""
        saved_out = ""
        try:
            with open(GENRE_FILE, "r") as f:
                data = json.load(f)
                saved_in = data.get("selected_input", "")
                saved_out = data.get("selected_output", "")
        except: pass
        
        for idx, dev in enumerate(inputs, 1):
            friendly = self.get_device_friendly_name(dev)
            combo_in.append_text(friendly)
            if dev == saved_in:
                active_in_idx = idx
                
        combo_in.set_active(active_in_idx)
        grid.attach(combo_in, 1, 0, 1, 1)
        
        # Output device
        lbl_out = Gtk.Label(label="<b>🔊 Thiết bị Loa ra:</b>", use_markup=True)
        lbl_out.set_halign(Gtk.Align.START)
        grid.attach(lbl_out, 0, 1, 1, 1)
        
        combo_out = Gtk.ComboBoxText()
        combo_out.append_text("Không thay đổi (Giữ nguyên)")
        active_out_idx = 0
        
        for idx, dev in enumerate(outputs, 1):
            friendly = self.get_device_friendly_name(dev)
            combo_out.append_text(friendly)
            if dev == saved_out:
                active_out_idx = idx
                
        combo_out.set_active(active_out_idx)
        grid.attach(combo_out, 1, 1, 1, 1)
        
        content_area.add(grid)
        dialog.show_all()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            sel_in_idx = combo_in.get_active()
            sel_out_idx = combo_out.get_active()
            
            new_in = inputs[sel_in_idx - 1] if sel_in_idx > 0 else ""
            new_out = outputs[sel_out_idx - 1] if sel_out_idx > 0 else ""
            
            try:
                with open(GENRE_FILE, "r") as f: data = json.load(f)
            except: data = {}
            
            data["selected_input"] = new_in
            data["selected_output"] = new_out
            data["timestamp"] = time.time()
            with open(GENRE_FILE, "w") as f:
                json.dump(data, f)
                
            self.check_audio_connections()
            self.status_lbl.set_markup("<span font='9' color='#2ecc71'>Đã áp dụng cấu hình thiết bị âm thanh!</span>")
            GLib.timeout_add(3000, lambda: self.status_lbl.set_markup("<span font='9' color='#71717a'>Sẵn sàng.</span>") or False)
            
        dialog.destroy()

def create_desktop_launcher():
    try:
        home = os.path.expanduser("~")
        desktop_dir = os.path.join(home, ".local", "share", "applications")
        os.makedirs(desktop_dir, exist_ok=True)
        
        dir_path = os.path.dirname(os.path.realpath(__file__))
        app_path = os.path.join(dir_path, "karaoke_app.py")
        icon_path = os.path.join(dir_path, "karaoke_icon.png")
        desktop_file = os.path.join(desktop_dir, "karaoke-ai-panel.desktop")
        
        content = f"""[Desktop Entry]
Type=Application
Name=Karaoke AI Panel
Comment=AI Karaoke Control Panel for REAPER
Exec=python3 {app_path}
Icon={icon_path}
Terminal=false
Categories=AudioVideo;Audio;
StartupWMClass=karaoke-ai-panel
"""
        with open(desktop_file, "w") as f:
            f.write(content)
        os.chmod(desktop_file, 0o755)
    except Exception as e:
        print(f"Không thể tạo .desktop launcher: {e}")

if __name__ == '__main__':
    create_desktop_launcher()
    GLib.set_prgname('karaoke-ai-panel')
    GLib.set_application_name('Karaoke AI Panel')
    win = KaraokeApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
