@echo off
chcp 65001 >nul
title Ev Butcesi
echo ===================================================
echo           Ev Butcesi Uygulamasi Baslatiliyor...
echo ===================================================
cd /d "%~dp0"

where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw main.py
    exit /b
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python main.py
    exit /b
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    py main.py
    exit /b
)

echo.
echo [HATA] Bilgisayarinizda Python bulunamadi!
echo Lutfen Python'un kurulu oldugundan emin olun.
pause
