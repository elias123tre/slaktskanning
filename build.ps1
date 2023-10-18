pyinstaller main.py --onefile --windowed --add-data "icon.png;." --add-data "icon.ico;." --icon "icon.ico"
rm "dist/Skanning metadata.exe"
mv "dist/main.exe" "dist/Skanning metadata.exe"
