@echo off
chcp 65001 >nul
echo.
echo ══════════════════════════════════════════
echo   Build — نظام إدارة المدفوعات
echo ══════════════════════════════════════════
echo.

:: ── 1. تحقق من Python ──────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python مش موجود في PATH
    pause & exit /b 1
)

:: ── 2. ثبّت PyInstaller لو مش موجود ───────────────────────────
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
)

:: ── 3. نظّف builds قديمة ────────────────────────────────────────
if exist "build"  rmdir /s /q "build"
if exist "dist"   rmdir /s /q "dist"
echo [OK] Cleaned old builds

:: ── 4. شغّل PyInstaller ────────────────────────────────────────
echo [INFO] Building EXE...
pyinstaller pos_system.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed — اقرأ الـ errors فوق
    pause & exit /b 1
)

:: ── 5. نتيجة ────────────────────────────────────────────────────
echo.
echo ══════════════════════════════════════════
echo   [SUCCESS] EXE جاهز في:
echo   dist\نظام_المدفوعات.exe
echo ══════════════════════════════════════════
echo.
explorer dist
pause
