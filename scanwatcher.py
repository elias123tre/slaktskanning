import tkinter as tk
from interface import PhotoInfoApp


def main():
    root = tk.Tk()
    app = PhotoInfoApp(root)
    app.withdraw_window()

    app.create_observer()
    print(f"Watching directory: {app.watched_directory}")

    # Run the Tkinter main loop
    root.mainloop()


if __name__ == "__main__":
    main()
