@echo off
rem بناء ملف التوزيع الوحيد: dist\سجلات النهج.exe (المفتاح مضمّن من assets\keys)
python -m PyInstaller run_app.py --name "سجلات النهج" --onefile --windowed --icon assets/logo.ico --add-data "assets;assets" --add-data "ui/theme.qss;ui" --noconfirm
pause
