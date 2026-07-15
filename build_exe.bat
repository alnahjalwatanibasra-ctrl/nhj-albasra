@echo off
rem بناء نسخة التوزيع: dist\سجل_الصادر\سجل_الصادر.exe
python -m PyInstaller run_app.py --name "سجل_الصادر" --windowed --icon assets/logo.ico --add-data "assets;assets" --add-data "ui/theme.qss;ui" --noconfirm
pause
