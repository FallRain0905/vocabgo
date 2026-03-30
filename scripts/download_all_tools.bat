@echo off
chcp 65001 >nul
echo ========================================
echo VocabGo RPA Tools One-Click Download
echo ========================================
echo.

REM Set script directory
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
cd %PROJECT_DIR%

echo.
echo [1/2] Downloading Translumo OCR tool...
echo.
powershell -ExecutionPolicy Bypass -File download_translumo.ps1
if errorlevel 1 (
    echo.
    echo [Error] Translumo download failed
    echo     Please check network connection or download manually
    pause
    exit /b 1
)
echo.
echo [Success] Translumo download completed!
echo.

echo.
echo [2/2] Downloading CapsWriter-Offline tool...
echo.
powershell -ExecutionPolicy Bypass -File download_capswriter.ps1
if errorlevel 1 (
    echo.
    echo [Error] CapsWriter-Offline download failed
    echo     Please check network connection or download manually
    pause
    exit /b 1
)
echo.
echo [Success] CapsWriter-Offline download completed!
echo.

echo.
echo ========================================
echo All tools download completed!
echo ========================================
echo.
echo Next steps:
echo 1. Translumo: tools\Translumo\Translumo.exe
echo 2. CapsWriter: tools\CapsWriter-Offline\start_server.exe
echo.
echo Note: CapsWriter requires additional model files
echo       Please visit: https://github.com/HaujetZhao/CapsWriter-Offline/releases
echo       Download models.zip and extract to models\ folder
echo.
pause