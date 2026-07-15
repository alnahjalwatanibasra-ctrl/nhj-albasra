@echo off
rem بناء ملف التوزيع الوحيد: dist\سجل الصادر.exe (انسخه لسطح المكتب أو أي مكان)
python -m PyInstaller run_app.py --name "سجل الصادر" --onefile --windowed --icon assets/logo.ico --add-data "assets;assets" --add-data "ui/theme.qss;ui" --noconfirm
pause
