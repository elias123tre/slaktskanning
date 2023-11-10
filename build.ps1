pyinstaller window.py --onefile --windowed --add-data "icon.png;." --add-data "icon.ico;." --icon "icon.ico"
if (Test-Path "dist/Skanning-metadata.exe") {
    Remove-Item "dist/Skanning-metadata.exe"
}
Move-Item "dist/window.exe" "dist/Skanning-metadata.exe"
