@echo off
title GitHub Guncelleme ve APK Derleme Araci
color 0B

echo ===================================================================
echo           EV BUTCESI - GITHUB GUNCELLEME VE YUKLEME ARACI
echo ===================================================================
echo.

cd /d "%~dp0"
echo Calisma dizini: %cd%
echo.

:: Git guvenli dizin ve kimlik ayarlari
git config --global user.name "Abdurrahman Coskun"
git config --global user.email "abdurrahmancosk@gmail.com"
git config --global --add safe.directory "%cd%"
git config --global --add safe.directory "*"

:: Guvenlik icin gitignore olustur
(
echo gemini_key.json
echo *.csv
echo *.db
echo *.sqlite3
echo __pycache__/
) > .gitignore

echo [1/3] Dosyalar zorunlu ekleniyor...
git add -f main.py
if exist "requirements.txt" git add -f requirements.txt
if exist "build-apk.yml" git add -f build-apk.yml
if exist ".github" git add -f .github
git add -f .gitignore
git add -f GitHub_Guncelle_ve_Yukle.bat
git add -f EvButcesi_Baslat.bat
git add -f EvButcesi.vbs

echo.
echo [2/3] Paket olusturuluyor...
set TARIH=%date% %time%
git commit -m "Guncelleme: %TARIH%" --allow-empty

echo.
echo [3/3] GitHub'a gonderiliyor (Push)...
git push -u origin main --force

echo.
echo ===================================================================
echo                     ISLEM TAMAMLANDI!
echo ===================================================================
echo.
echo Cikmak icin bir tusa basin...
cmd /k
