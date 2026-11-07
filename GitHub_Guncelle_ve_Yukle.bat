@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title GitHub Guncelleme ve APK Derleme Araci
color 0B

echo ===================================================================
echo           EV BUTCESI - GITHUB GUNCELLEME VE YUKLEME ARACI
echo ===================================================================
echo.

cd /d "%~dp0"
echo Calisma dizini: %cd%
echo.

set REPO_URL=https://github.com/abdurrahmancosk/ev-butcesi.git

:: Git kontrolu
where git >nul 2>nul
if errorlevel 1 (
    echo [HATA] Git programi bulunamadi! Lutfen Git'in kurulu oldugundan emin olun.
    goto bitir
)

:: Guvenli dizin tanimlamasi (Google Drive ag/sanal surucu izin sorunu icin)
git config --global --add safe.directory "%cd%" 2>nul
git config --global --add safe.directory "*" 2>nul

:: Git kullanici bilgisi tanimla (hata vermemesi icin)
git config user.name >nul 2>nul
if errorlevel 1 (
    git config --global user.name "Abdurrahman Coskun"
    git config --global user.email "abdurrahmancosk@gmail.com"
)

if not exist ".git" (
    echo Depo olusturuluyor...
    git init
    git branch -M main
    git remote add origin %REPO_URL%
) else (
    git remote set-url origin %REPO_URL% 2>nul
    git branch -M main 2>nul
)

echo [1/3] Dosyalar hazirlaniyor...
git add -A

set TARIH=%date% %time%
echo [2/3] Degisiklikler paketleniyor (%TARIH%)...
git commit -m "Guncelleme: %TARIH%"

echo.
echo [3/3] GitHub ile esitleniyor ve gonderiliyor...
:: Eger GitHub'da onceden olusan commitler varsa once yerel ile birlestir
git pull origin main --rebase --allow-unrelated-histories 2>nul
if errorlevel 1 (
    git pull origin master --rebase --allow-unrelated-histories 2>nul
)

git push -u origin main
if errorlevel 1 (
    echo 'main' basarisiz oldu, zorlayarak guncelleniyor (force push)...
    git push -u origin main --force
)

if errorlevel 1 (
    echo.
    echo [UYARI] Gonderim tamamlanamadi!
    echo Tarayicinizda GitHub oturum acma ekrani geldiyse lutfen yetki verin.
) else (
    echo.
    echo ===================================================================
    echo [TEBRIKLER] Kodlar GitHub'a basariyla gonderildi!
    echo GitHub Actions otomatik olarak yeni APK derlemesini baslatti.
    echo ===================================================================
)

:bitir
echo.
echo Pencereyi kapatmak icin klavyeden herhangi bir tusa basin...
pause >nul
