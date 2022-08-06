"""A GUI for scan.py"""

import threading
from pathlib import Path
from datetime import datetime

import PySimpleGUI as sg
from PIL import Image

from scan import Scanner, downscale


def run_scan(window: sg.Window, scanner: Scanner, filename: str, dpi: int):
    """Perform a scan"""
    window.write_event_value("-RUNNING-", True)
    # self.start_btn.state(["disabled"])

    try:
        match scanner.is_ready():
            case None:
                print("Error: Scanner unavailable")
                return
            case False:
                print("Error: scanner is not ready")
                return

        # self.progress.pack(fill=tk.X, padx=5, pady=5, before=self.start_btn)
        # self.progress.start()

        # Full quality scan
        scanner.start_scan(dpi, compression=95)
        job = next(scanner.get_jobs(), None)

        if not job:
            print("Error: job not found after starting scan")
            return

        status = scanner.job_status(job["id"])
        if status != "Processing":
            print("Error: job could not start")
            return

        out_file = Path(filename)

        # Download the scanned page
        scanner.download_scan(job["id"], out_file)
        out_filename = downscale(out_file, size=1080, quality=75)
        Image.open(out_filename).show()
        print("Scan done:", out_filename)
    finally:
        window.write_event_value("-RUNNING-", False)
        # self.start_btn.state(["!disabled"])


def main():
    """Main function for scanner GUI"""
    scanner = Scanner()

    def start_scan(dpi):
        date = datetime.now().isoformat(" ", "seconds")
        filename = f"{date}.jpg"
        threading.Thread(
            target=run_scan, args=(window, scanner, filename, dpi), daemon=True
        ).start()

    layout = [
        [
            sg.Text("Upplösning:"),
            sg.OptionMenu(
                values=scanner.DPIS,
                default_value=600,
                key="-DPI-",
            ),
        ],
        [sg.Multiline(key="-OUT-", size=(60, 6), autoscroll=True, disabled=True)],
        [
            sg.Button("Starta skanning", key="-START SCAN-", bind_return_key=True),
            sg.Button("Stäng"),
        ],
    ]

    window = sg.Window("Skanna bilder", layout)
    sg.cprint_set_output_destination(window, "-OUT-")

    while True:  # Event Loop
        match window.read():  # type (event, values)
            case (sg.WIN_CLOSED | "Stäng", _):
                break
            case ("-START SCAN-", values):
                sg.cprint("Starting scan")
                start_scan(dpi=values["-DPI-"])
                sg.cprint("Scan started")
            case ("-RUNNING-", values):
                window["-START SCAN-"].update(disabled=values["-RUNNING-"])
            case ("-THREAD DONE-", _):
                sg.cprint("Scan done!")
            case (event, values):  # default
                print(event, values)

    window.close()


if __name__ == "__main__":
    main()
