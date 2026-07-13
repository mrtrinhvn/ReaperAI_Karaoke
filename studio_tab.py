import gi
import time
import subprocess
import threading
import json
import os
import numpy as np
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


class TargetProgressBar(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(150, 15)
        self.value = 0.0
        self.target = 0.0
        self.tolerance = 0.0
        self.connect("draw", self.on_draw)

    def set_fraction_with_target(self, value, target, tolerance):
        self.value = min(1.0, max(0.0, value))
        self.target = min(1.0, max(0.0, target))
        self.tolerance = tolerance
        self.queue_draw()

    def on_draw(self, widget, cr):
        width = self.get_allocated_width()
        height = self.get_allocated_height()

        # Draw background (dark gray)
        cr.set_source_rgb(0.15, 0.15, 0.2)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        # Draw target zone (green semi-transparent)
        target_x = max(0, (self.target - self.tolerance) * width)
        target_w = (self.tolerance * 2) * width
        cr.set_source_rgba(0.2, 0.8, 0.2, 0.25)
        cr.rectangle(target_x, 0, target_w, height)
        cr.fill()

        # Draw target center line (white, thin)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.6)
        cr.set_line_width(1.0)
        cr.move_to(self.target * width, 0)
        cr.line_to(self.target * width, height)
        cr.stroke()

        # Draw value bar
        bar_width = self.value * width
        diff = abs(self.value - self.target)
        if diff <= self.tolerance:
            cr.set_source_rgba(0.3, 0.8, 1.0, 0.8) # Cyan when inside target
        else:
            cr.set_source_rgba(0.9, 0.3, 0.3, 0.8) # Red when outside target
            
        cr.rectangle(0, height * 0.25, bar_width, height * 0.5) # Thinner bar in the middle
        cr.fill()
        
        return False

class StudioTab(Gtk.Box):
    def __init__(self, parent_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_border_width(10)
        self.parent_window = parent_window
        
        # 1. Header
        lbl = Gtk.Label(use_markup=True)
        lbl.set_markup("<span font='14' weight='bold' color='#38bdf8'>🎓 Kỹ Sư Âm Thanh (AI Tutor)</span>")
        lbl.set_halign(Gtk.Align.START)
        self.pack_start(lbl, False, False, 5)
        
        desc_lbl = Gtk.Label(label="Phân tích giọng thật và hướng dẫn vặn FX trong REAPER.")
        desc_lbl.set_halign(Gtk.Align.START)
        self.pack_start(desc_lbl, False, False, 0)
        
        # 2. Spectrum Visualizer (8 Bands)
        self.spectrum_bars = []
        self.spectrum_labels = []
        bands_names = ["Sub (20-80)", "Bass (80-250)", "LMid (250-500)", "Mid (500-1k)", 
                       "UMid (1k-2.5k)", "Pres (2.5k-5k)", "Bright (5k-8k)", "Air (8k-16k)"]
        
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(5)
        
        self.selected_tutor_band = None
        for i, name in enumerate(bands_names):
            name_btn = Gtk.Button()
            name_btn.set_relief(Gtk.ReliefStyle.NONE)
            name_btn_lbl = Gtk.Label(use_markup=True)
            name_btn_lbl.set_markup(f"<span font='9' color='#8caaee'>👉 {name}</span>")
            name_btn.add(name_btn_lbl)
            name_btn.set_halign(Gtk.Align.START)
            name_btn.connect("clicked", self.on_band_clicked, i)
            grid.attach(name_btn, 0, i, 1, 1)
            
            pbar = TargetProgressBar()
            pbar.set_size_request(150, 15)
            grid.attach(pbar, 1, i, 1, 1)
            self.spectrum_bars.append(pbar)
            
            val_lbl = Gtk.Label(use_markup=True)
            val_lbl.set_markup("<span font='9'>0.0%</span>")
            grid.attach(val_lbl, 2, i, 1, 1)
            self.spectrum_labels.append(val_lbl)
            
        self.pack_start(grid, False, False, 5)
        
        # 3. Mode Switch
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        mode_box.pack_start(Gtk.Label(label="Chế độ:"), False, False, 0)
        
        self.band_advice_db = {
            0: ("Sub (20-80Hz)", "Low Shelf", "ùng ùng, ù nền", "mỏng, thiếu lực đáy"),
            1: ("Bass (80-250Hz)", "Low Shelf (Band 1)", "đục, ồm ồm", "mỏng tang, thiếu ấm"),
            2: ("LMid (250-500Hz)", "Band (Band 2)", "um, như bị nghẹt mũi", "rỗng, thiếu độ dày"),
            3: ("Mid (500-1kHz)", "Band (Band 3)", "vọng ống bơ, oang oang", "chìm sâu, không rõ lời"),
            4: ("UMid (1k-2.5kHz)", "Band (Band 3)", "gắt, điếc tai", "thiếu sức sống, mờ nhạt"),
            5: ("Pres (2.5k-5kHz)", "Band (Band 4)", "đanh, rát tai", "kém hiện diện"),
            6: ("Bright (5k-8kHz)", "High Shelf (Band 4)", "xé tiếng, gắt gỏng", "tối, đục tiếng"),
            7: ("Air (8k-16kHz)", "High Shelf (Band 4)", "xì chói tai (Sibilance)", "bí bách, kém bay bổng")
        }

    def on_band_clicked(self, widget, band_idx):
        self.selected_tutor_band = band_idx

        self.tutor_switch = Gtk.Switch()
        self.tutor_switch.set_active(True)
        mode_box.pack_start(self.tutor_switch, False, False, 0)
        mode_box.pack_start(Gtk.Label(label="Hướng dẫn bằng chữ (Tutor Mode)"), False, False, 0)
        
        self.pack_start(mode_box, False, False, 10)
        
        # 4. Tutor Feedback Text Box
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(100)
        self.tutor_textview = Gtk.TextView()
        self.tutor_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.tutor_textview.set_editable(False)
        self.tutor_textview.set_cursor_visible(False)
        
        # Thêm màu nền tối và chữ sáng cho textview
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"textview { background-color: #1e1e2e; color: #cdd6f4; font-size: 10pt; }")
        context = self.tutor_textview.get_style_context()
        context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        scrolled.add(self.tutor_textview)
        self.pack_start(scrolled, True, True, 5)
        
        # 5. Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        ref_btn = Gtk.Button(label="📁 Nạp File Mẫu (Match EQ)")
        ref_btn.connect("clicked", self.on_ref_file_clicked)
        btn_box.pack_start(ref_btn, True, True, 0)
        
        self.pack_start(btn_box, False, False, 5)
        
        # Variables
        self.audio_spectrum = [0.0] * 8
        self.ref_spectrum = [14.2, 24.8, 36.0, 18.7, 4.8, 0.9, 0.2, 0.3] # Default reference
        self.is_listening = True
        
        # Bắt đầu luồng nghe âm thanh
        t = threading.Thread(target=self.audio_listener_thread, daemon=True)
        t.start()
        
        # Hẹn giờ cập nhật UI
        GLib.timeout_add(500, self.update_studio_ui)

    def on_ref_file_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Chọn file nhạc mẫu (WAV/MP3)",
            parent=self.parent_window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        filter_audio = Gtk.FileFilter()
        filter_audio.set_name("Audio files")
        filter_audio.add_mime_type("audio/wav")
        filter_audio.add_mime_type("audio/mpeg")
        dialog.add_filter(filter_audio)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            self.analyze_reference_file(filepath)
        
        dialog.destroy()
        
    def analyze_reference_file(self, filepath):
        buf = self.tutor_textview.get_buffer()
        buf.set_text(f"⏳ Đang phân tích phổ tần file:\n{filepath}\nVui lòng đợi vài giây...")
        
        def run_analysis():
            try:
                cmd = ["ffmpeg", "-i", filepath, "-f", "f32le", "-ac", "1", "-ar", "48000", "-"]
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                raw, _ = p.communicate()
                
                samples = np.frombuffer(raw, dtype=np.float32)
                
                sr = 48000
                from numpy.fft import rfft, rfftfreq
                freqs = rfftfreq(len(samples), 1.0/sr)
                fft = np.abs(rfft(samples)) / len(samples)
                
                bands = [
                    (20, 80), (80, 250), (250, 500), (500, 1000), 
                    (1000, 2500), (2500, 5000), (5000, 8000), (8000, 16000)
                ]
                
                total = sum(np.sum(fft[(freqs >= lo) & (freqs < hi)]**2) for lo,hi in bands)
                if total > 0:
                    new_ref = []
                    for lo, hi in bands:
                        e = np.sum(fft[(freqs >= lo) & (freqs < hi)]**2) / total * 100
                        new_ref.append(e)
                    self.ref_spectrum = new_ref
                    
                    def update_success():
                        buf = self.tutor_textview.get_buffer()
                        buf.set_text(f"✅ Đã phân tích xong File Mẫu!\nThông số chuẩn mới đã được áp dụng để so sánh.")
                    GLib.idle_add(update_success)
            except Exception as e:
                def update_err():
                    buf = self.tutor_textview.get_buffer()
                    buf.set_text(f"❌ Lỗi phân tích: {e}")
                GLib.idle_add(update_err)
                
        threading.Thread(target=run_analysis, daemon=True).start()

    def audio_listener_thread(self):
        bands = [
            (20, 80), (80, 250), (250, 500), (500, 1000), 
            (1000, 2500), (2500, 5000), (5000, 8000), (8000, 16000)
        ]
        
        while self.is_listening:
            try:
                try:
                    reaper_id = subprocess.check_output(
                        "pw-dump | jq '.[] | select(.info.props[\"node.name\"] == \"REAPER\") | .id' | head -n 1", 
                        shell=True, text=True
                    ).strip()
                    target = reaper_id if reaper_id else "528967"
                except Exception:
                    target = "528967"
                    
                cmd = ['pw-record', '--target', target, '--format', 'f32', '--rate', '48000', '--channels', '2', '-']
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                
                chunk_size = 48000 * 2 * 4 # 1 second chunk
                
                while self.is_listening:
                    data = p.stdout.read(chunk_size)
                    if not data:
                        time.sleep(0.1)
                        break # Trở lại vòng lặp ngoài để khởi động lại tiến trình
                        
                    s = np.frombuffer(data, np.float32).reshape(-1, 2)
                    mono = (s[:, 0] + s[:, 1]) / 2
                    
                    rms = 20 * np.log10(np.sqrt(np.mean(mono**2)) + 1e-10)
                    if rms > -45: # Chỉ phân tích khi có tiếng (để biểu đồ không chạy loạn khi im lặng)
                        from numpy.fft import rfft, rfftfreq
                        freqs = rfftfreq(len(mono), 1.0/48000)
                        fft = np.abs(rfft(mono)) / len(mono)
                        
                        total = sum(np.sum(fft[(freqs >= lo) & (freqs < hi)]**2) for lo,hi in bands)
                        if total > 0:
                            new_spec = []
                            for lo, hi in bands:
                                e = np.sum(fft[(freqs >= lo) & (freqs < hi)]**2) / total * 100
                                new_spec.append(e)
                            self.audio_spectrum = new_spec
            except Exception:
                time.sleep(1)

    def update_studio_ui(self):
        # 1. Update Progress bars
        for i, val in enumerate(self.audio_spectrum):
            ref = self.ref_spectrum[i]
            
            # Tính toán tỷ lệ dựa trên max_scale
            max_scale = max(30.0, ref + 10.0)
            val_frac = val / max_scale
            ref_frac = ref / max_scale
            tol_frac = 4.0 / max_scale # Khoảng chuẩn (dung sai 4%)
            
            self.spectrum_bars[i].set_fraction_with_target(val_frac, ref_frac, tol_frac)
            
            diff = val - ref
            if abs(diff) < 4:
                status = "✅"
            else:
                status = "📈" if diff > 0 else "📉"
            self.spectrum_labels[i].set_markup(f"<span font='9'>{val:.1f}% ({status})</span>")
            
        # 2. Update Tutor Text
        buf = self.tutor_textview.get_buffer()
        if not self.tutor_switch.get_active():
            buf.set_text("Đang ẩn hướng dẫn (Chế độ chuyên gia). Bật 'Hướng dẫn bằng chữ' để xem AI Tutor.")
        else:
            if self.selected_tutor_band is None:
                buf.set_text("🎓 HƯỚNG DẪN CĂN CHỈNH:\n\n👆 Bấm vào tên một dải tần số (Ví dụ: 👉 Bass, 👉 Mid...) ở bảng trên để xem phân tích và hướng dẫn vặn REAPER cho dải tần đó.")
            else:
                idx = self.selected_tutor_band
                val = self.audio_spectrum[idx]
                ref = self.ref_spectrum[idx]
                diff = val - ref
                
                b_name, b_eq, b_high, b_low = self.band_advice_db[idx]
                
                feedback = f"🎓 PHÂN TÍCH DẢI TẦN: {b_name}\n"
                feedback += f"▶ Tín hiệu hiện tại: {val:.1f}% | Vùng chuẩn: {ref:.1f}%\n\n"
                
                if abs(diff) <= 4.0:
                    feedback += "✅ TUYỆT VỜI! Dải tần này đang nằm gọn trong vùng an toàn (xanh lơ). Hãy giữ nguyên thiết lập hiện tại."
                elif diff > 4.0:
                    feedback += f"🔴 CẢNH BÁO: Đang DƯ thừa (+{diff:.1f}%)\n"
                    feedback += f"- Biểu hiện: Giọng sẽ bị {b_high}. Thanh tín hiệu văng khỏi vùng chuẩn.\n"
                    feedback += f"- Cách chỉnh: 👉 Mở FX > ReaEQ > Chọn {b_eq}: GIẢM nút Gain xuống từ từ cho đến khi thanh tín hiệu tụt vào vùng xanh lơ."
                else:
                    feedback += f"🔴 CẢNH BÁO: Đang THIẾU hụt ({diff:.1f}%)\n"
                    feedback += f"- Biểu hiện: Giọng sẽ bị {b_low}. Thanh tín hiệu tụt ra khỏi vùng chuẩn.\n"
                    feedback += f"- Cách chỉnh: 👉 Mở FX > ReaEQ > Chọn {b_eq}: TĂNG nút Gain lên từ từ cho đến khi thanh tín hiệu lọt vào vùng xanh lơ."
                    
                buf.set_text(feedback)
                
        return True
