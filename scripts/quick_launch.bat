@echo off
chcp 65001 >nul
echo ========================================
echo VocabGo RPA Quick Launch
echo ========================================
echo.

REM Set paths
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

:menu
cls
echo.
echo Please select launch mode:
echo.
echo [1] Full startup (all tools)
echo [2] Translumo only
echo [3] CapsWriter only
echo [4] Auto Translator (Listening questions)
echo [5] Test Qwen API
echo [6] Generate optimized prompt
echo [7] Install Python dependencies
echo [8] Exit
echo.
set /p choice=Please enter choice (1-8):

if "%choice%"=="1" goto full_start
if "%choice%"=="2" goto translumo_only
if "%choice%"=="3" goto capswriter_only
if "%choice%"=="4" goto auto_translator
if "%choice%"=="5" goto test_api
if "%choice%"=="6" goto prompt_generator
if "%choice%"=="7" goto install_deps
if "%choice%"=="8" goto exit

echo.
echo Invalid choice, please try again
pause
goto menu

:full_start
echo.
echo [Starting] Full system...
call "%SCRIPT_DIR%startup.bat"
goto end

:translumo_only
echo.
echo [Starting] Translumo only...
set TRANSLUMO_PATH=%PROJECT_DIR%\tools\Translumo\Translumo.exe
if exist "%TRANSLUMO_PATH%" (
    start "" "%TRANSLUMO_PATH%"
    echo [Success] Translumo is started
) else (
    echo [Error] Translumo not installed
)
pause
goto menu

:capswriter_only
echo.
echo [Starting] CapsWriter only...
set CAPSWRITER_SERVER=%PROJECT_DIR%\tools\CapsWriter-Offline\start_server.exe
set CAPSWRITER_CLIENT=%PROJECT_DIR%\tools\CapsWriter-Offline\start_client.exe
if exist "%CAPSWRITER_SERVER%" (
    start /min "" "%CAPSWRITER_SERVER%"
    timeout /t 3 /nobreak >nul
    start /min "" "%CAPSWRITER_CLIENT%"
    echo [Success] CapsWriter is started
) else (
    echo [Error] CapsWriter not installed
)
pause
goto menu

:auto_translator
echo.
echo [Starting] Auto Translator...
echo.
echo Auto Translator options:
echo [1] Start normal listening
echo [2] List available microphones
echo [3] Test microphone
echo [4] Check API configuration
echo.
set /p translator_choice=Please enter choice (1-4):

if "%translator_choice%"=="1" goto auto_start
if "%translator_choice%"=="2" goto auto_list
if "%translator_choice%"=="3" goto auto_test
if "%translator_choice%"=="4" goto auto_check

goto menu

:auto_start
cd "%SCRIPT_DIR%"
python auto_translator.py
pause
goto menu

:auto_list
cd "%SCRIPT_DIR%"
python auto_translator.py --list
pause
goto menu

:auto_test
cd "%SCRIPT_DIR%"
python auto_translator.py --test
pause
goto menu

:auto_check
cd "%SCRIPT_DIR%"
python auto_translator.py --check-api
pause
goto menu

:install_deps
echo.
echo [Installing] Python dependencies...
cd "%PROJECT_DIR%"
pip install -r requirements.txt
if %errorlevel% equ 0 (
    echo [Success] Dependencies installed successfully
) else (
    echo [Warning] Some dependencies may have failed to install
    echo.
    echo Note: pyaudio may require special installation on Windows
    echo Try: pipwin install pyaudio
)
pause
goto menu

:test_api
echo.
echo [Testing] Qwen API connection...
cd "%SCRIPT_DIR%"
python qwen_helper.py test
pause
goto menu

:prompt_generator
echo.
echo [Starting] Prompt optimizer...
echo.
echo Prompt type:
echo [1] Translation question prompt
echo [2] Listening question prompt
echo [3] Advanced analysis prompt
echo [4] Custom prompt
echo.
set /p prompt_type=Please enter choice (1-4):

if "%prompt_type%"=="1" goto translation_prompt
if "%prompt_type%"=="2" goto listening_prompt
if "%prompt_type%"=="3" goto analysis_prompt
if "%prompt_type%"=="4" goto custom_prompt

echo.
echo Invalid choice
pause
goto menu

:translation_prompt
echo.
set /p sentence=Please enter English sentence:
set /p options=Please enter options (optional, format: A. option1 B. option2):

if "%options%"=="" (
    python prompt_optimizer.py translate "%sentence%"
) else (
    python prompt_optimizer.py translate "%sentence%" %options%
)
pause
goto menu

:listening_prompt
echo.
set /p word=Please enter English word:
set /p options=Please enter options (optional, format: A. option1 B. option2):

if "%options%"=="" (
    python prompt_optimizer.py listening "%word%"
) else (
    python prompt_optimizer.py listening "%word%" %options%
)
pause
goto menu

:analysis_prompt
echo.
set /p sentence=Please enter English sentence:
set /p word=Please enter highlighted word:
set /p options=Please enter options (format: A. option1 B. option2):

if "%options%"=="" (
    python prompt_optimizer.py analyze "%sentence%" "%word%"
) else (
    python prompt_optimizer.py analyze "%sentence%" "%word%" %options%
)
pause
goto menu

:custom_prompt
echo.
set /p content=Please enter custom prompt content:
set /p filename=Please enter filename (optional):
if "%filename%"=="" (
    python prompt_optimizer.py save custom "%content%"
) else (
    python prompt_optimizer.py save custom "%content%" "%filename%"
)
pause
goto menu

:exit
echo.
echo Thank you for using VocabGo RPA system!
echo.
goto end

:end