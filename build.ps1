pyinstaller main.py --onefile --windowed --add-data "icon.png;." --icon "icon.ico"
mv "dist/main.exe" "dist/Skanning metadata.exe"
