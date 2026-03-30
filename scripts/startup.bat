@echo off
chcp 65001 >nul
echo ========================================
echo VocabGo RPA System Startup
echo ========================================
echo.

REM Set script directory
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

REM Check if tools are installed
echo [1/4] Checking tool installation status...

set TRANSLUMO_PATH=%PROJECT_DIR%\tools\Translumo\Translumo.exe
set CAPSWRITER_SERVER=%PROJECT_DIR%\tools\CapsWriter-Offline\start_server.exe
set CAPSWRITER_CLIENT=%PROJECT_DIR%\tools\CapsWriter-Offline\start_client.exe

if not exist "%TRANSLUMO_PATH%" (
    echo [Warning] Translumo not installed
    echo     Please run: scripts\download_translumo.ps1
    echo.
) else (
    echo [Success] Translumo is installed
)

if not exist "%CAPSWRITER_SERVER%" (
    echo [Warning] CapsWriter-Offline not installed
    echo     Please run: scripts\download_capswriter.ps1
    echo.
) else (
    echo [Success] CapsWriter-Offline is installed
)

echo.
echo [2/4] Checking configuration files...

set QWEN_CONFIG=%PROJECT_DIR%\config\qwen-config.json
if not exist "%QWEN_CONFIG%" (
    echo [Warning] Qwen config file not found
    echo     Please edit: config\qwen-config.json
    echo.
) else (
    echo [Success] Configuration file is ready
)

echo.
echo [3/4] Starting tools...
echo.

REM Start Translumo
if exist "%TRANSLUMO_PATH%" (
    echo [Starting] Translumo OCR tool...
    start "" "%TRANSLUMO_PATH%"
    timeout /t 2 /nobreak >nul
)

REM Start CapsWriter server
if exist "%CAPSWRITER_SERVER%" (
    echo [Starting] CapsWriter server...
    start /min "" "%CAPSWRITER_SERVER%"
    timeout /t 3 /nobreak >nul
)

REM Start CapsWriter client
if exist "%CAPSWRITER_CLIENT%" (
    echo [Starting] CapsWriter client...
    start /min "" "%CAPSWRITER_CLIENT%"
    timeout /t 2 /nobreak >nul
)

echo.
echo [4/4] System is ready!
echo.
echo ========================================
echo Usage Instructions:
echo ========================================
echo.
echo 1. PC WeChat - Open vocabulary assignment page
echo.
echo 2. Translumo - Use hotkeys:
echo    Alt + G : Open settings
echo    Alt + Q : Select screen area
echo    ~      : Start/stop translation
echo.
echo 3. CapsWriter - Press CapsLock to record
echo.
echo 4. Qwen API - Configure API in Translumo
echo.
echo ========================================
echo.
echo Tip: Tools are minimized to system tray
echo      You can manage them in the tray
echo.
echo Press any key to close this window...
pause >nul