@echo off
rem بناء ملف التوزيع الوحيد: dist\Nhj AL-Basra.exe (المفتاح مضمّن من assets\keys)
python -m PyInstaller run_app.py --name "Nhj AL-Basra" --onefile --windowed --icon assets/logo.ico --splash assets/splash.png --add-data "assets;assets" --add-data "ui/theme.qss;ui" --noconfirm
pause
