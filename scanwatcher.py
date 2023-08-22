import tkinter as tk
from interface import PhotoInfoApp

# Initialize the Tkinter window
root = tk.Tk()
app = PhotoInfoApp(root)
app.withdraw_window()

app.create_observer()
print(f"Watching directory: {app.watched_directory}")

# Run the Tkinter main loop
root.mainloop()

