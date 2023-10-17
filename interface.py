from collections import OrderedDict
from datetime import datetime
import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog
import pystray
from PIL import Image, ImageTk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from metadata import METADATA_SCHEMA


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

        self.root.geometry("500x500")

        self.image_path = None
        self.observer = None
        self.handler = NewFileHandler(self)
        self.watched_directory = Path("~/Pictures/Skanningar").expanduser()

        self.root.iconbitmap("icon.ico")

        self.setup_tray_icon()
        self.setup_ui()

        if not self.watched_directory.exists():
            self.change_scan_folder()

        # TEMPORARY
        # self.show_window("~/Pictures/Screenshots/Screenshot 2023-04-08 152009.png")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def setup_tray_icon(self):
        self.image = Image.open(resource_path("icon.png"))
        self.menu = (
            pystray.MenuItem(
                "Öppna fil för att lägga till metadata", self.add_metadata
            ),
            pystray.MenuItem("Välj inskanningsmapp", self.change_scan_folder),
            pystray.MenuItem("Avsluta", self.quit_app),
        )
        self.icon = pystray.Icon(
            "name", self.image, f"Släktskanning\n{self.watched_directory}", self.menu
        )
        self.icon.run_detached()

    def setup_ui(self):
        # Lämna tomt om informationen inte finns

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=1)

        self.canvas = tk.Canvas(self.main_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # Create a Label to display the image
        if self.image_path:
            image = Image.open(self.image_path)
            image.thumbnail((100, 100))  # Resize the image as needed
            self.photo = ImageTk.PhotoImage(image)  # Store the PhotoImage
            self.image_label = ttk.Label(self.main_frame, image=self.photo)
            # Prevent the image from being garbage collected
            self.image_label.image = self.photo
            self.image_label.pack(side=tk.LEFT, padx=10)

        self.scrollbar = tk.Scrollbar(
            self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.field_frame = tk.Frame(self.canvas)

        self.componets = OrderedDict()
        for key, value in METADATA_SCHEMA.items():
            label = ttk.Label(self.field_frame, text=value["label"])
            label.pack(fill=tk.X)

            if value.get("multiline"):
                text = tk.Text(self.field_frame, height=5, width=40)
                text.pack(fill=tk.X)
                self.componets[key] = text
            else:
                entry = ttk.Entry(self.field_frame)
                entry.pack(fill=tk.X)
                self.componets[key] = entry

            examples = value.get("examples")
            if examples:
                example_label = ttk.Label(
                    self.field_frame, text="Exempel:\n" + "\n".join(examples)
                )
                example_label.pack(fill=tk.X)

            # separator
            separator = ttk.Separator(self.field_frame, orient="horizontal")
            separator.pack(fill="x", pady=10)

        self.submit_button = ttk.Button(
            self.field_frame, text="Submit", command=self.save_info
        )
        self.submit_button.pack()

        self.canvas.create_window((0, 0), window=self.field_frame, anchor="nw")

    def save_info(self):
        if self.image_path:
            image = Path(self.image_path)
            now = datetime.now()

            info = [
                f'Datum inskannat:\n{now.strftime("%Y-%m-%d %H:%M:%S")}',
                f"Inskannade bildens filstorlek (byte):\n{image.stat().st_size}",
            ]

            for key, value in self.componets.items():
                identifier = METADATA_SCHEMA[key]["identifier"]
                if isinstance(value, tk.Text):
                    text_content = value.get("1.0", "end-1c")
                else:
                    text_content = value.get()
                if text_content:
                    info.append(f"{identifier}\n{text_content}")

            metadata_text = "\n\n".join(info)
            meta = image.with_stem(image.stem + "_metadata").with_suffix(".txt")
            # if file exists rename the old one with its creation date
            if meta.exists():
                meta.rename(meta.with_stem(meta.stem + meta.stat().st_ctime))
            meta.write_text(metadata_text, encoding="utf-8")

        self.withdraw_window()
        self.clear_fields()

    def clear_fields(self):
        for _, value in self.componets.items():
            if isinstance(value, tk.Text):
                value.delete("1.0", "end")
            else:
                value.delete(0, tk.END)

    def quit_app(self):
        self.root.after(0, self.icon.stop)
        self.root.after(0, self.root.destroy)

    def show_window(self, image_path):
        self.image_path = image_path
        self.root.title(f"Släktskanning - {Path(self.image_path).name}")

        if self.image_path:
            image = Image.open(self.image_path)
            image.thumbnail((100, 100))  # Resize the new image as needed
            new_photo = ImageTk.PhotoImage(image)  # Create a new PhotoImage
            if not hasattr(self, "image_label"):
                self.image_label = ttk.Label(self.main_frame, image=new_photo)
            # Update the label with the new image
            self.image_label.configure(image=new_photo)
            # Prevent the new image from being garbage collected
            self.image_label.image = new_photo
        
            print("new image")

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

    def add_metadata(self):
        file = filedialog.askopenfilename(
            initialdir=self.watched_directory,
            title="Välj fil att lägga till metadata till",
        )
        if file:
            self.show_window(file)

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
