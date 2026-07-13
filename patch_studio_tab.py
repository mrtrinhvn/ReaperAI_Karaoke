import os
import re

FILE_PATH = "studio_tab.py"

with open(FILE_PATH, "r") as f:
    content = f.read()

# 1. Add the TargetProgressBar class
custom_widget_code = """
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

class StudioTab(Gtk.Box):"""

content = content.replace("class StudioTab(Gtk.Box):", custom_widget_code)

# 2. Use TargetProgressBar instead of Gtk.ProgressBar
content = content.replace("pbar = Gtk.ProgressBar()", "pbar = TargetProgressBar()")

# 3. Update the UI update loop
old_update_loop = """        # 1. Update Progress bars
        for i, val in enumerate(self.audio_spectrum):
            ref = self.ref_spectrum[i]
            frac = min(1.0, val / max(30.0, ref + 10.0))
            self.spectrum_bars[i].set_fraction(frac)
            
            diff = val - ref
            if abs(diff) < 4:"""

new_update_loop = """        # 1. Update Progress bars
        for i, val in enumerate(self.audio_spectrum):
            ref = self.ref_spectrum[i]
            
            # Tính toán tỷ lệ dựa trên max_scale
            max_scale = max(30.0, ref + 10.0)
            val_frac = val / max_scale
            ref_frac = ref / max_scale
            tol_frac = 4.0 / max_scale # Khoảng chuẩn (dung sai 4%)
            
            self.spectrum_bars[i].set_fraction_with_target(val_frac, ref_frac, tol_frac)
            
            diff = val - ref
            if abs(diff) < 4:"""

content = content.replace(old_update_loop, new_update_loop)

with open(FILE_PATH, "w") as f:
    f.write(content)
