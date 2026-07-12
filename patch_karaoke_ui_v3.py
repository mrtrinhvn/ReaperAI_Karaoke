import os
import re

APP_FILE = "karaoke_app.py"

with open(APP_FILE, "r") as f:
    content = f.read()

# 1. Remove Notebook and replace with a main vbox
notebook_code = """        # Sử dụng Notebook để chia Tab
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
            print(f"Lỗi nạp Studio Tab: {e}")"""

new_main_box = """        # Giao diện Gộp
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        try:
            from studio_tab import StudioTab
            self.studio_tab = StudioTab(self)
        except Exception as e:
            print(f"Lỗi nạp Studio Tab: {e}")
            self.studio_tab = None"""

content = content.replace(notebook_code, new_main_box)

# 2. Replace the old header & big flowbox
flowbox_code_start = """        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)"""

flowbox_code_end = """        self.buttons = {}"""

new_genre_placeholder = """        # (Header UI has been moved below after initialization of current_saved)
        self.buttons = {}"""

regex_flowbox = re.compile(re.escape(flowbox_code_start) + r".*?" + re.escape(flowbox_code_end), re.DOTALL)
content = regex_flowbox.sub(new_genre_placeholder, content)

# 3. Insert the new Header (ComboBox + Analyze Btn) AFTER current_saved is read
insert_after_line = """        except: pass

        for key, p in PRESETS.items():"""

new_header = """        except: pass

        # New Header Box for Genre ComboBox & Analyze Button
        genre_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        lbl = Gtk.Label(label="<span font='12' weight='bold' color='#a78bfa'>🎤 Thể Loại:</span>", use_markup=True)
        genre_row.pack_start(lbl, False, False, 0)
        
        self.genre_combo = Gtk.ComboBoxText()
        for key, p in PRESETS.items():
            self.genre_combo.append(key, f"{p['emoji']} {p['name']}")
        
        active_idx = list(PRESETS.keys()).index(current_saved) if current_saved in PRESETS else 0
        self.genre_combo.set_active(active_idx)
        self.genre_combo.connect("changed", self.on_genre_combo_changed)
        genre_row.pack_start(self.genre_combo, True, True, 0)
        
        # Nút Phân tích giọng (di chuyển lên đây)
        self.analyze_btn = Gtk.Button()
        self.analyze_btn.set_name("analyze-btn")
        self.analyze_btn.get_style_context().add_class("analyze-btn")
        self.analyze_lbl = Gtk.Label(label="<span font='10' weight='bold' color='#ffffff'>🎙️ Phân Tích</span>", use_markup=True)
        self.analyze_btn.add(self.analyze_lbl)
        self.analyze_btn.connect("clicked", self.on_analyze_clicked)
        genre_row.pack_start(self.analyze_btn, False, False, 0)
        
        settings_btn = Gtk.Button()
        settings_btn.get_style_context().add_class("settings-btn")
        settings_lbl = Gtk.Label(label="<span font='14'>⚙️</span>", use_markup=True)
        settings_btn.add(settings_lbl)
        settings_btn.connect("clicked", self.on_settings_clicked)
        genre_row.pack_start(settings_btn, False, False, 0)
        
        vbox.pack_start(genre_row, False, False, 0)
        
        if getattr(self, "studio_tab", None):
            vbox.pack_start(self.studio_tab, True, True, 0)

        # Bỏ qua việc tạo nút to (flowbox), ta đè lên hàm on_genre_clicked cũ:
        def dummy_on_genre_clicked(widget, key): pass
        self.on_genre_clicked = dummy_on_genre_clicked

        for key, p in PRESETS.items():"""

content = content.replace(insert_after_line, new_header)

# 4. Remove old flowbox logic
remove_flowbox_regex = re.compile(r'self\.buttons\[key\] = btn\s*flowbox\.insert\(btn, -1\)', re.DOTALL)
content = remove_flowbox_regex.sub('self.buttons[key] = btn\n            pass # flowbox removed', content)

# Remove the old Analyze Button code from tools_box
old_analyze_btn_regex = re.compile(r'\s*# Nút Phân tích giọng \(Auto-Calibration\).*?tools_box\.pack_start\(self\.analyze_btn, True, True, 0\)', re.DOTALL)
content = old_analyze_btn_regex.sub('', content)

# 5. Add on_genre_combo_changed
combo_handler = """    def on_genre_combo_changed(self, combo):
        active_id = combo.get_active_id()
        if not active_id:
            idx = combo.get_active()
            active_id = list(PRESETS.keys())[idx]
        
        try:
            with open(GENRE_FILE, "r") as f:
                data = json.load(f)
            data["genre"] = active_id
            data["name"] = PRESETS[active_id]["name"]
            data["bpm_suggest"] = PRESETS[active_id]["bpm_suggest"]
            
            for k, v in PRESETS[active_id].items():
                data[k] = v
                
            with open(GENRE_FILE, "w") as f:
                json.dump(data, f)
                
            self.bpm_scale.set_value(data["bpm_suggest"])
        except Exception as e:
            print("Error changing genre:", e)

    def on_settings_clicked"""

content = content.replace("    def on_settings_clicked", combo_handler)

with open(APP_FILE, "w") as f:
    f.write(content)
