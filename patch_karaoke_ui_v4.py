import os
import re

APP_FILE = "karaoke_app.py"

with open(APP_FILE, "r") as f:
    content = f.read()

combo_code_start = """        # New Header Box for Genre ComboBox & Analyze Button"""
combo_code_end = """        genre_row.pack_start(self.analyze_btn, False, False, 0)"""

new_genre_flowbox = """        # --- DÃY NÚT CHỌN THỂ LOẠI (THAY CHO COMBOBOX BỊ LỖI LÒI LÊN TRỜI) ---
        genre_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        lbl = Gtk.Label(label="<span font='12' weight='bold' color='#a78bfa'>🎤 Thể Loại:</span>", use_markup=True)
        lbl.set_valign(Gtk.Align.START)
        genre_row.pack_start(lbl, False, False, 5)
        
        self.genre_flow = Gtk.FlowBox()
        self.genre_flow.set_valign(Gtk.Align.START)
        self.genre_flow.set_max_children_per_line(3) # 3 cột
        self.genre_flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.genre_flow.set_row_spacing(5)
        self.genre_flow.set_column_spacing(5)
        
        self.genre_keys = list(PRESETS.keys())
        active_idx = self.genre_keys.index(current_saved) if current_saved in self.genre_keys else 0
        
        for key in self.genre_keys:
            p = PRESETS[key]
            lbl_btn = Gtk.Label(label=f"<span font='9'>{p['emoji']} {p['name']}</span>", use_markup=True)
            box = Gtk.Box()
            box.set_border_width(3)
            box.add(lbl_btn)
            self.genre_flow.insert(box, -1)
            
        self.genre_flow.connect("child-activated", self.on_genre_flow_activated)
        
        # Chọn mục mặc định
        child_to_select = self.genre_flow.get_child_at_index(active_idx)
        if child_to_select:
            self.genre_flow.select_child(child_to_select)
            
        genre_row.pack_start(self.genre_flow, True, True, 0)
        
        # Nút Phân tích giọng (bên phải)
        tools_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.analyze_btn = Gtk.Button()
        self.analyze_btn.set_name("analyze-btn")
        self.analyze_btn.get_style_context().add_class("analyze-btn")
        self.analyze_lbl = Gtk.Label(label="<span font='10' weight='bold' color='#ffffff'>🎙️ Phân Tích</span>", use_markup=True)
        self.analyze_btn.add(self.analyze_lbl)
        self.analyze_btn.connect("clicked", self.on_analyze_clicked)
        tools_col.pack_start(self.analyze_btn, False, False, 0)"""

regex_combo = re.compile(re.escape(combo_code_start) + r".*?" + re.escape(combo_code_end), re.DOTALL)
content = regex_combo.sub(new_genre_flowbox, content)

# Remove on_genre_combo_changed and add on_genre_flow_activated
combo_handler_code = """    def on_genre_combo_changed(self, combo):
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
            print("Error changing genre:", e)"""

new_flow_handler = """    def on_genre_flow_activated(self, flowbox, child):
        idx = child.get_index()
        active_id = self.genre_keys[idx]
        
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
            print("Error changing genre:", e)"""

content = content.replace(combo_handler_code, new_flow_handler)

with open(APP_FILE, "w") as f:
    f.write(content)
