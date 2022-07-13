"""
A script for making automated scanning jobs for the HP Envy 4500 printer.

Reverse-engineered the webscan service att http://192.168.1.17/#hId-pgWebScan
"""

import shutil
import time
import tkinter as tk
import xml.etree.ElementTree as ET
from pathlib import Path
from tkinter import ttk
from typing import Iterator

import requests
from PIL import Image


def downscale(
    input_file: str | Path,
    size: int,
    quality: int,
    output_file: str | Path | None = None,
) -> Image:
    """
    Downsize the image to desired max size and jpeg quality.
    Output filename default: `[filename]_thumbnail.[extension]`
    """
    if isinstance(input_file, str):
        input_file = Path(input_file)
    if isinstance(output_file, str):
        output_file = Path(output_file)
    if not output_file:
        output_file = input_file.with_stem(f"{input_file.stem}_thumbnail")
    img = Image.open(input_file)
    img.thumbnail((size, size))
    img.save(output_file, quality=quality)
    return (output_file, img)


class Scanner:
    """
    Main scanner class

    Args:
        printer (str): Printer ip address url, ex. `http://192.168.1.17`.
    """

    SCHEMA = "{http://www.hp.com/schemas/imaging/con/ledm/jobs/2009/04/30}"

    printer: str
    cookies: dict[str, str]
    headers: dict[str, str]

    def __init__(
        self,
        printer: str = "http://192.168.1.17",
    ):
        self.printer = printer
        self.cookies = {
            "sid": "s0538708d-811ba985e173db93169e975baf2840b7",
            "mobileView": "0",
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64; rv:101.0) "
            "Gecko/20100101 Firefox/101.0",
            "Accept": "application/xml, text/xml, */*",
            "Accept-Language": "en,sv-SE;q=0.8,sv;q=0.5,en-US;q=0.3",
            "DNT": "1",
            "Connection": "keep-alive",
            "Referer": self.printer,
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

    def get_status(self) -> (str | None):
        """Get scanner status text"""
        response = requests.get(
            f"{self.printer}/Scan/Status", cookies=self.cookies, headers=self.headers
        )
        root = ET.fromstring(response.content)
        for child in root.iter():
            if child.tag.endswith("ScannerState"):
                return child.text
        print("Error: Could not get ScannerState")
        return None

    def is_ready(self) -> bool | None:
        """If scanner is ready to receive another can job"""
        status = self.get_status()
        if status is None:
            return None
        return status == "Idle"

    def block_until_ready(
        self, interval: float = 1, max_wait: float = 60
    ) -> bool | None:
        """
        Wait for the scanner to become idle.
        `interval` and `max_wait` are in seconds.
        Returns True if ready, False if timeout, None if error.
        """
        seconds = 0.0
        ready = None
        while not ready:
            ready = self.is_ready()
            if ready is None:
                return None
            time.sleep(interval)
            seconds += interval
            if seconds > max_wait:
                return True
        return False

    def get_jobs(self) -> Iterator[dict[str, str | int | None]]:
        """Get list of all scanning jobs ids on printer, latest last"""
        response = requests.get(
            f"{self.printer}/Jobs/JobList", cookies=self.cookies, headers=self.headers
        )
        if response.status_code == 204:
            return
        response.raise_for_status()
        root = ET.fromstring(response.content)
        for job in reversed(root):
            jobdict = {attr.tag.split("}", 1)[1]: attr.text for attr in job}
            if jobdict["JobUrl"] and jobdict["JobCategory"] == "Scan":
                yield {
                    **jobdict,
                    "id": int(jobdict["JobUrl"].split("/")[-1]),
                }

    def job_status(self, job_id: int):
        """Get status for job with id"""
        response = requests.get(
            f"{self.printer}/Jobs/JobList/{job_id}",
            cookies=self.cookies,
            headers=self.headers,
        )
        response.raise_for_status()
        root = ET.fromstring(response.content)
        jobdict = {attr.tag.split("}", 1)[1]: attr.text for attr in root}
        return jobdict.get("JobState")

    def start_scan(self, dpi: int, compression: int):
        """
        Start a scan
        dpi: higher is better, any of 75, 100, 200, 300, 600, 1200, 2400
        compression: lower is better - 0 = no compression, 95 = full compression
        """
        if not dpi in [75, 100, 200, 300, 600, 1200, 2400]:
            raise ValueError(
                "DPI must be one of the following values: "
                "75, 100, 200, 300, 600, 1200, 2400"
            )

        # width: 8-2550 (A4 2480)
        # height: 8-3508 (A4 3508)
        post_data = f"""
        <scan:ScanJob xmlns:scan="http://www.hp.com/schemas/imaging/con/cnx/scan/2008/08/19" xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/" xmlns:fw="http://www.hp.com/schemas/imaging/con/firewall/2011/01/05">
            <scan:XResolution>{dpi}</scan:XResolution>
            <scan:YResolution>{dpi}</scan:YResolution>
            <scan:XStart>0</scan:XStart>
            <scan:YStart>0</scan:YStart>
            <scan:Width>2550</scan:Width>
            <scan:Height>3508</scan:Height>
            <scan:Format>Jpeg</scan:Format>
            <scan:CompressionQFactor>{compression}</scan:CompressionQFactor>
            <scan:ColorSpace>Color</scan:ColorSpace>
            <scan:BitDepth>8</scan:BitDepth>
            <scan:InputSource>Platen</scan:InputSource>
            <scan:GrayRendering>NTSC</scan:GrayRendering>
            <scan:ToneMap>
                <scan:Gamma>1000</scan:Gamma>
                <scan:Brightness>1000</scan:Brightness>
                <scan:Contrast>1000</scan:Contrast>
                <scan:Highlite>179</scan:Highlite>
                <scan:Shadow>25</scan:Shadow>
            </scan:ToneMap>
            <scan:ContentType>Photo</scan:ContentType>
        </scan:ScanJob>
        """.strip()

        response = requests.post(
            f"{self.printer}/Scan/Jobs",
            cookies=self.cookies,
            headers={**self.headers, "Content-Type": "text/xml"},
            data=post_data,
        )
        response.raise_for_status()

    def download_scan(self, job_id: int, output_file: str | Path, page: int = 1):
        """Download the scanned file to disk"""

        with requests.get(
            f"{self.printer}/Scan/Jobs/{job_id}/Pages/{page}",
            cookies=self.cookies,
            headers={
                **self.headers,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8",
            },
            stream=True,
        ) as req:
            with open(output_file, "wb") as file:
                shutil.copyfileobj(req.raw, file)


