# Släktskanning

> This is a program that watches a folder for new scanned images and shows a prompt with fields for metadata to that picture and saves it as a metadata file besides the image.

**Note:** This program is in Swedish.

## Instructions

[![Download button](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=Download&query=%24.tag_name&url=https%3A%2F%2Fapi.github.com%2Frepos%2Felias123tre%2Fslaktskanning%2Freleases%2Flatest&style=for-the-badge)](https://github.com/elias123tre/slaktskanning/releases/latest/download/Skanning-metadata.exe)

1. Download the latest release from the badge above.
2. Run the program.
3. Select the folder you want to watch (only first run).
4. Check the system tray for the icon to see that it is running (see options on right click).
5. Scan your images to the selected folder.
6. Window to fill in metadata will pop up.
7. Fill in the metadata and press Submit.
8. The metadata will be saved as `<image_filename>_metadata.yaml` in the same folder as the image.

## Build instructions (advanced)

A build script for Windows using PyInstaller is in `build.ps1`, just run it with PowerShell and the executable will be in `dist\Skanning-metadata.exe`.

The main file is `window.py` and can also be run manually with `python window.py` after installing the dependencies in `requirements.txt`.
