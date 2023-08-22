from pathlib import Path
import tkinter as tk
from interface import PhotoInfoApp
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Directory to monitor
watched_directory = Path("~/Pictures/Skanningar").expanduser()

# Initialize the Tkinter window
root = tk.Tk()
app = PhotoInfoApp(root)
app.withdraw_window()

# Function to display a message box when a new file is added
def show_notification(event):
    if event.event_type == 'created':
        # messagebox.showinfo("New File Added", f"New file '{event.src_path}' added!")
        image = Path(event.src_path)
        # if image is of file type image
        if image.suffix in ['.jpg', '.jpeg', '.png', '.gif']:
            # Show the window
            app.show_window(image)

# Create a file system event handler
event_handler = None

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        show_notification(event)

try:
    event_handler = NewFileHandler()

    # Set up the watchdog observer to monitor the directory
    observer = Observer()
    observer.schedule(event_handler, path=watched_directory, recursive=False)
    observer.start()

    print(f"Watching directory: {watched_directory}")

    # Run the Tkinter main loop
    root.mainloop()

finally:
    if event_handler:
        observer.stop()
        observer.join()
