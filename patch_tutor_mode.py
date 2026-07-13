import os
import re

FILE_PATH = "studio_tab.py"

with open(FILE_PATH, "r") as f:
    content = f.read()

# 1. Update the loop to create buttons instead of labels
old_grid_loop = """        for i, name in enumerate(bands_names):
            name_lbl = Gtk.Label(use_markup=True)
            name_lbl.set_markup(f"<span font='9'>{name}</span>")
            name_lbl.set_halign(Gtk.Align.START)
            grid.attach(name_lbl, 0, i, 1, 1)"""

new_grid_loop = """        self.selected_tutor_band = None
        for i, name in enumerate(bands_names):
            name_btn = Gtk.Button()
            name_btn.set_relief(Gtk.ReliefStyle.NONE)
            name_btn_lbl = Gtk.Label(use_markup=True)
            name_btn_lbl.set_markup(f"<span font='9' color='#8caaee'>👉 {name}</span>")
            name_btn.add(name_btn_lbl)
            name_btn.set_halign(Gtk.Align.START)
            name_btn.connect("clicked", self.on_band_clicked, i)
            grid.attach(name_btn, 0, i, 1, 1)"""

content = content.replace(old_grid_loop, new_grid_loop)

# 2. Add the on_band_clicked method and band DB
old_tutor_switch = """        self.tutor_switch = Gtk.Switch()"""

new_tutor_switch = """        self.band_advice_db = {
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

        self.tutor_switch = Gtk.Switch()"""

content = content.replace(old_tutor_switch, new_tutor_switch)

# 3. Rewrite Update Tutor Text logic
old_tutor_update_start = """        # 2. Update Tutor Text
        if self.tutor_switch.get_active():
            feedback = ["🎓 HƯỚNG DẪN KỸ SƯ ÂM THANH:"]
            
            # Đánh giá Bass (Band 1)
            dbass = self.audio_spectrum[1] - self.ref_spectrum[1]
            if dbass > 7:
                feedback.append("- Dải Bass (80-250) đang quá DƯ. Giọng ùng ùng. 👉 Mở FX > ReaEQ > Chọn vòng số 1 (Low Shelf): Giảm nút Gain xuống khoảng -2dB.")
            elif dbass < -7:
                feedback.append("- Dải Bass (80-250) đang bị THIẾU. Giọng mỏng tang. 👉 Mở FX > ReaEQ > Chọn vòng số 1 (Low Shelf): Tăng Gain lên khoảng +1.5dB.")
                
            # Đánh giá LMid (Band 2)
            dlmid = self.audio_spectrum[2] - self.ref_spectrum[2]
            if dlmid > 8:
                feedback.append("- Dải Low-Mid (250-500) đang DƯ. Tiếng bị um / ồm. 👉 Mở FX > ReaEQ > Chọn vòng số 2 (Band): Giảm Gain xuống khoảng -4dB để dọn sạch.")
                
            # Đánh giá Mid (Band 3)
            dmid = self.audio_spectrum[3] - self.ref_spectrum[3]
            if dmid < -6:
                feedback.append("- Dải Mid (500-1k) đang THIẾU. Tiếng hát bị chìm sâu. 👉 Mở FX > ReaEQ > Chọn vòng số 3 (Band): Nhích Gain lên +2dB để rõ lời.")
                
            # Đánh giá Air (Band 4)
            dair = self.audio_spectrum[7] - self.ref_spectrum[7]
            if dair > 2:
                feedback.append("- Dải Air (8k-16k) đang DƯ. Tiếng xì chói tai (Sibilance). 👉 Mở FX > ReaEQ > Chọn vòng số 4 (High Shelf): Giảm Gain đi -1.5dB.")
                
            buf = self.tutor_textview.get_buffer()
            if len(feedback) > 1:
                buf.set_text("\\n\\n".join(feedback))
            else:
                buf.set_text("🎓 HƯỚNG DẪN KỸ SƯ ÂM THANH:\\n\\n✅ Tuyệt vời! Các dải tần đang nằm trong mức an toàn so với file mẫu. Hãy duy trì kỹ thuật và EQ này.")"""

new_tutor_update = """        # 2. Update Tutor Text
        buf = self.tutor_textview.get_buffer()
        if not self.tutor_switch.get_active():
            buf.set_text("Đang ẩn hướng dẫn (Chế độ chuyên gia). Bật 'Hướng dẫn bằng chữ' để xem AI Tutor.")
        else:
            if self.selected_tutor_band is None:
                buf.set_text("🎓 HƯỚNG DẪN CĂN CHỈNH:\\n\\n👆 Bấm vào tên một dải tần số (Ví dụ: 👉 Bass, 👉 Mid...) ở bảng trên để xem phân tích và hướng dẫn vặn REAPER cho dải tần đó.")
            else:
                idx = self.selected_tutor_band
                val = self.audio_spectrum[idx]
                ref = self.ref_spectrum[idx]
                diff = val - ref
                
                b_name, b_eq, b_high, b_low = self.band_advice_db[idx]
                
                feedback = f"🎓 PHÂN TÍCH DẢI TẦN: {b_name}\\n"
                feedback += f"▶ Tín hiệu hiện tại: {val:.1f}% | Vùng chuẩn: {ref:.1f}%\\n\\n"
                
                if abs(diff) <= 4.0:
                    feedback += "✅ TUYỆT VỜI! Dải tần này đang nằm gọn trong vùng an toàn (xanh lơ). Hãy giữ nguyên thiết lập hiện tại."
                elif diff > 4.0:
                    feedback += f"🔴 CẢNH BÁO: Đang DƯ thừa (+{diff:.1f}%)\\n"
                    feedback += f"- Biểu hiện: Giọng sẽ bị {b_high}. Thanh tín hiệu văng khỏi vùng chuẩn.\\n"
                    feedback += f"- Cách chỉnh: 👉 Mở FX > ReaEQ > Chọn {b_eq}: GIẢM nút Gain xuống từ từ cho đến khi thanh tín hiệu tụt vào vùng xanh lơ."
                else:
                    feedback += f"🔴 CẢNH BÁO: Đang THIẾU hụt ({diff:.1f}%)\\n"
                    feedback += f"- Biểu hiện: Giọng sẽ bị {b_low}. Thanh tín hiệu tụt ra khỏi vùng chuẩn.\\n"
                    feedback += f"- Cách chỉnh: 👉 Mở FX > ReaEQ > Chọn {b_eq}: TĂNG nút Gain lên từ từ cho đến khi thanh tín hiệu lọt vào vùng xanh lơ."
                    
                buf.set_text(feedback)"""

content = content.replace(old_tutor_update_start, new_tutor_update)

with open(FILE_PATH, "w") as f:
    f.write(content)
