import os

FILE_PATH = "studio_tab.py"

with open(FILE_PATH, "r") as f:
    content = f.read()

# 1. Thinner bars in TargetProgressBar
old_draw_bar = """        # Vạch tín hiệu thực tế
        bar_width = self.value * width
        diff = abs(self.value - self.target)
        if diff <= self.tolerance:
            cr.set_source_rgba(0.0, 0.8, 1.0, 0.9) # Xanh lơ (đạt)
        else:
            cr.set_source_rgba(1.0, 0.3, 0.3, 0.9) # Đỏ (lệch)
            
        cr.rectangle(0, height * 0.25, bar_width, height * 0.5) # Thanh mỏng ở giữa
        cr.fill()"""

new_draw_bar = """        # Vạch tín hiệu thực tế cực mỏng
        bar_width = self.value * width
        diff = abs(self.value - self.target)
        if diff <= self.tolerance:
            cr.set_source_rgba(0.0, 0.9, 1.0, 1.0) # Xanh lơ rực
        else:
            cr.set_source_rgba(1.0, 0.2, 0.2, 1.0) # Đỏ rực
            
        cr.rectangle(0, height * 0.4, bar_width, height * 0.2) # Rất mỏng
        cr.fill()"""

content = content.replace(old_draw_bar, new_draw_bar)

# 2. Add Spatial FX grid to __init__
old_pack_grid = """        self.pack_start(grid, False, False, 5)"""

new_pack_grid = """        self.pack_start(grid, False, False, 5)
        
        # --- Khối Không Gian & Reverb ---
        space_lbl = Gtk.Label(use_markup=True)
        space_lbl.set_markup("<span font='10' weight='bold' color='#f38ba8'>🌌 Không gian & Độ Vang (Target)</span>")
        space_lbl.set_halign(Gtk.Align.START)
        self.pack_start(space_lbl, False, False, 0)
        
        space_grid = Gtk.Grid()
        space_grid.set_column_spacing(10)
        space_grid.set_row_spacing(5)
        
        self.space_bars = []
        space_names = ["Kích thước phòng (Room)", "Độ ướt (Wet/Level)", "Độ nghẹt (Damp)", "Độ rộng (Width)"]
        
        for i, name in enumerate(space_names):
            name_lbl = Gtk.Label(use_markup=True)
            name_lbl.set_markup(f"<span font='9'>{name}</span>")
            name_lbl.set_halign(Gtk.Align.START)
            space_grid.attach(name_lbl, 0, i, 1, 1)
            
            pbar = TargetProgressBar()
            space_grid.attach(pbar, 1, i, 1, 1)
            self.space_bars.append(pbar)
            
        self.pack_start(space_grid, False, False, 5)"""

content = content.replace(old_pack_grid, new_pack_grid)

# 3. Update spatial bars in update_studio_ui
old_update_ui = """            diff = val - ref
            if abs(diff) < 4:
                status = "✅"
            else:
                status = "📈" if diff > 0 else "📉"
            self.spectrum_labels[i].set_markup(f"<span font='9'>{val:.1f}% ({status})</span>")
            
        buf = self.tutor_textview.get_buffer()"""

new_update_ui = """            diff = val - ref
            if abs(diff) < 4:
                status = "✅"
            else:
                status = "📈" if diff > 0 else "📉"
            self.spectrum_labels[i].set_markup(f"<span font='9'>{val:.1f}% ({status})</span>")
            
        # Update Spatial bars based on current genre presets
        try:
            import json
            with open(os.path.join(os.path.dirname(__file__), "genre_state.json"), "r") as f:
                data = json.load(f)
                
            self.space_bars[0].set_fraction_with_target(data.get("reverb_room", 0.5), data.get("reverb_room", 0.5), 0.05)
            self.space_bars[1].set_fraction_with_target(data.get("reverb_wet", 0.3), data.get("reverb_wet", 0.3), 0.05)
            self.space_bars[2].set_fraction_with_target(data.get("reverb_damp", 0.5), data.get("reverb_damp", 0.5), 0.05)
            self.space_bars[3].set_fraction_with_target(data.get("reverb_width", 1.0), data.get("reverb_width", 1.0), 0.05)
        except Exception:
            pass
            
        buf = self.tutor_textview.get_buffer()"""

content = content.replace(old_update_ui, new_update_ui)

with open(FILE_PATH, "w") as f:
    f.write(content)
