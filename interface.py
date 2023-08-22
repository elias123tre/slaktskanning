from pathlib import Path
import tkinter as tk
from tkinter import ttk

import pystray
from PIL import Image


class PhotoInfoApp:
    image_path: Path | None = None

    def __init__(self, root):
        self.root = root
        self.root.title("Släktskanning")
        self.root.protocol("WM_DELETE_WINDOW", self.withdraw_window)

        self.image = Image.open("icon.png")
        self.menu = (
            # pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Quit", self.quit_window),
        )
        self.icon = pystray.Icon("name", self.image, "Släktskanning", self.menu)
        self.icon.run_detached()

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
        self.people_label = ttk.Label(root, text="Personer i bilden (en per rad, vänster till höger):")
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
