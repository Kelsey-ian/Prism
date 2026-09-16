@echo off
chcp 65001 >nul 2>&1
REM ================================================================
REM  Prism Build Script
REM  Usage:
REM    build.bat x64        - Build 64-bit portable
REM    build.bat x86        - Build 32-bit portable (needs 32-bit Python)
REM    build.bat x64 nsis   - Build 64-bit + NSIS installer
REM ================================================================

setlocal enabledelayedexpansion

set "ARCH=%~1"
set "MAKE_INSTALLER=%~2"
set "ROOT=%~dp0.."
set "SPEC=%ROOT%\prism.spec"
set "DIST=%ROOT%\dist"
set "BUILD=%ROOT%\build"

if "%ARCH%"=="" set "ARCH=x64"

echo ============================================
echo  Prism Build - %ARCH%
echo  Root: %ROOT%
echo  Spec: %SPEC%
echo ============================================

REM --- Check Python ---
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    exit /b 1
)

REM --- Show Python architecture ---
python -c "import struct; bits=struct.calcsize('P')*8; print(f'Python {bits}-bit')"

REM --- Install PyInstaller ---
echo.
echo [1/4] Checking PyInstaller...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

REM --- Inject build time ---
echo.
echo [2/4] Injecting build metadata...
python -c "from datetime import datetime; t=datetime.now().strftime('%%Y-%%m-%%d'); f=open(r'%ROOT%\app\__init__.py','r',encoding='utf-8'); c=f.read(); f.close(); import re; c=re.sub(r'APP_BUILD_TIME = \"[^\"]*\"', f'APP_BUILD_TIME = \"{t}\"', c); f=open(r'%ROOT%\app\__init__.py','w',encoding='utf-8'); f.write(c); f.close(); print(f'Build time: {t}')"

REM --- Clean old build ---
echo.
echo [3/4] Cleaning old build...
if exist "%BUILD%" rmdir /s /q "%BUILD%"
if exist "%DIST%\Prism" rmdir /s /q "%DIST%\Prism"

REM --- Run PyInstaller ---
echo.
echo [4/4] Running PyInstaller...
cd /d "%ROOT%"
python -m PyInstaller "%SPEC%" --noconfirm
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed
    exit /b 1
)

echo.
echo ============================================
echo  Build complete: %DIST%\Prism\
echo ============================================

REM --- Optional: NSIS installer ---
if /i "%MAKE_INSTALLER%"=="nsis" (
    echo.
    echo Building NSIS installer...

    REM Find makensis: check PATH first, then common install locations
    set "NSIS_EXE="
    makensis /VERSION >nul 2>&1
    if not errorlevel 1 (
        set "NSIS_EXE=makensis"
    )
    if not defined NSIS_EXE if exist "C:\Program Files\NSIS\makensis.exe" set "NSIS_EXE=C:\Program Files\NSIS\makensis.exe"
    if not defined NSIS_EXE if exist "C:\Program Files (x86)\NSIS\makensis.exe" set "NSIS_EXE=C:\Program Files (x86)\NSIS\makensis.exe"
    if not defined NSIS_EXE if exist "D:\APPs\NSIS\makensis.exe" set "NSIS_EXE=D:\APPs\NSIS\makensis.exe"

    if not defined NSIS_EXE (
        echo [WARN] makensis not found. Install NSIS: https://nsis.sourceforge.io
        exit /b 0
    )

    echo Using NSIS: !NSIS_EXE!
    cd /d "%ROOT%\scripts"
    "!NSIS_EXE!" prism_installer.nsi
    if errorlevel 1 (
        echo [ERROR] NSIS build failed
        exit /b 1
    )
    echo.
    echo Installer: %DIST%\Prism_Setup_%ARCH%.exe
)

endlocal
