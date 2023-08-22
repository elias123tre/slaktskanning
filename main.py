import tkinter as tk
from interface import PhotoInfoApp


def main():
    root = tk.Tk()
    app = PhotoInfoApp(root)
    app.withdraw_window()

    app.create_observer()

    root.mainloop()


if __name__ == "__main__":
    main()
