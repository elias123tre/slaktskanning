import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog

import pystray
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class NewFileHandler(FileSystemEventHandler):
    def __init__(self, gui):
        self.gui = gui

    def on_created(self, event):
        self.gui.show_notification(event)


class PhotoInfoApp:
    watched_directory: Path = Path("~/Pictures/Skanningar").expanduser()
    image_path: Path | None = None
    observer: Observer | None = None

    def __init__(self, root):
        self.root = root
        self.root.title("Släktskanning")
        self.root.protocol("WM_DELETE_WINDOW", self.withdraw_window)

        self.observer = None
        self.handler = NewFileHandler(self)

        self.image = Image.open(resource_path("icon.png"))
        self.menu = (
            pystray.MenuItem("Välj inskanningsmapp", self.change_scan_folder),
            pystray.MenuItem("Avsluta", self.quit_window),
        )
        self.icon = pystray.Icon(
            "name", self.image, f"Släktskanning\n{self.watched_directory}", self.menu
        )
        self.icon.run_detached()

        if not self.watched_directory.exists():
            self.change_scan_folder()

        # Photo location
        self.location_label = ttk.Label(root, text="Plats där fotot togs:")
        self.location_label.pack()
        self.location_entry = ttk.Entry(root)
        self.location_entry.pack()

        # Date and time taken
        self.date_label = ttk.Label(root, text="Datum (och tid) när fotot togs:")
        self.date_label.pack()
        self.date_entry = ttk.Entry(root)
        self.date_entry.pack()

        # People in the photo
        self.people_label = ttk.Label(
            root, text="Personer i bilden (en per rad, vänster till höger):"
        )
        self.people_label.pack()
        self.people_text = tk.Text(root, height=5, width=30)
        self.people_text.pack()

        # Submit and Show/Hide buttons
        self.submit_button = ttk.Button(root, text="Submit", command=self.save_info)
        self.submit_button.pack()

        self.info_window = None

    def save_info(self):
        location = self.location_entry.get()
        date_taken = self.date_entry.get()
        people = self.people_text.get("1.0", "end-1c")  # Get all lines of text
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

    def quit_window(self):
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
            # messagebox.showinfo("New File Added", f"New file '{event.src_path}' added!")
            image = Path(event.src_path)
            # if image is of file type image
            if image.suffix in [".jpg", ".jpeg", ".png", ".gif"]:
                # Show the window
                self.show_window(image)
