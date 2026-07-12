#!/usr/bin/env python3
"""
🎤 Karaoke Control Panel — Floating Desktop App (GTK3)
======================================================
Ứng dụng nổi (Always on top) để chọn thể loại khi đang hát.
"""
import gi, json, os, time, subprocess
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

GENRE_FILE = "/tmp/ai_karaoke_genre.json"
BPM_FILE = "/tmp/ai_karaoke_bpm.txt"
KEY_FILE = "/tmp/ai_karaoke_key.json"

# --- CẤU HÌNH CỔNG REAPER ---
# Mặc định: Vocal dùng in3/in4, Nhạc nền dùng in1/in2
REAPER_VOCAL_IN_L = "REAPER:in3"
REAPER_VOCAL_IN_R = "REAPER:in4"
REAPER_MUSIC_IN_L = "REAPER:in1"
REAPER_MUSIC_IN_R = "REAPER:in2"

# Thử đọc cấu hình từ file .env nếu có
try:
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k == "REAPER_VOCAL_IN_L": REAPER_VOCAL_IN_L = v
                        elif k == "REAPER_VOCAL_IN_R": REAPER_VOCAL_IN_R = v
                        elif k == "REAPER_MUSIC_IN_L": REAPER_MUSIC_IN_L = v
                        elif k == "REAPER_MUSIC_IN_R": REAPER_MUSIC_IN_R = v
except Exception as e:
    print(f"Lỗi đọc cấu hình cổng từ .env: {e}")

PRESETS = {
    "bolero": {
        "name": "Bolero", 
        "emoji": "🌹", 
        "bpm_suggest": 85, 
        "color": "#e74c3c", 
        "delay_fraction": 0.5, "delay_volume": 0.12, "delay_feedback": 0.20, 
        "reverb_room": 0.42, "reverb_wet": 0.52, "reverb_damp": 0.25, "reverb_width": 1.00, 
        "chorus_mix": 0.20, "comp_ratio": 0.025, "comp_thresh": 0.030, "duck_intensity": 0.8, "saturation_amount": 0.15,
        "desc": (
            "<b>🌹 BOLERO (Trữ Tình - Sâu Lắng - Vang Sáng Mịn)</b>\n"
            "• <b>Vang Reverb:</b> Cực sâu &amp; Đuôi sáng mịn (82% Room, 52% Wet, Damp 15%) giúp nâng đỡ giọng hát ngân ngọt ngào.\n"
            "• <b>Màu sắc:</b> Chorus 20% mượt mà, Saturation 15% cho chất giọng trữ tình mộc mạc."
        )
    },
    "dan_ca": {
        "name": "Dân ca / Ca cổ", 
        "emoji": "🎋", 
        "bpm_suggest": 100, 
        "color": "#27ae60", 
        "delay_fraction": 0.5, "delay_volume": 0.10, "delay_feedback": 0.15, 
        "reverb_room": 0.38, "reverb_wet": 0.46, "reverb_damp": 0.30, "reverb_width": 0.95, 
        "chorus_mix": 0.12, "comp_ratio": 0.025, "comp_thresh": 0.030, "duck_intensity": 0.6, "saturation_amount": 0.15,
        "desc": (
            "<b>🎋 DÂN CA / CA CỔ (Ngọt Ngào - Mộc Mạc - Bay Bổng)</b>\n"
            "• <b>Vang Reverb:</b> Không gian rộng mở tự nhiên (75% Room, 46% Wet, Damp 20%) tạo độ bay mà vẫn mộc mạc.\n"
            "• <b>Màu sắc:</b> Thang âm ngũ cung hạn chế autotune méo tiếng, giữ sự ngọt ngào truyền thống."
        )
    },
    "nhac_tre": {
        "name": "Nhạc trẻ", 
        "emoji": "🎤", 
        "bpm_suggest": 120, 
        "color": "#9b59b6", 
        "delay_fraction": 0.5, "delay_volume": 0.12, "delay_feedback": 0.20, 
        "reverb_room": 0.40, "reverb_wet": 0.48, "reverb_damp": 0.28, "reverb_width": 0.95, 
        "chorus_mix": 0.15, "comp_ratio": 0.025, "comp_thresh": 0.030, "duck_intensity": 1.0, "saturation_amount": 0.20,
        "desc": (
            "<b>🎤 NHẠC TRẺ (Pop/Ballad Hiện Đại - Lung Linh)</b>\n"
            "• <b>Vang Reverb:</b> Hiện đại, đuôi vang lấp lánh (78% Room, 48% Wet, Damp 15%) cho giọng hát bắt tai, cuốn hút.\n"
            "• <b>Màu sắc:</b> Autotune nhạy bén kết hợp độ bóng bẩy nhẹ nhàng nổi bật trên nền beat."
        )
    },
    "ballad": {
        "name": "Ballad", 
        "emoji": "💫", 
        "bpm_suggest": 75, 
        "color": "#2980b9", 
        "delay_fraction": 0.5, "delay_volume": 0.18, "delay_feedback": 0.30, 
        "reverb_room": 0.45, "reverb_wet": 0.55, "reverb_damp": 0.22, "reverb_width": 1.00, 
        "chorus_mix": 0.26, "comp_ratio": 0.025, "comp_thresh": 0.030, "duck_intensity": 0.9, "saturation_amount": 0.32,
        "desc": (
            "<b>💫 BALLAD (Bay Bổng - Siêu Mượt Mà - Màu Sắc Pro)</b>\n"
            "• <b>Vang Reverb:</b> Không gian siêu rộng, ẩm mịn quyện giọng (85% Room, 58% Wet, Damp 10%) giúp hát nhẹ nhõm không tốn sức.\n"
            "• <b>Màu sắc:</b> Chorus 26% lộng lẫy pha lê, Saturation 32% dày dặn âm sắc analog."
        )
    },
    "rap": {
        "name": "Rap", 
        "emoji": "🎧", 
        "bpm_suggest": 95, 
        "color": "#e67e22", 
        "delay_fraction": 0.25, "delay_volume": 0.08, "delay_feedback": 0.08, 
        "reverb_room": 0.30, "reverb_wet": 0.30, "reverb_damp": 0.35, "reverb_width": 0.85, 
        "chorus_mix": 0.12, "comp_ratio": 0.025, "comp_thresh": 0.030, "duck_intensity": 1.2, "saturation_amount": 0.35,
        "desc": (
            "<b>🎧 RAP (Hiện Đại - Rõ Lời - Độ Sâu Tốt)</b>\n"
            "• <b>Vang Reverb:</b> Không gian phòng vừa phải, rất trong trẻo (58% Room, 30% Wet, Damp 25%) giữ độ nét ca từ.\n"
            "• <b>Màu sắc:</b> Hài âm saturation 35% ấm dày, nén chặt để vocal đè lên beat rap uy lực."
        )
    },
    "dance": {
        "name": "Dance", 
        "emoji": "🪩", 
        "bpm_suggest": 128, 
        "color": "#1abc9c", 
        "delay_fraction": 0.5, "delay_volume": 0.12, "delay_feedback": 0.15, 
        "reverb_room": 0.35, "reverb_wet": 0.40, "reverb_damp": 0.30, "reverb_width": 0.90, 
        "chorus_mix": 0.18, "comp_ratio": 0.025, "comp_thresh": 0.030, "duck_intensity": 1.0, "saturation_amount": 0.30,
        "desc": (
            "<b>🪩 DANCE (Sôi Động - Điện Tử - Bay Bổng)</b>\n"
            "• <b>Vang Reverb:</b> Vang năng động sáng rõ (65% Room, 40% Wet, Damp 20%) tránh đục tiếng trên beat nhanh.\n"
            "• <b>Màu sắc:</b> Autotune mạnh kết hợp Saturation 30% tạo giọng máy đặc trưng hòa vào beat."
        )
    },
    "khong_gian_ok": {
        "name": "Không Gian OK", 
        "emoji": "🌊", 
        "bpm_suggest": 87, 
        "color": "#16a085", 
        "delay_fraction": 0.5, "delay_volume": 0.22, "delay_feedback": 0.25, 
        "reverb_room": 0.40, "reverb_wet": 0.50, "reverb_damp": 0.28, "reverb_width": 1.00, 
        "chorus_mix": 0.25, "comp_ratio": 0.025, "comp_thresh": 0.030, "duck_intensity": 0.9, "saturation_amount": 0.15,
        "desc": (
            "<b>🌊 KHÔNG GIAN OK (Mượt Mà - Long Lanh - Màu Sắc Pro)</b>\n"
            "• <b>Vang Reverb:</b> Vang rộng &amp; Ẩm mượt (Room 80%, Wet 55%, Damp 20%) tạo độ mịn màng nâng đỡ hơi hát cực tốt.\n"
            "• <b>Màu sắc:</b> Chorus rộng 25% phủ bóng pha lê, Saturation 15% sạch sẽ, trong trẻo."
        )
    },
}

class KaraokeApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Karaoke AI Panel")
        self.set_border_width(10)
        self.set_default_size(360, 1)
        self.set_size_request(360, -1) # Khóa bề ngang tối thiểu để vừa 3 cột nút SFX
        
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

        # Sử dụng Notebook để chia Tab
        self.notebook = Gtk.Notebook()
        self.add(self.notebook)
        
        # --- TAB 1: TRÌNH DIỄN ---
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.notebook.append_page(vbox, Gtk.Label(label="🎤 Trình Diễn"))
        
        # --- TAB 2: KỸ SƯ ÂM THANH ---
        try:
            from studio_tab import StudioTab
            self.studio_tab = StudioTab(self)
            self.notebook.append_page(self.studio_tab, Gtk.Label(label="🎓 Studio (Tutor)"))
        except Exception as e:
            print(f"Lỗi nạp Studio Tab: {e}")

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
        vbox.pack_start(flowbox, False, False, 0)

        self.buttons = {}
        
        # Init default genre file if missing
        if not os.path.exists(GENRE_FILE):
            try:
                default_preset = PRESETS.get("khong_gian_ok", PRESETS["nhac_tre"])
                with open(GENRE_FILE, "w") as f:
                    json.dump({
                        "genre": "khong_gian_ok",
                        "name": default_preset["name"],
                        "bpm_suggest": default_preset["bpm_suggest"],
                        "reverb_scale": 0,
                        "pitch_offset": 0,
                        "autotune_enabled": True,
                        "force_podcast": False,
                        **{k: v for k, v in default_preset.items()},
                    }, f)
            except: pass

        current_saved = "khong_gian_ok"
        is_podcast = False
        autotune_enabled = True
        try:
            with open(GENRE_FILE, "r") as f:
                saved_data = json.load(f)
                current_saved = saved_data.get("genre", "khong_gian_ok")
                is_podcast = saved_data.get("force_podcast", False)
                autotune_enabled = saved_data.get("autotune_enabled", True)
        except: pass

        for key, p in PRESETS.items():
            btn = Gtk.Button()
            btn.get_style_context().add_class("genre-btn")
            
            # Xây dựng bảng hiển thị thông số âm học chi tiết khi hover
            tooltip_text = (
                f"{p['desc']}\n\n"
                f"<b>📊 CHỈ SỐ DSP HỆ THỐNG:</b>\n"
                f"  • Kích thước phòng (Room): <b>{p.get('reverb_room', 0.0):.0%}</b>\n"
                f"  • Tỷ lệ vang (Reverb Wet): <b>{p.get('reverb_wet', 0.0):.0%}</b>\n"
                f"  • Tiêu tán âm dải cao (Damp): <b>{p.get('reverb_damp', 0.0):.0%}</b>\n"
                f"  • Độ bóng bẩy (Chorus Mix): <b>{p.get('chorus_mix', 0.0):.0%}</b>\n"
                f"  • Màu sắc hài âm (Saturation): <b>{p.get('saturation_amount', 0.0):.0%}</b>\n"
                f"  • Âm lượng nhại (Delay Vol): <b>{p.get('delay_volume', 0.0):.0%}</b>\n"
                f"  • Độ giữ nhại (Delay FB): <b>{p.get('delay_feedback', 0.0):.0%}</b>"
            )
            btn.set_tooltip_markup(tooltip_text)
            
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

        # LED dot chỉ báo kết nối BPM AI
        self.bpm_led = Gtk.Label(label="●", use_markup=False)
        self.bpm_led.set_markup("<span font='10' color='#52525b'>●</span>")
        bpm_led_ev = Gtk.EventBox()
        bpm_led_ev.add(self.bpm_led)
        bpm_led_ev.set_tooltip_text("BPM AI: Đang quét...")
        bpm_led_ev.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        bpm_led_ev.connect("button-press-event", lambda w, e: self.manual_connect_browser(target="bpm"))
        self._bpm_led_ev = bpm_led_ev  # giữ tham chiếu để set_tooltip_text sau
        bpm_box.pack_start(bpm_led_ev, False, False, 0)

        bpm_lbl = Gtk.Label(label="BPM")
        bpm_lbl.get_style_context().add_class("fixed-lbl")
        bpm_box.pack_start(bpm_lbl, False, False, 0)
        
        self.bpm_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 60, 180, 1)
        self.bpm_scale.set_value(PRESETS.get(current_saved, PRESETS["nhac_tre"])["bpm_suggest"])
        self.bpm_scale.connect("value-changed", self.on_bpm_changed)
        bpm_box.pack_start(self.bpm_scale, True, True, 0)
        
        vbox.pack_start(bpm_box, False, False, 0)
        
        # Reverb Scale Section (Vang tăng thêm %)
        reverb_scale_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        reverb_scale_lbl = Gtk.Label(label="Vang (%)")
        reverb_scale_lbl.get_style_context().add_class("fixed-lbl")
        reverb_scale_box.pack_start(reverb_scale_lbl, False, False, 0)
        
        self.reverb_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -100, 100, 5)
        saved_reverb_scale = 0
        try:
            with open(GENRE_FILE, "r") as f:
                saved_reverb_scale = json.load(f).get("reverb_scale", 0)
        except: pass
        self.reverb_scale.set_value(saved_reverb_scale)
        self.reverb_scale.connect("value-changed", self.on_reverb_scale_changed)
        reverb_scale_box.pack_start(self.reverb_scale, True, True, 0)
        
        vbox.pack_start(reverb_scale_box, False, False, 0)

        # Music Volume Section (Tăng/giảm Nhạc)
        music_vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        music_vol_lbl = Gtk.Label(label="Nhạc (%)")
        music_vol_lbl.get_style_context().add_class("fixed-lbl")
        music_vol_box.pack_start(music_vol_lbl, False, False, 0)
        
        self.music_vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 150, 1)
        saved_music_vol = 0.56
        try:
            with open(GENRE_FILE, "r") as f:
                saved_music_vol = json.load(f).get("music_volume", 0.56)
        except: pass
        saved_music_pct = int(round(saved_music_vol / 0.0056))
        self.music_vol_scale.set_value(saved_music_pct)
        self.music_vol_scale.connect("value-changed", self.on_music_volume_changed)
        music_vol_box.pack_start(self.music_vol_scale, True, True, 0)
        
        vbox.pack_start(music_vol_box, False, False, 0)
        
        # AutoTune toggle — sẽ được gom vào tone_box bên dưới
        self.autotune_toggle = Gtk.Switch()
        self.autotune_toggle.set_active(autotune_enabled)
        self.autotune_toggle.connect("notify::active", self.on_autotune_toggle)
        
        # Hàng chứa các nút Công cụ nâng cao
        tools_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        tools_box.set_halign(Gtk.Align.CENTER)
        
        # Nút Phân tích giọng (Auto-Calibration)
        self.analyze_btn = Gtk.Button()
        self.analyze_btn.set_name("analyze-btn")
        self.analyze_btn.get_style_context().add_class("analyze-btn")
        self.analyze_lbl = Gtk.Label(label="<span font='10' weight='bold' color='#ffffff'>🎙️ Phân Tích Giọng</span>", use_markup=True)
        self.analyze_btn.add(self.analyze_lbl)
        self.analyze_btn.connect("clicked", self.on_analyze_clicked)
        tools_box.pack_start(self.analyze_btn, True, True, 0)
        
        self.analyze_btn_css_provider = Gtk.CssProvider()
        self.analyze_btn.get_style_context().add_provider(
            self.analyze_btn_css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        vbox.pack_start(tools_box, False, False, 0)
        
        # Nút gạt chế độ HÁT LIVE vs. PODCAST (Thiết kế Điện tử Chân không / Neon Glow)
        self.is_podcast = is_podcast
        
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        mode_box.set_halign(Gtk.Align.CENTER)
        mode_box.get_style_context().add_class("mode-selector")
        
        self.btn_mode_singing = Gtk.Button(label="🎤 HÁT LIVE")
        self.btn_mode_singing.get_style_context().add_class("mode-btn")
        
        self.btn_mode_podcast = Gtk.Button(label="🎙️ PODCAST")
        self.btn_mode_podcast.get_style_context().add_class("mode-btn")
        
        mode_box.pack_start(self.btn_mode_singing, False, False, 0)
        mode_box.pack_start(self.btn_mode_podcast, False, False, 0)
        vbox.pack_start(mode_box, False, False, 12)
        
        # Connect signals
        self.btn_mode_singing.connect("clicked", lambda w: self.set_app_mode(False))
        self.btn_mode_podcast.connect("clicked", lambda w: self.set_app_mode(True))
        
        # Initialize active state
        self.set_app_mode(is_podcast, save=False)
        
        # ═══ TONE & AUTO-TUNE SECTION (gom chung — ẩn khi Podcast) ═══
        self.pitch_offset = 0
        try:
            with open(GENRE_FILE, "r") as f:
                saved_data = json.load(f)
                self.pitch_offset = saved_data.get("pitch_offset", 0)
        except: pass

        # Container dọc bao toàn bộ khu vực Tông + AutoTune
        self.tone_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.tone_box.set_halign(Gtk.Align.FILL)

        # Hàng 1: Tone giọng detect được (từ AI Key Detector)
        tone_detect_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        tone_detect_row.set_halign(Gtk.Align.CENTER)
        tone_detect_lbl = Gtk.Label(label="<span font='9' color='#71717a'>Giọng hát:</span>", use_markup=True)
        self.tone_lbl = Gtk.Label(label="<span font='11' weight='bold' color='#f39c12'>---</span>", use_markup=True)

        # LED dot chỉ báo kết nối Tông AI
        self.key_led = Gtk.Label()
        self.key_led.set_markup("<span font='10' color='#52525b'>●</span>")
        key_led_ev = Gtk.EventBox()
        key_led_ev.add(self.key_led)
        key_led_ev.set_tooltip_text("Tông AI: Đang quét...")
        key_led_ev.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        key_led_ev.connect("button-press-event", lambda w, e: self.manual_connect_browser(target="key"))
        self._key_led_ev = key_led_ev

        tone_detect_row.pack_start(tone_detect_lbl, False, False, 0)
        tone_detect_row.pack_start(self.tone_lbl, False, False, 4)
        tone_detect_row.pack_start(key_led_ev, False, False, 4)
        self.tone_box.pack_start(tone_detect_row, False, False, 0)

        # Hàng 2: Tông nhạc (shift) + AutoTune toggle — cùng 1 hàng
        tone_ctrl_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        tone_ctrl_row.set_halign(Gtk.Align.CENTER)

        lbl_tone_title = Gtk.Label(label="<b>🎹 Tông:</b>", use_markup=True)
        lbl_tone_title.get_style_context().add_class("tone-title-lbl")

        btn_tone_dec = Gtk.Button(label="➖")
        btn_tone_dec.get_style_context().add_class("tone-ctrl-btn")

        self.lbl_tone_value = Gtk.Label(label="<span font='10' weight='bold' color='#ff7c43'>0 (Gốc)</span>", use_markup=True)
        self.lbl_tone_value.set_xalign(0.5)
        self.lbl_tone_value.get_style_context().add_class("tone-val-lbl")

        btn_tone_inc = Gtk.Button(label="➕")
        btn_tone_inc.get_style_context().add_class("tone-ctrl-btn")

        # Separator
        sep_lbl = Gtk.Label(label="<span color='#3f3f46'>│</span>", use_markup=True)

        at_lbl = Gtk.Label(label="<b>Auto-Tune:</b>", use_markup=True)
        at_lbl.get_style_context().add_class("tone-title-lbl")

        tone_ctrl_row.pack_start(lbl_tone_title, False, False, 0)
        tone_ctrl_row.pack_start(btn_tone_dec, False, False, 0)
        tone_ctrl_row.pack_start(self.lbl_tone_value, False, False, 4)
        tone_ctrl_row.pack_start(btn_tone_inc, False, False, 0)
        tone_ctrl_row.pack_start(sep_lbl, False, False, 6)
        tone_ctrl_row.pack_start(at_lbl, False, False, 0)
        tone_ctrl_row.pack_start(self.autotune_toggle, False, False, 4)

        self.tone_box.pack_start(tone_ctrl_row, False, False, 0)
        vbox.pack_start(self.tone_box, False, False, 8)

        btn_tone_dec.connect("clicked", lambda w: self.adjust_pitch(-1))
        btn_tone_inc.connect("clicked", lambda w: self.adjust_pitch(1))
        self.update_pitch_label()
        
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
            
        self.status_lbl = Gtk.Label(label="", use_markup=True)
        self.status_lbl.set_line_wrap(True)
        self.status_lbl.set_max_width_chars(45) # Giới hạn ký tự để tự động xuống dòng, không kéo giãn cửa sổ
        vbox.pack_start(self.status_lbl, False, False, 5)
        
        # Audio Connection Status — các chỉ báo bấm được
        conn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        conn_box.set_halign(Gtk.Align.CENTER)

        def make_conn_indicator(attr_name, init_text):
            """Tạo nhãn chỉ báo có thể bấm được."""
            lbl = Gtk.Label(label=init_text, use_markup=True)
            ev = Gtk.EventBox()
            ev.add(lbl)
            ev.set_tooltip_text("Bấm để kết nối thủ công")
            ev.get_style_context().add_class("conn-indicator")
            ev.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            setattr(self, attr_name, lbl)
            return ev

        beat_ev  = make_conn_indicator("beat_conn_lbl",   "<span font='9'>🎵 Nhạc: Đang quét...</span>")
        mic_ev   = make_conn_indicator("mic_conn_lbl",    "<span font='9'>🎤 Mic: Đang quét...</span>")
        master_ev = make_conn_indicator("master_conn_lbl", "<span font='9'>🎧 Master: Đang quét...</span>")

        # Giữ tham chiếu ảo cho bpm_conn_lbl và key_conn_lbl (được thể hiện bằng LED riêng)
        self.bpm_conn_lbl = Gtk.Label()   # LED tỹ theo self.bpm_led
        self.key_conn_lbl = Gtk.Label()   # LED theo self.key_led

        # Click handlers — kết nối thủ công
        beat_ev.connect("button-press-event",   lambda w, e: self.manual_connect_browser())
        mic_ev.connect("button-press-event",    lambda w, e: self.manual_connect_mic())
        master_ev.connect("button-press-event", lambda w, e: self.manual_connect_master())

        for ev in [beat_ev, mic_ev, master_ev]:
            conn_box.pack_start(ev, False, False, 0)
        vbox.pack_start(conn_box, False, False, 10)

        # Biến cờ để tránh vòng lặp sự kiện (user kéo slider vs file update)
        self.user_sliding = False
        self.bpm_scale.connect("button-press-event", self.on_slider_press)
        self.bpm_scale.connect("button-release-event", self.on_slider_release)
        self.reverb_scale.connect("button-press-event", self.on_slider_press)
        self.reverb_scale.connect("button-release-event", self.on_slider_release)
        self.music_vol_scale.connect("button-press-event", self.on_slider_press)
        self.music_vol_scale.connect("button-release-event", self.on_slider_release)
        
        # Khởi chạy kiểm tra kết nối định kỳ
        GLib.timeout_add(2000, self.check_audio_connections)
        
        # Bắt đầu luồng kiểm tra BPM file tự động
        GLib.timeout_add(1000, self.check_bpm_file)
        
        # Khởi chạy kiểm tra Tone file định kỳ
        self.last_key_timestamp = 0
        GLib.timeout_add(500, self.check_key_file)
        
        # Kết nối sự kiện bàn phím cho 9 phím tắt SFX
        self.connect("key-press-event", self.on_key_press)
        
        # Khởi tạo giá trị hiển thị cho các tooltip của preset
        self.update_genre_tooltips()

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
        if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS:
            if widget == self.music_vol_scale:
                widget.set_value(100) # Reset Nhạc về 100% (0dB)
            elif widget == self.reverb_scale:
                widget.set_value(0)   # Reset Vang về 0% (Offset = 0)
            elif widget == self.bpm_scale:
                try:
                    with open(GENRE_FILE, "r") as f:
                        key = json.load(f).get("genre", "nhac_tre")
                    widget.set_value(PRESETS.get(key, PRESETS["nhac_tre"])["bpm_suggest"])
                except:
                    widget.set_value(100)
            return True
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
                    self.tone_lbl.set_markup(f"<span font='11' weight='bold' color='#f39c12'>{note} {scale}</span>")
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

            # Scan available interfaces
            inputs, outputs = self.get_audio_interfaces()
            default_in, default_out = self.get_default_pipewire_nodes()

            # Resolve active input/output devices (NO automatic fallback unless explicitly selected)
            active_in = ""
            if sel_in and sel_in in inputs:
                active_in = sel_in

            active_out = ""
            if sel_out and sel_out in outputs:
                active_out = sel_out

            # Tìm các cổng của Mic_AI recorder
            mic_ai_ports = []
            try:
                res_i = subprocess.run(["pw-link", "-i"], capture_output=True, text=True, timeout=0.5)
                for line in res_i.stdout.splitlines():
                    line = line.strip()
                    if "vocal_ai" in line.lower() or "pw-record" in line.lower() or "pw-cat" in line.lower():
                        if not any(x in line.lower() for x in ["beat_ai", "beat_ai_key", "master_ai"]):
                            mic_ai_ports.append(line)
            except: pass

            # Tự động kết nối & duy trì thiết bị đầu vào (Mic)
            if active_in:
                # Ngắt kết nối của các thiết bị đầu vào khác đang nối tới REAPER và mic_ai_ports
                for src_port, active_conns in list(connections.items()):
                    if src_port.startswith("alsa_input.") and not src_port.startswith(f"{active_in}:"):
                        for dest in active_conns:
                            if dest in [REAPER_VOCAL_IN_L, REAPER_VOCAL_IN_R] or dest in mic_ai_ports:
                                subprocess.run(["pw-link", "-d", src_port, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # ⚠️ ANTI-FEEDBACK: Mic (alsa_input) KHÔNG ĐƯỢC vào REAPER music in (in1/in2)
            for src_port, active_conns in list(connections.items()):
                if src_port.startswith("alsa_input."):
                    for dest in active_conns:
                        if dest in [REAPER_MUSIC_IN_L, REAPER_MUSIC_IN_R]:
                            subprocess.run(["pw-link", "-d", src_port, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # ⚠️ ANTI-FEEDBACK: Monitor ports (alsa_output.*:monitor_*) KHÔNG ĐƯỢC vào REAPER
            # Đây là nguồn gốc của tiếng "ò ò": MixPre monitor → REAPER vocal in → loa → MixPre
            for src_port, active_conns in list(connections.items()):
                if ":monitor_" in src_port.lower():
                    for dest in active_conns:
                        if dest.startswith("REAPER:"):  # monitor không được vào REAPER bất kỳ kênh nào
                            subprocess.run(["pw-link", "-d", src_port, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if active_in:
                capture_ports = []
                try:
                    res_o = subprocess.run(["pw-link", "-o"], capture_output=True, text=True, timeout=0.5)
                    capture_ports = [
                        l.strip() for l in res_o.stdout.splitlines()
                        if l.startswith(f"{active_in}:")
                        and ":capture_" in l.lower()      # chỉ capture port thực sự
                        and ":monitor_" not in l.lower()  # loại bỏ monitor (gây feedback!)
                    ]
                    capture_ports.sort() # Sắp xếp để đảm bảo capture_FL, capture_FR đúng thứ tự
                except: pass
                
                if capture_ports:
                    target_map = {}
                    if len(capture_ports) == 1:
                        target_map[capture_ports[0]] = [REAPER_VOCAL_IN_L, REAPER_VOCAL_IN_R] + mic_ai_ports
                    else:
                        target_map[capture_ports[0]] = [REAPER_VOCAL_IN_L] + mic_ai_ports
                        target_map[capture_ports[1]] = [REAPER_VOCAL_IN_R]
                        
                    for src_port, dests in target_map.items():
                        active_conns = connections.get(src_port, [])
                        for target_dest in dests:
                            if target_dest not in active_conns:
                                subprocess.run(["pw-link", src_port, target_dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        # Ngắt kết nối thừa tới các cổng REAPER vocal in khác không mong muốn
                        for dest in active_conns:
                            if dest.startswith("REAPER:") and dest not in dests:
                                subprocess.run(["pw-link", "-d", src_port, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                
                # Ngắt kết nối của các thiết bị đầu vào khác đang nối tới REAPER và mic_ai_ports
                for src_port, active_conns in list(connections.items()):
                    if src_port.startswith("alsa_input.") and not src_port.startswith(f"{active_in}:"):
                        for dest in active_conns:
                            if dest in [REAPER_VOCAL_IN_L, REAPER_VOCAL_IN_R] or dest in mic_ai_ports:
                                subprocess.run(["pw-link", "-d", src_port, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


            # Ngắt kết nối trực tiếp từ Microphone tới bất kỳ loa/đầu ra nào (alsa_input.* -> alsa_output.*)
            # để tránh rú rít (feedback loop) và hiện tượng trễ âm kép
            for src_port, active_conns in list(connections.items()):
                if src_port.startswith("alsa_input."):
                    for dest in active_conns:
                        if dest.startswith("alsa_output."):
                            subprocess.run(["pw-link", "-d", src_port, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Tự động kết nối & duy trì thiết bị đầu ra (Speaker / Interface Out)
            if active_out:
                playback_ports = []
                try:
                    res_play = subprocess.run(["pw-link", "-i"], capture_output=True, text=True, timeout=0.5)
                    playback_ports = [l.strip() for l in res_play.stdout.splitlines() if l.startswith(f"{active_out}:")]
                    playback_ports.sort() # Sắp xếp để đảm bảo playback_FL, playback_FR đúng thứ tự
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
                        # Ngắt các kết nối thừa từ REAPER out này tới các cổng loa khác không mong muốn trong chính thiết bị được chọn
                        for dest in active_conns:
                            if dest.startswith(f"{active_out}:") and dest not in dests:
                                subprocess.run(["pw-link", "-d", src_port, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                
                # Ngắt kết nối của REAPER tới các thiết bị đầu ra khác
                for src_port, active_conns in list(connections.items()):
                    if src_port in ["REAPER:out1", "REAPER:out2"]:
                        for dest in active_conns:
                            if dest.startswith("alsa_output.") and not dest.startswith(f"{active_out}:"):
                                subprocess.run(["pw-link", "-d", src_port, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # Ngắt kết nối của tất cả các nguồn âm thanh khác (không phải REAPER) tới thiết bị đầu ra được chọn
                for src_port, active_conns in list(connections.items()):
                    if src_port not in ["REAPER:out1", "REAPER:out2"]:
                        for dest in active_conns:
                            if dest.startswith(f"{active_out}:"):
                                subprocess.run(["pw-link", "-d", src_port, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


            # Analyze connection states for UI indicators
            for src, dests in connections.items():
                src_lower = src.lower()
                for dest in dests:
                    dest_lower = dest.lower()
                    
                    # 1. Nhạc (Beat): Browser connected to REAPER or Beat_AI
                    is_browser_src = any(x in src_lower for x in ["chrome", "firefox", "brave", "opera", "edge", "vivaldi"])
                    is_browser_dest = any(x in dest_lower for x in ["chrome", "firefox", "brave", "opera", "edge", "vivaldi"])
                    if is_browser_src and ("reaper" in dest_lower or "beat_ai" in dest_lower):
                        has_beat = True
                    elif is_browser_dest and ("reaper" in src_lower or "beat_ai" in src_lower):
                        has_beat = True
                            
                    # 2. Mic: Selected (or any) input connected to REAPER or Vocal_AI
                    is_mic_src = "alsa_input" in src_lower and "capture" in src_lower
                    is_mic_dest = "alsa_input" in dest_lower and "capture" in dest_lower
                    
                    if is_mic_src:
                        if active_in:
                            if active_in in src and ("reaper" in dest_lower or "vocal_ai" in dest_lower):
                                has_mic = True
                        else:
                            if "reaper" in dest_lower or "vocal_ai" in dest_lower:
                                has_mic = True
                    elif is_mic_dest:
                        if active_in:
                            if active_in in dest and ("reaper" in src_lower or "vocal_ai" in src_lower):
                                has_mic = True
                        else:
                            if "reaper" in src_lower or "vocal_ai" in src_lower:
                                has_mic = True
                                
                    # 3. Master: REAPER output connected to Master_AI
                    is_reaper_out_src = "reaper" in src_lower and "out" in src_lower
                    is_reaper_out_dest = "reaper" in dest_lower and "out" in dest_lower
                    if is_reaper_out_src and "master_ai" in dest_lower:
                        has_master = True
                    elif is_reaper_out_dest and "master_ai" in src_lower:
                        has_master = True
            
            # Thu thập browser ports
            browser_ports = [src for src in connections.keys()
                             if any(x in src.lower() for x in ["firefox", "chrom", "brave", "opera", "edge", "vivaldi"])]
            browser_ports.sort()

            # Cập nhật trạng thái kết nối Beat_AI và Key_AI (Beat_AI_Key)
            has_bpm_ai  = False  # browser → Beat_AI
            has_key_ai  = False  # browser → Beat_AI_Key

            for src_port in browser_ports:
                bp_conns = connections.get(src_port, [])\

                # Nối vào REAPER (nhạc nền) — chỉ nếu REAPER đang chạy
                reaper_dest = REAPER_MUSIC_IN_L if (browser_ports.index(src_port) % 2 == 0) else REAPER_MUSIC_IN_R
                reaper_connected = reaper_dest in bp_conns  # đã nối từ trước?
                if not reaper_connected:
                    result = subprocess.run(["pw-link", src_port, reaper_dest],
                                            capture_output=True, text=True)
                    reaper_connected = (result.returncode == 0)

                # Nối vào Beat_AI (BPM detector)
                beat_ai_ports = []
                try:
                    res_i2 = subprocess.run(["pw-link", "-i"], capture_output=True, text=True, timeout=0.5)
                    beat_ai_ports = [l.strip() for l in res_i2.stdout.splitlines()
                                     if "beat_ai" in l.lower() and "beat_ai_key" not in l.lower()]
                except: pass
                for bat_port in beat_ai_ports:
                    if bat_port not in bp_conns:
                        subprocess.run(["pw-link", src_port, bat_port], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if beat_ai_ports:
                    has_bpm_ai = True

                # Nối vào Beat_AI_Key (Tone/Key detector)
                key_ai_ports = []
                try:
                    res_i3 = subprocess.run(["pw-link", "-i"], capture_output=True, text=True, timeout=0.5)
                    key_ai_ports = [l.strip() for l in res_i3.stdout.splitlines()
                                    if "beat_ai_key" in l.lower()]
                except: pass
                for kap in key_ai_ports:
                    if kap not in bp_conns:
                        subprocess.run(["pw-link", src_port, kap], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if key_ai_ports:
                    has_key_ai = True

                # ⚠️ Chỉ ngắt browser khỏi loa hệ thống KHI REAPER đã nhận được âm
                # Nếu REAPER chưa kết nối được → GIỮ nguyên để YouTube vẫn phát được
                if reaper_connected:
                    for dest in list(bp_conns):
                        if "REAPER" not in dest:
                            if not any(x in dest.lower() for x in ["beat_ai", "beat_ai_key", "key_ai", "pw-record", "master_ai"]):
                                subprocess.run(["pw-link", "-d", src_port, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        elif dest in [REAPER_VOCAL_IN_L, REAPER_VOCAL_IN_R]:
                            subprocess.run(["pw-link", "-d", src_port, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                            
            # ─ Cập nhật chỉ báo Nhạc ─
            if has_beat:
                self.beat_conn_lbl.set_markup("<span font='9' color='#2ecc71'>🎵 Nhạc: Đã nối</span>")
                self.beat_conn_lbl.set_tooltip_text("Trình phát nhạc đã kết nối vào REAPER")
            else:
                self.beat_conn_lbl.set_markup("<span font='9' color='#e74c3c'>🎵 Nhạc: Chưa có web</span>")
                self.beat_conn_lbl.set_tooltip_text("Bấm để thử nối lại")

            # ─ LED dot BPM AI (cạnh chữ BPM) ─
            if has_bpm_ai:
                self.bpm_led.set_markup("<span font='10' color='#2ecc71'>●</span>")
                self._bpm_led_ev.set_tooltip_text("BPM AI: Đã nối — Nhạc đang vào Beat_AI")
            elif browser_ports:
                self.bpm_led.set_markup("<span font='10' color='#f39c12'>●</span>")
                self._bpm_led_ev.set_tooltip_text("BPM AI: Chưa có node — Beat_AI chưa chạy (bấm để thử nối)")
            else:
                self.bpm_led.set_markup("<span font='10' color='#52525b'>●</span>")
                self._bpm_led_ev.set_tooltip_text("BPM AI: Chưa có nhạc — Bật nhạc trình duyệt trước")

            # ─ LED dot Tông AI (cạnh hiển thị giọng) ─
            if has_key_ai:
                self.key_led.set_markup("<span font='10' color='#2ecc71'>●</span>")
                self._key_led_ev.set_tooltip_text("Tông AI: Đã nối — Nhạc đang vào Beat_AI_Key")
            elif browser_ports:
                self.key_led.set_markup("<span font='10' color='#f39c12'>●</span>")
                self._key_led_ev.set_tooltip_text("Tông AI: Chưa có node — Beat_AI_Key chưa chạy (bấm để thử nối)")
            else:
                self.key_led.set_markup("<span font='10' color='#52525b'>●</span>")
                self._key_led_ev.set_tooltip_text("Tông AI: Chưa có nhạc — Bật nhạc trình duyệt trước")


            # ─ Cập nhật chỉ báo Mic ─
            if has_mic:
                if active_in:
                    friendly_mic = self.get_device_friendly_name(active_in)
                    friendly_mic = friendly_mic.replace("🎙️", "").strip()
                else:
                    friendly_mic = "Hệ thống / Thủ công"
                self.mic_conn_lbl.set_markup("<span font='9' color='#2ecc71'>🎤 Mic: Đã nối</span>")
                self.mic_conn_lbl.set_tooltip_text(friendly_mic)
            else:
                self.mic_conn_lbl.set_markup("<span font='9' color='#e74c3c'>🎤 Mic: Chưa nối AI</span>")
                self.mic_conn_lbl.set_tooltip_text("Bấm để kết nối thủ công")

            # ─ Cập nhật chỉ báo Master ─
            if has_master:
                friendly_out = "AI Hoạt động"
                if active_out:
                    friendly_out = self.get_device_friendly_name(active_out)
                    friendly_out = friendly_out.replace("🔊", "").strip()
                master_status = "Đã nối"
                master_color = "#2ecc71"
                try:
                    with open("/tmp/ai_karaoke_master_status.txt", "r") as f:
                        if "OVERLOAD" in f.read():
                            master_status = "QUÁ TẢI!"
                            master_color = "#e74c3c"
                except: pass
                self.master_conn_lbl.set_markup(f"<span font='9' color='{master_color}'>🎧 Master: {master_status}</span>")
                self.master_conn_lbl.set_tooltip_text(friendly_out)
            else:
                self.master_conn_lbl.set_markup("<span font='9' color='#e74c3c'>🎧 Master: Chưa nối AI</span>")
                self.master_conn_lbl.set_tooltip_text("Bấm để kết nối thủ công")

        except: pass
        GLib.idle_add(lambda: self.resize(360, 1) or False)
        return True

    def manual_connect_browser(self, target="all"):
        """Kết nối thủ công browser → REAPER / Beat_AI / Beat_AI_Key."""
        import subprocess
        try:
            res = subprocess.run(["pw-link", "-o"], capture_output=True, text=True, timeout=2)
            browser_ports = [l.strip() for l in res.stdout.splitlines()
                             if any(x in l.lower() for x in ["firefox", "chrom", "brave", "opera", "edge", "vivaldi"])]
            if not browser_ports:
                self.update_status("<span font='9' color='#f39c12'>⚠️ Chưa thấy trình duyệt đang phát nhạc</span>")
                GLib.timeout_add(3000, lambda: self.update_status("") or False)
                return
            res_i = subprocess.run(["pw-link", "-i"], capture_output=True, text=True, timeout=2)
            all_inputs = res_i.stdout.splitlines()
            reaper_ports = [REAPER_MUSIC_IN_L, REAPER_MUSIC_IN_R]
            beat_ports = [l.strip() for l in all_inputs if "beat_ai" in l.lower() and "beat_ai_key" not in l.lower()]
            key_ports  = [l.strip() for l in all_inputs if "beat_ai_key" in l.lower()]
            connected = 0
            for i, bp in enumerate(browser_ports):
                if target in ("all", "reaper"):
                    dst = reaper_ports[i % len(reaper_ports)]
                    subprocess.run(["pw-link", bp, dst], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    connected += 1
                if target in ("all", "bpm"):
                    for bat in beat_ports:
                        subprocess.run(["pw-link", bp, bat], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        connected += 1
                if target in ("all", "key"):
                    for kp in key_ports:
                        subprocess.run(["pw-link", bp, kp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        connected += 1
            label = {"bpm": "BPM AI", "key": "Tông AI", "all": "REAPER + BPM + Tông AI"}.get(target, target)
            self.update_status(f"<span font='9' color='#2ecc71'>✅ Đã nối thủ công: {label} ({connected} link)</span>")
            GLib.timeout_add(3000, lambda: self.update_status("") or False)
        except Exception as ex:
            self.update_status(f"<span font='9' color='#e74c3c'>❌ Kết nối thất bại: {ex}</span>")
            GLib.timeout_add(3000, lambda: self.update_status("") or False)

    def manual_connect_mic(self):
        """Kết nối thủ công mic → REAPER / Vocal_AI."""
        self.check_audio_connections()
        self.update_status("<span font='9' color='#2ecc71'>✅ Đã thử nối lại Mic</span>")
        GLib.timeout_add(2000, lambda: self.update_status("") or False)

    def manual_connect_master(self):
        """Kết nối REAPER out → Master_AI."""
        import subprocess
        try:
            res_i = subprocess.run(["pw-link", "-i"], capture_output=True, text=True, timeout=2)
            master_ports = [l.strip() for l in res_i.stdout.splitlines() if "master_ai" in l.lower()]
            for mp in master_ports:
                subprocess.run(["pw-link", "REAPER:out1", mp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["pw-link", "REAPER:out2", mp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.update_status(f"<span font='9' color='#2ecc71'>✅ Đã nối REAPER → Master AI ({len(master_ports)} port)</span>")
            GLib.timeout_add(3000, lambda: self.update_status("") or False)
        except Exception as ex:
            self.update_status(f"<span font='9' color='#e74c3c'>❌ {ex}</span>")
            GLib.timeout_add(3000, lambda: self.update_status("") or False)


    def setup_css(self):
        css = """
        window { background-color: #121218; }
        .fixed-lbl {
            color: #d1d5db;
            text-shadow: none;
        }
        .fixed-lbl:backdrop, .fixed-lbl:disabled {
            color: #d1d5db;
        }
        button {
            background-image: none;
            text-shadow: none;
            box-shadow: none;
        }
        .genre-btn {
            background-image: none;
            background-color: #1f1f28;
            border-radius: 12px;
            border: 1px solid #333340;
            padding: 10px;
            color: #e4e4e7;
            transition: all 0.2s ease;
        }
        .genre-btn:hover { background-image: none; background-color: #2d2d3b; border-color: #a78bfa; }
        .active-btn {
            background-image: none;
            background-color: #3b2a5c;
            border: 2px solid #a78bfa;
            color: white;
        }
        .analyze-btn {
            background-image: none;
            background-color: #e67e22;
            border-radius: 8px;
            padding: 8px;
            transition: all 0.2s ease;
        }
        .analyze-btn:hover { background-image: none; background-color: #d35400; }
        .sfx-btn {
            background-image: none;
            background-color: #1a1a24;
            border-radius: 10px;
            border: 1px solid #2d2d3d;
            padding: 8px;
            color: #cbd5e1;
            transition: all 0.2s ease;
        }
        .sfx-btn:hover {
            background-image: none;
            background-color: #2e2e3e;
            border-color: #38bdf8;
            color: #ffffff;
        }
        .settings-btn {
            background-image: none;
            background-color: transparent;
            border: none;
            color: #a78bfa;
            padding: 4px;
            transition: all 0.2s ease;
        }
        .settings-btn:hover {
            background-image: none;
            color: #c084fc;
        }
        .settings-dialog {
            background-color: #121218;
            color: #cbd5e1;
        }
        .setup-btn {
            background-image: none;
            background-color: #7c3aed;
            border: 1px solid #6d28d9;
            color: #ffffff;
            font-weight: bold;
            padding: 8px 16px;
            margin-top: 15px;
            border-radius: 6px;
            transition: all 0.2s ease;
        }
        .setup-btn:hover {
            background-image: none;
            background-color: #8b5cf6;
            border-color: #7c3aed;
            color: #ffffff;
        }
        .tone-title-lbl {
            color: #cbd5e1;
            font-size: 11px;
            margin-right: 5px;
        }
        .tone-val-lbl {
            min-width: 60px;
        }
        .tone-ctrl-btn {
            background-image: none;
            background-color: #1a1a24;
            border: 1px solid #2e2e3e;
            border-radius: 6px;
            padding: 4px 12px;
            font-size: 10px;
            font-weight: bold;
            color: #cbd5e1;
            transition: all 0.2s ease;
        }
        .tone-ctrl-btn:hover {
            background-image: none;
            background-color: #2b1f1d;
            border-color: #ff7c43;
            color: #ff7c43;
        }
        
        /* Cấu hình bộ gạt chế độ Neon Chân Không */
        .mode-selector {
            background-color: #1a1a24;
            border: 2px solid #2e2e3e;
            border-radius: 20px;
            padding: 3px;
        }
        .mode-btn {
            background-image: none;
            background-color: #121218;
            border: 1px solid #2d2d3d;
            border-radius: 17px;
            padding: 6px 20px;
            font-size: 11px;
            font-weight: bold;
            color: #8e8e9f;
            transition: all 0.3s ease;
        }
        .mode-btn:hover {
            color: #a1a1aa;
        }
        
        /* Trạng thái Hát hoạt động: Neon Cam Amber sáng đèn (Chữ trắng phát sáng) */
        #mode-singing-active {
            background-image: none;
            background-color: #3d1c0a;
            color: #ffffff;
            border-color: #ff7c43;
            text-shadow: 0 0 5px #ff7c43, 0 0 10px #ff7c43;
            box-shadow: 0 0 8px rgba(255, 124, 67, 0.6), inset 0 0 6px rgba(255, 124, 67, 0.3);
        }
        /* Trạng thái Hát tắt: Đèn tắt nguồn (Độ sáng cực thấp) */
        #mode-singing-inactive {
            background-image: none;
            background-color: #14141c;
            color: #592710;
            border-color: #2b170e;
            box-shadow: none;
        }
        
        /* Trạng thái Podcast hoạt động: Neon Xanh Cyan sáng đèn (Chữ trắng phát sáng) */
        #mode-podcast-active {
            background-image: none;
            background-color: #08292e;
            color: #ffffff;
            border-color: #00f5ff;
            text-shadow: 0 0 5px #00f5ff, 0 0 10px #00f5ff;
            box-shadow: 0 0 8px rgba(0, 245, 255, 0.6), inset 0 0 6px rgba(0, 245, 255, 0.3);
        }
        /* Trạng thái Podcast tắt: Đèn tắt nguồn (Độ sáng cực thấp) */
        #mode-podcast-inactive {
            background-image: none;
            background-color: #14141c;
            color: #004547;
            border-color: #0a2529;
            box-shadow: none;
        }
        
        /* Cấu hình ComboBox thiết bị âm thanh rõ nét trong Dark mode */
        combobox {
            background-color: #1f1f28;
            color: #ffffff;
            border: 1px solid #333340;
            border-radius: 6px;
            padding: 3px;
        }
        combobox cellview {
            background-color: transparent;
            color: #ffffff;
        }
        combobox button {
            background-color: transparent;
            color: #ffffff;
            background-image: none;
            border: none;
            box-shadow: none;
        }
        combobox menu, combobox window, combobox popover {
            background-color: #1f1f28;
            color: #ffffff;
            border: 1px solid #333340;
        }
        combobox menu menuitem, combobox popover modelbutton {
            color: #ffffff;
            background-color: #1f1f28;
            padding: 6px 12px;
        }
        combobox menu menuitem:hover, combobox popover modelbutton:hover {
            background-color: #3b2a5c;
            color: #ffffff;
        }
        
        /* Cấu hình các nút trong hộp thoại Settings */
        .dialog-btn {
            background-image: none;
            border-radius: 6px;
            padding: 6px 16px;
            font-weight: bold;
            transition: all 0.2s ease;
        }
        .cancel-btn {
            background-color: #2d2d3d;
            border: 1px solid #47475c;
            color: #cbd5e1;
        }
        .cancel-btn:hover {
            background-color: #3e3e55;
            color: #ffffff;
        }
        .ok-btn {
            background-color: #7c3aed;
            border: 1px solid #6d28d9;
            color: #ffffff;
        }
        .ok-btn:hover {
            background-color: #8b5cf6;
            border-color: #7c3aed;
        }
        scale trough {
            background-color: #1f1f2e;
            border-radius: 4px;
            min-height: 8px;
        }
        scale highlight {
            background-color: #8b5cf6;
            border-radius: 4px;
        }
        scale slider {
            background-color: #a78bfa;
            border-radius: 50%;
            min-width: 16px;
            min-height: 16px;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def update_status(self, markup_text):
        self.status_lbl.set_markup(markup_text)
        GLib.idle_add(lambda: self.resize(360, 1) or False)

    def on_analyze_clicked(self, widget):
        if getattr(self, "is_analyzing", False):
            return
        self.is_analyzing = True
        
        progress_file = "/tmp/ai_karaoke_calib_progress.json"
        if os.path.exists(progress_file):
            try: os.remove(progress_file)
            except: pass
            
        self.update_status("<span font='9' color='#f1c40f'>🎤 Đang khởi động lấy mẫu giọng...</span>")
        self.analyze_lbl.set_markup("<span font='11' weight='bold' color='#ffffff'>🎙️ Đang khởi động...</span>")
        
        # Helper to set button progress background
        def set_btn_progress(progress, status_type="recording"):
            percentage = int(progress * 100)
            if status_type == "recording":
                color = "#38bdf8" # Blue
            elif status_type == "waiting":
                color = "#f1c40f" # Yellow
            elif status_type == "done":
                color = "#2ecc71" # Green
            else:
                color = "#e74c3c" # Red
                
            css_data = f"""
            #analyze-btn {{
                background-image: linear-gradient(to right, {color} {percentage}%, #2e2e3e {percentage}%);
                color: #ffffff;
                border-color: {color};
            }}
            """
            self.analyze_btn_css_provider.load_from_data(css_data.encode("utf-8"))

        import subprocess
        dir_path = os.path.dirname(os.path.realpath(__file__))
        subprocess.Popen(["python3", os.path.join(dir_path, "auto_calibrate.py")])
        
        def poll_progress():
            if not os.path.exists(progress_file):
                return True
                
            try:
                with open(progress_file, "r") as f:
                    data = json.load(f)
                    
                status = data.get("status", "waiting")
                seconds = data.get("seconds", 0.0)
                target = data.get("target_seconds", 5.0)
                progress = data.get("progress", 0.0)
                
                if status == "recording":
                    self.update_status(f"<span font='9' color='#38bdf8'>🎙️ Đang thu âm: {seconds:.1f}s / {target:.1f}s (Hãy tiếp tục hát...)</span>")
                    self.analyze_lbl.set_markup(f"<span font='11' weight='bold' color='#ffffff'>🎙️ Đang thu: {seconds:.1f}s / {target:.1f}s</span>")
                    set_btn_progress(progress, "recording")
                elif status == "waiting":
                    self.update_status(f"<span font='9' color='#f1c40f'>🎙️ Lấy mẫu giọng: {seconds:.1f}s / {target:.1f}s (Hãy hát/ngâm nga vào mic...)</span>")
                    self.analyze_lbl.set_markup(f"<span font='11' weight='bold' color='#ffffff'>🎙️ Hãy hát vào mic...</span>")
                    set_btn_progress(progress, "waiting")
                elif status == "done":
                    self.update_status("<span font='9' color='#2ecc71'>✅ Đã lấy mẫu thành công &amp; tinh chỉnh EQ, Reverb!</span>")
                    self.analyze_lbl.set_markup("<span font='11' weight='bold' color='#ffffff'>✅ Đã lấy mẫu xong!</span>")
                    set_btn_progress(1.0, "done")
                    
                    def reset_btn():
                        css_data = """
                        #analyze-btn {
                            background-image: none;
                        }
                        """
                        self.analyze_btn_css_provider.load_from_data(css_data.encode("utf-8"))
                        self.analyze_lbl.set_markup("<span font='10' weight='bold' color='#ffffff'>🎙️ Phân Tích Giọng</span>")
                        self.is_analyzing = False
                        self.update_status("")
                        return False
                        
                    GLib.timeout_add(3000, reset_btn)
                    return False
                elif status in ["timeout", "error"]:
                    msg = "⚠️ Quá giờ lấy mẫu!" if status == "timeout" else "❌ Lỗi lấy mẫu!"
                    color_tag = "#e74c3c"
                    self.update_status(f"<span font='9' color='{color_tag}'>{msg}</span>")
                    self.analyze_lbl.set_markup(f"<span font='11' weight='bold' color='#ffffff'>{msg}</span>")
                    set_btn_progress(progress, "error")
                    
                    def reset_btn():
                        css_data = """
                        #analyze-btn {
                            background-image: none;
                        }
                        """
                        self.analyze_btn_css_provider.load_from_data(css_data.encode("utf-8"))
                        self.analyze_lbl.set_markup("<span font='10' weight='bold' color='#ffffff'>🎙️ Phân Tích Giọng</span>")
                        self.is_analyzing = False
                        self.update_status("")
                        return False
                        
                    GLib.timeout_add(3500, reset_btn)
                    return False
            except:
                pass
            return True
            
        GLib.timeout_add(150, poll_progress)

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
            
        data["reverb_scale"] = self.reverb_scale.get_value() if hasattr(self, "reverb_scale") else old_data.get("reverb_scale", 0)
        data["music_volume"] = self.music_vol_scale.get_value() * 0.0056 if hasattr(self, "music_vol_scale") else old_data.get("music_volume", 0.56)

        if "autotune_enabled" in old_data:
            data["autotune_enabled"] = old_data["autotune_enabled"]
            if hasattr(self, "autotune_toggle"):
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

    def update_genre_tooltips(self):
        reverb_scale = self.reverb_scale.get_value() if hasattr(self, "reverb_scale") else 0.0
        scale_factor = 1.0 + (reverb_scale / 100.0)
        room_scale_factor = 1.0 + (reverb_scale / 200.0)
        
        for key, p in PRESETS.items():
            btn = self.buttons.get(key)
            if not btn: continue
            
            wet = p.get("reverb_wet", 0.0)
            room = p.get("reverb_room", 0.0)
            scaled_wet = min(max(wet * scale_factor, 0.0), 0.95)
            scaled_room = min(max(room * room_scale_factor, 0.2), 0.95)
            
            # Xây dựng bảng hiển thị thông số âm học chi tiết khi hover
            tooltip_text = (
                f"{p['desc']}\n\n"
                f"<b>📊 CHỈ SỐ DSP THỰC TẾ (Đã điều chỉnh):</b>\n"
                f"  • Kích thước phòng (Room): <b>{scaled_room:.0%}</b> (Gốc: {room:.0%})\n"
                f"  • Tỷ lệ vang (Reverb Wet): <b>{scaled_wet:.0%}</b> (Gốc: {wet:.0%})\n"
                f"  • Tiêu tán âm dải cao (Damp): <b>{p.get('reverb_damp', 0.0):.0%}</b>\n"
                f"  • Độ bóng bẩy (Chorus Mix): <b>{p.get('chorus_mix', 0.0):.0%}</b>\n"
                f"  • Màu sắc hài âm (Saturation): <b>{p.get('saturation_amount', 0.0):.0%}</b>\n"
                f"  • Âm lượng nhại (Delay Vol): <b>{p.get('delay_volume', 0.0):.0%}</b>\n"
                f"  • Độ giữ nhại (Delay FB): <b>{p.get('delay_feedback', 0.0):.0%}</b>"
            )
            btn.set_tooltip_markup(tooltip_text)

    def on_reverb_scale_changed(self, widget):
        val = widget.get_value()
        try:
            with open(GENRE_FILE, "r") as f: data = json.load(f)
        except: data = {}
        data["reverb_scale"] = val
        data["timestamp"] = time.time()
        with open(GENRE_FILE, "w") as f:
            json.dump(data, f)
        self.update_genre_tooltips()

    def on_music_volume_changed(self, widget):
        pct = widget.get_value()
        val = round(pct * 0.0056, 4)
        try:
            with open(GENRE_FILE, "r") as f: data = json.load(f)
        except: data = {}
        data["music_volume"] = val
        data["timestamp"] = time.time()
        with open(GENRE_FILE, "w") as f:
            json.dump(data, f)
            
    def set_app_mode(self, to_podcast, save=True):
        self.is_podcast = to_podcast
        if to_podcast:
            # Active Podcast: Vacuum tube green-blue neon glow
            self.btn_mode_singing.set_name("mode-singing-inactive")
            self.btn_mode_podcast.set_name("mode-podcast-active")
        else:
            # Active Singing: Vacuum tube orange-amber neon glow
            self.btn_mode_singing.set_name("mode-singing-active")
            self.btn_mode_podcast.set_name("mode-podcast-inactive")
            
        # Ẩn/hiện khu vực Tông + AutoTune theo mode
        if hasattr(self, "tone_box"):
            if to_podcast:
                self.tone_box.hide()
            else:
                self.tone_box.show_all()
            
        if save:
            try:
                with open(GENRE_FILE, "r") as f: data = json.load(f)
            except: data = {}
            data["force_podcast"] = to_podcast
            data["timestamp"] = time.time()
            with open(GENRE_FILE, "w") as f:
                json.dump(data, f)
            
            if to_podcast:
                self.update_status("<span font='9' color='#00f5ff'>🎙️ Đã chuyển sang chế độ Podcast (Giọng ấm, nén gắt, tắt autotune)</span>")
            else:
                self.update_status("<span font='9' color='#ff7c43'>🎤 Đã chuyển sang chế độ Hát Live (Kích hoạt Auto-tune, Reverb &amp; Nhạc nền)</span>")
            GLib.timeout_add(3000, lambda: self.update_status("") or False)

    def adjust_pitch(self, delta):
        if self.is_podcast:
            return
        new_pitch = self.pitch_offset + delta
        if -6 <= new_pitch <= 6:
            self.pitch_offset = new_pitch
            self.update_pitch_label()
            
            try:
                with open(GENRE_FILE, "r") as f: data = json.load(f)
            except: data = {}
            data["pitch_offset"] = self.pitch_offset
            data["timestamp"] = time.time()
            with open(GENRE_FILE, "w") as f:
                json.dump(data, f)
                
            self.update_status(f"<span font='9' color='#ff7c43'>🎹 Đã chỉnh Tông nhạc: {self.pitch_offset:+} semitone</span>")
            GLib.timeout_add(2000, lambda: self.update_status("") or False)
            
    def update_pitch_label(self):
        if self.pitch_offset == 0:
            txt = "<span font='10' weight='bold' color='#ff7c43'>0 (Gốc)</span>"
        else:
            txt = f"<span font='10' weight='bold' color='#ff7c43'>{self.pitch_offset:+}</span>"
        self.lbl_tone_value.set_markup(txt)

    def on_autotune_toggle(self, switch, gparam):
        is_active = switch.get_active()
        try:
            with open(GENRE_FILE, "r") as f: data = json.load(f)
        except: data = {}
        data["autotune_enabled"] = is_active
        data["timestamp"] = time.time()
        with open(GENRE_FILE, "w") as f:
            json.dump(data, f)

    def play_sfx(self, widget, filename):
        import subprocess
        import threading
        dir_path = os.path.dirname(os.path.realpath(__file__))
        filepath = os.path.join(dir_path, "sounds", filename)
        if os.path.exists(filepath):
            node_name = f"sfx_play_{int(time.time() * 1000)}"
            # Sử dụng --volume 0.65 để giảm âm lượng tránh vỡ âm (clipping) khi phát cùng nhạc nền
            cmd = ["pw-play", "-P", f"{{ node.name = {node_name} }}", "--target", "0", "--volume", "0.65", filepath]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            def link_thread():
                start_time = time.time()
                while time.time() - start_time < 1.0:
                    try:
                        res = subprocess.run(["pw-link", "-o"], capture_output=True, text=True, timeout=0.5)
                        lines = res.stdout.splitlines()
                        matching_ports = [l.strip() for l in lines if node_name in l]
                        if matching_ports:
                            matching_ports.sort()
                            if len(matching_ports) == 1:
                                # Mono: Phát vào cả 2 kênh L và R
                                subprocess.run(["pw-link", matching_ports[0], REAPER_MUSIC_IN_L], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                subprocess.run(["pw-link", matching_ports[0], REAPER_MUSIC_IN_R], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            else:
                                # Stereo: Kênh L (cổng thứ 1) vào L, Kênh R (cổng thứ 2) vào R
                                # Tránh gộp chung cả L và R vào mỗi bên gây cộng dồn cường độ âm thanh (+6dB) làm vỡ tiếng
                                subprocess.run(["pw-link", matching_ports[0], REAPER_MUSIC_IN_L], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                subprocess.run(["pw-link", matching_ports[1], REAPER_MUSIC_IN_R], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            break
                    except:
                        pass
                    time.sleep(0.02)
            
            threading.Thread(target=link_thread, daemon=True).start()
            self.update_status(f"<span font='9' color='#38bdf8'>🔊 Đang phát hiệu ứng: {filename}</span>")
            GLib.timeout_add(3000, lambda: self.update_status("") or False)
        else:
            self.update_status(f"<span font='9' color='#e74c3c'>⚠️ Lỗi: Không thấy file {filename}</span>")

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

    def get_default_pipewire_nodes(self):
        import subprocess
        import re
        
        default_input = ""
        default_output = ""
        
        try:
            res = subprocess.run(["wpctl", "status"], capture_output=True, text=True, timeout=1.0)
            lines = res.stdout.splitlines()
            
            in_sources_section = False
            in_sinks_section = False
            
            default_in_id = ""
            default_out_id = ""
            
            for line in lines:
                line_strip = line.strip()
                if "Sinks:" in line:
                    in_sinks_section = True
                    in_sources_section = False
                elif "Sources:" in line:
                    in_sources_section = True
                    in_sinks_section = False
                elif line_strip.startswith("Sink endpoints:") or line_strip.startswith("Source endpoints:") or line_strip.startswith("Streams:"):
                    in_sinks_section = False
                    in_sources_section = False
                    
                if in_sinks_section and "*" in line:
                    match = re.search(r'\*\s+(\d+)\.', line)
                    if match:
                        default_out_id = match.group(1)
                        
                if in_sources_section and "*" in line:
                    match = re.search(r'\*\s+(\d+)\.', line)
                    if match:
                        default_in_id = match.group(1)
                        
            if default_in_id:
                res_inspect = subprocess.run(["wpctl", "inspect", default_in_id], capture_output=True, text=True, timeout=1.0)
                for l in res_inspect.stdout.splitlines():
                    if "node.name" in l:
                        m = re.search(r'node\.name\s*=\s*"([^"]+)"', l)
                        if m:
                            default_input = m.group(1)
                            break
                            
            if default_out_id:
                res_inspect = subprocess.run(["wpctl", "inspect", default_out_id], capture_output=True, text=True, timeout=1.0)
                for l in res_inspect.stdout.splitlines():
                    if "node.name" in l:
                        m = re.search(r'node\.name\s*=\s*"([^"]+)"', l)
                        if m:
                            default_output = m.group(1)
                            break
        except Exception as e:
            print(f"Error querying default devices: {e}")
            
        return default_input, default_output

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
            flags=0
        )
        dialog.set_default_size(320, 240)
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
        
        # Row 2: Box chứa 2 nút: Kết nối và Đóng (sát với hộp chọn thiết bị)
        btn_connect = Gtk.Button(label="🔌 Kết nối thiết bị")
        btn_connect.get_style_context().add_class("dialog-btn")
        btn_connect.get_style_context().add_class("ok-btn")
        
        btn_close = Gtk.Button(label="Đóng")
        btn_close.get_style_context().add_class("dialog-btn")
        btn_close.get_style_context().add_class("cancel-btn")
        
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.pack_start(btn_connect, True, True, 0)
        btn_box.pack_start(btn_close, True, True, 0)
        grid.attach(btn_box, 0, 2, 2, 1)
        
        # Row 3: Đường phân cách
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        grid.attach(sep, 0, 3, 2, 1)
        
        # Row 4: Nút Khởi tạo project hát karaoke ở đáy
        btn_setup = Gtk.Button()
        btn_setup.get_style_context().add_class("setup-btn")
        setup_inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        setup_inner.set_halign(Gtk.Align.CENTER)
        setup_icon = Gtk.Label(label="⚡")
        setup_icon.get_style_context().add_class("setup-icon")
        setup_text = Gtk.Label(label="Khởi tạo project hát karaoke")
        setup_text.get_style_context().add_class("setup-text")
        setup_inner.pack_start(setup_icon, False, False, 0)
        setup_inner.pack_start(setup_text, False, False, 0)
        btn_setup.add(setup_inner)
        grid.attach(btn_setup, 0, 4, 2, 1)
        
        # Nhãn trạng thái kết nối dưới cùng (Đã loại bỏ để tránh làm giãn thành phần)
        
        def show_message(title, message, msg_type=Gtk.MessageType.INFO):
            msg_dialog = Gtk.MessageDialog(
                transient_for=dialog,
                flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                message_type=msg_type,
                buttons=Gtk.ButtonsType.OK,
                text=title
            )
            msg_dialog.format_secondary_text(message)
            msg_dialog.run()
            msg_dialog.destroy()
 
        def connect_devices():
            """Kết nối thiết bị đã chọn và ghi nhớ — không đóng dialog."""
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
            parts = []
            if new_in: parts.append(f"Mic: {self.get_device_friendly_name(new_in)}")
            if new_out: parts.append(f"Loa: {self.get_device_friendly_name(new_out)}")
            msg = "\n".join(parts) if parts else "Giữ nguyên thiết bị"
            
            show_message("Kết Nối Thiết Bị Thành Công", f"Đã cấu hình và kết nối âm thanh:\n{msg}")
            
            self.update_status(f"<span font='9' color='#2ecc71'>đã áp dụng cấu hình!</span>")
            GLib.timeout_add(3000, lambda: self.update_status("") or False)
 
        def on_setup_project_clicked(button):
            try:
                setup_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setup_karaoke.lua")
                subprocess.run(["/opt/REAPER/reaper", "-nonewinst", setup_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                fix_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix_master.lua")
                subprocess.run(["/opt/REAPER/reaper", "-nonewinst", fix_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                show_message("Khởi Tạo Thành Công", "Project REAPER Karaoke đã được thiết lập thành công!")
                
                self.update_status("<span font='9' color='#2ecc71'>⚡ Đã thiết lập Project REAPER v6!</span>")
                GLib.timeout_add(4000, lambda: self.update_status("") or False)
            except Exception as e:
                show_message("Lỗi Thiết Lập", f"Không thể khởi tạo project:\n{str(e)}", Gtk.MessageType.ERROR)
                
        btn_connect.connect("clicked", lambda w: connect_devices())
        btn_close.connect("clicked", lambda w: dialog.response(Gtk.ResponseType.CLOSE))
        btn_setup.connect("clicked", on_setup_project_clicked)
        
        content_area.add(grid)
        dialog.show_all()
        dialog.run()  # Chạy cho đến khi user bấm Đóng
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
    def on_destroy(widget):
        Gtk.main_quit()
        try:
            import signal
            os.kill(0, signal.SIGINT)
        except:
            pass
    win.connect("destroy", on_destroy)
    win.show_all()
    Gtk.main()
