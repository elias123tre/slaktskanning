import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog
import pystray
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class NewFileHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    def on_created(self, event):
        self.app.show_notification(event)


class PhotoInfoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Släktskanning")
        self.root.protocol("WM_DELETE_WINDOW", self.withdraw_window)

        self.image_path = None
        self.observer = None
        self.handler = NewFileHandler(self)
        self.watched_directory = Path("~/Pictures/Skanningar").expanduser()

        self.setup_tray_icon()
        self.setup_ui()

        if not self.watched_directory.exists():
            self.change_scan_folder()

    def setup_tray_icon(self):
        self.image = Image.open(resource_path("icon.png"))
        self.menu = (
            pystray.MenuItem("Välj inskanningsmapp", self.change_scan_folder),
            pystray.MenuItem("Avsluta", self.quit_app),
        )
        self.icon = pystray.Icon(
            "name", self.image, f"Släktskanning\n{self.watched_directory}", self.menu
        )
        self.icon.run_detached()

    def setup_ui(self):
        self.location_label = ttk.Label(self.root, text="Plats där fotot togs:")
        self.location_label.pack()
        self.location_entry = ttk.Entry(self.root)
        self.location_entry.pack()

        self.date_label = ttk.Label(self.root, text="Datum (och tid) när fotot togs:")
        self.date_label.pack()
        self.date_entry = ttk.Entry(self.root)
        self.date_entry.pack()

        self.people_label = ttk.Label(
            self.root, text="Personer i bilden (en per rad, vänster till höger):"
        )
        self.people_label.pack()
        self.people_text = tk.Text(self.root, height=5, width=30)
        self.people_text.pack()

        self.submit_button = ttk.Button(
            self.root, text="Submit", command=self.save_info
        )
        self.submit_button.pack()

    def save_info(self):
        location = self.location_entry.get()
        date_taken = self.date_entry.get()
        people = self.people_text.get("1.0", "end-1c")
        people_lines = "\n".join(f"- {line}" for line in people.splitlines())

        info = f"""
Plats: {location}
Datum fotat: {date_taken}
Personer i bilden (vänster till höger):
{people_lines}
""".strip()

        if self.image_path:
            image = Path(self.image_path)
            meta = image.with_stem(image.stem + "_info").with_suffix(".txt")
            meta.write_text(info, encoding="utf-8")

        self.withdraw_window()
        self.clear_fields()

    def clear_fields(self):
        self.location_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.people_text.delete("1.0", "end")

    def quit_app(self):
        self.root.after(0, self.icon.stop)
        self.root.after(0, self.root.destroy)

    def show_window(self, image_path):
        self.image_path = image_path
        self.root.protocol("WM_DELETE_WINDOW", self.withdraw_window)
        self.root.after(0, self.root.deiconify)

    def withdraw_window(self):
        self.image_path = None
        self.root.withdraw()

    def change_scan_folder(self):
        startdir = (
            self.watched_directory if self.watched_directory.exists() else os.getcwd()
        )
        folder = filedialog.askdirectory(
            initialdir=startdir, title="Välj inskanningsmapp"
        )
        if folder:
            self.watched_directory = Path(folder).expanduser()
            print(f"Watching directory: {self.watched_directory}")
            self.create_observer()
            self.icon.title = f"Släktskanning\n{self.watched_directory}"

    def create_observer(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

        self.observer = Observer()
        self.observer.schedule(
            self.handler, path=self.watched_directory, recursive=False
        )
        self.observer.start()

    def show_notification(self, event):
        if event.event_type == "created":
            image = Path(event.src_path)
            if image.suffix in [".jpg", ".jpeg", ".png", ".gif"]:
                self.show_window(image)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