class ScannerWindow(tk.Tk):
    """Window to execute scanning actions"""

    DPIS = (75, 100, 200, 300, 600, 1200, 2400)

    def __init__(self, scanner: Scanner):
        super().__init__()
        self.title("Skanna bilder")
        self._scanner = scanner
        self.dpi = tk.StringVar(self)
        self._create_inputs()
        self._create_buttons()

    def _create_inputs(self):
        filename_frame = ttk.Frame(master=self)
        filename_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        label = ttk.Label(
            master=filename_frame, width=50, text="Filnamn för skanningen:", anchor="w"
        )
        label.pack(side=tk.LEFT)
        self.filename = ttk.Entry(master=filename_frame)
        self.filename.insert(0, "scan.jpg")
        self.filename.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

        dpi_frame = ttk.Frame(master=self)
        dpi_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        label = ttk.Label(
            master=dpi_frame, width=50, text="DPI (tal mellan 75 och 600):", anchor="w"
        )
        label.pack(side=tk.LEFT)
        self.dpi_menu = ttk.OptionMenu(
            dpi_frame,
            self.dpi,
            "600",
            *(str(dpi) for dpi in self.DPIS),
            # command=lambda: print("changed")
        )
        self.dpi_menu.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

        quality_frame = ttk.Frame(master=self)
        quality_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        label = ttk.Label(
            master=quality_frame,
            width=50,
            text="JPEG kvalite (0 för sämsta kvalite, 95 för bästa kvalite):",
            anchor="w",
        )
        label.pack(side=tk.LEFT)
        self.quality = ttk.Entry(master=quality_frame)
        self.quality.insert(0, "65")
        self.quality.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

    def _create_buttons(self):
        self.bind("<Return>", lambda _: self.initiate_scan())

        self.start_btn = ttk.Button(
            master=self, text="Starta skanning", command=self.initiate_scan
        )
        self.start_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.progress = ttk.Progressbar(
            master=self, orient="horizontal", mode="indeterminate", length=280
        )
        self.progress.pack(fill=tk.X, padx=5, pady=5, before=self.start_btn)
        self.progress.pack_forget()

        quit_btn = ttk.Button(master=self, text="Avsluta", command=self.quit)
        quit_btn.pack(side=tk.LEFT, padx=5, pady=5)

    def initiate_scan(self):
        """Perform a scan"""
        self.start_btn.state(["disabled"])

        try:
            match self._scanner.is_ready():
                case None:
                    print("Error: Scanner unavailable")
                    return
                case False:
                    print("Error: scanner is not ready")
                    return

            self.progress.pack(fill=tk.X, padx=5, pady=5, before=self.start_btn)
            self.progress.start()

            # Full quality scan
            self._scanner.start_scan(int(self.dpi.get()), compression=95)
            job = next(self._scanner.get_jobs(), None)

            if not job:
                print("Error: job not found after starting scan")
                return

            status = self._scanner.job_status(job["id"])
            if status != "Processing":
                print("Error: job could not start")
                return

            out_file = Path(self.filename.get())

            # Download the scanned page
            self._scanner.download_scan(job["id"], out_file)
            (filename, image) = downscale(out_file, size=1080, quality=int(self.quality.get()))
            image.show()
            print("Scan done:", filename)
        finally:
            self.progress.stop()
            self.progress.pack_forget()
            self.start_btn.state(["!disabled"])


if __name__ == "__main__":
    scannr = Scanner()
    window = ScannerWindow(scannr)
    window.mainloop()
