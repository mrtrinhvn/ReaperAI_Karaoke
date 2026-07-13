import os

APP_FILE = "karaoke_app.py"
with open(APP_FILE, "r") as f:
    content = f.read()

# Force global dark theme
old_init = """    def __init__(self):
        super().__init__(title="Karaoke AI Studio")"""

new_init = """    def __init__(self):
        super().__init__(title="Karaoke AI Studio")
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)"""

content = content.replace(old_init, new_init)

with open(APP_FILE, "w") as f:
    f.write(content)
