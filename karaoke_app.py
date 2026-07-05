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

PRESETS = {
    "bolero": {"name": "Bolero", "emoji": "🌹", "bpm_suggest": 85, "color": "#e74c3c", "delay_fraction": 0.5, "delay_volume": 0.18, "delay_feedback": 0.15, "reverb_room": 0.65, "reverb_wet": 0.38, "reverb_damp": 0.50, "reverb_width": 0.80, "chorus_mix": 0.15, "comp_ratio": 0.20, "comp_thresh": 0.55, "duck_intensity": 0.8},
    "dan_ca": {"name": "Dân ca", "emoji": "🎋", "bpm_suggest": 100, "color": "#27ae60", "delay_fraction": 0.5, "delay_volume": 0.15, "delay_feedback": 0.10, "reverb_room": 0.40, "reverb_wet": 0.35, "reverb_damp": 0.60, "reverb_width": 0.65, "chorus_mix": 0.10, "comp_ratio": 0.22, "comp_thresh": 0.52, "duck_intensity": 0.6},
    "nhac_tre": {"name": "Nhạc trẻ", "emoji": "🎤", "bpm_suggest": 120, "color": "#9b59b6", "delay_fraction": 0.5, "delay_volume": 0.16, "delay_feedback": 0.12, "reverb_room": 0.45, "reverb_wet": 0.32, "reverb_damp": 0.55, "reverb_width": 0.75, "chorus_mix": 0.10, "comp_ratio": 0.30, "comp_thresh": 0.48, "duck_intensity": 1.0},
    "ballad": {"name": "Ballad", "emoji": "💫", "bpm_suggest": 75, "color": "#2980b9", "delay_fraction": 0.5, "delay_volume": 0.20, "delay_feedback": 0.18, "reverb_room": 0.70, "reverb_wet": 0.42, "reverb_damp": 0.45, "reverb_width": 0.85, "chorus_mix": 0.15, "comp_ratio": 0.18, "comp_thresh": 0.55, "duck_intensity": 0.9},
    "rap": {"name": "Rap", "emoji": "🎧", "bpm_suggest": 95, "color": "#e67e22", "delay_fraction": 0.25, "delay_volume": 0.08, "delay_feedback": 0.0, "reverb_room": 0.20, "reverb_wet": 0.15, "reverb_damp": 0.70, "reverb_width": 0.50, "chorus_mix": 0.0, "comp_ratio": 0.40, "comp_thresh": 0.42, "duck_intensity": 1.2},
    "dance": {"name": "Dance", "emoji": "🪩", "bpm_suggest": 128, "color": "#1abc9c", "delay_fraction": 0.5, "delay_volume": 0.12, "delay_feedback": 0.0, "reverb_room": 0.25, "reverb_wet": 0.22, "reverb_damp": 0.65, "reverb_width": 0.70, "chorus_mix": 0.15, "comp_ratio": 0.35, "comp_thresh": 0.45, "duck_intensity": 1.0},
}

class KaraokeApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Karaoke AI Panel")
        self.set_border_width(10)
        self.set_default_size(300, 400)
        
        # Thiết lập: Luôn nổi trên cùng (Always on Top)
        self.set_keep_above(True)
        # Giữ nó cố định trên mọi workspaces
        self.stick()
        
        # Tạo CSS tuỳ chỉnh (màu tối, bo góc)
        self.setup_css()

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.add(vbox)

        # Header
        lbl = Gtk.Label(label="<span font='16' weight='bold' color='#a78bfa'>🎤 Chọn Thể Loại</span>", use_markup=True)
        vbox.pack_start(lbl, False, False, 0)
        
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
        try:
            with open(GENRE_FILE, "r") as f:
                current_saved = json.load(f).get("genre", "nhac_tre")
        except: pass

        for key, p in PRESETS.items():
            btn = Gtk.Button()
            btn.get_style_context().add_class("genre-btn")
            
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
        
        # Nút Phân tích giọng (Auto-Calibration)
        analyze_btn = Gtk.Button()
        analyze_btn.get_style_context().add_class("analyze-btn")
        analyze_lbl = Gtk.Label(label="<span font='11' weight='bold' color='#ffffff'>🎙️ Tự Động Phân Tích Giọng (5s)</span>", use_markup=True)
        analyze_btn.add(analyze_lbl)
        analyze_btn.connect("clicked", self.on_analyze_clicked)
        vbox.pack_start(analyze_btn, False, False, 0)
        
        # Nút Bật/Tắt chế độ MC / Podcast
        self.podcast_toggle = Gtk.Switch()
        self.podcast_toggle.set_active(False)
        self.podcast_toggle.connect("notify::active", self.on_podcast_toggle)
        
        toggle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toggle_box.pack_start(Gtk.Label(label="<span font='10' color='#71717a'>Chế độ Livestream / MC (Giọng ấm, tắt Vang)</span>", use_markup=True), False, False, 0)
        toggle_box.pack_start(self.podcast_toggle, False, False, 0)
        vbox.pack_start(toggle_box, False, False, 0)
        
        self.status_lbl = Gtk.Label(label="<span font='9' color='#71717a'>Sẵn sàng.</span>", use_markup=True)
        vbox.pack_start(self.status_lbl, False, False, 0)
        
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

    def check_audio_connections(self):
        try:
            import subprocess
            res = subprocess.run(["pw-link", "-l"], capture_output=True, text=True)
            lines = res.stdout.splitlines()
            
            has_beat = False
            has_mic = False
            has_master = False
            
            current_src = ""
            for line in lines:
                if not line.startswith(" ") and not line.startswith("\t"):
                    current_src = line.lower()
                else:
                    line_lower = line.lower()
                    if "pw-record" in line_lower or "beat_ai" in line_lower or "mic_ai" in line_lower or "master_ai" in line_lower:
                        if "chrome" in current_src or "firefox" in current_src:
                            has_beat = True
                        if "alsa_input" in current_src and "capture" in current_src:
                            has_mic = True
                        if "reaper" in current_src and "out" in current_src:
                            has_master = True
                            
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
            
    def on_podcast_toggle(self, switch, gparam):
        try:
            with open(GENRE_FILE, "r") as f: data = json.load(f)
        except: data = {}
        data["force_podcast"] = switch.get_active()
        data["timestamp"] = time.time()
        with open(GENRE_FILE, "w") as f:
            json.dump(data, f)
            
        status = "BẬT" if switch.get_active() else "TẮT"
        self.status_lbl.set_markup(f"<span font='9' color='#00ff00'>Chế độ Livestream / Podcast: {status}</span>")
if __name__ == '__main__':
    win = KaraokeApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
