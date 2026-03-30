# Simple Direct Download Script
# Downloads Translumo and CapsWriter-Offline directly

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VocabGo RPA - Tool Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set paths
$toolsDir = Join-Path $PSScriptRoot "..\tools"
if (-not (Test-Path $toolsDir)) {
    New-Item -ItemType Directory -Path $toolsDir -Force
}

try {
    # Download Translumo
    Write-Host "[1/2] Downloading Translumo v1.0.2..." -ForegroundColor Yellow
    $translumoUrl = "https://github.com/ramjke/Translumo/releases/download/v1.0.2/Translumo_1.0.2.zip"
    $translumoZip = Join-Path $toolsDir "translumo_v1.0.2.zip"

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $translumoUrl -OutFile $translumoZip -UseBasicParsing -TimeoutSec 30
        Write-Host "[OK] Translumo downloaded successfully!" -ForegroundColor Green

        # Extract Translumo
        Write-Host "[1/2] Extracting Translumo..." -ForegroundColor Cyan
        $translumoDir = Join-Path $toolsDir "Translumo"
        if (-not (Test-Path $translumoDir)) {
            New-Item -ItemType Directory -Path $translumoDir -Force
        }
        Expand-Archive -Path $translumoZip -DestinationPath $translumoDir -Force
        Remove-Item $translumoZip -Force
        Write-Host "[OK] Translumo extracted successfully!" -ForegroundColor Green

    } catch {
        Write-Host "[ERROR] Translumo failed: $_" -ForegroundColor Red
    }

    # Download CapsWriter-Offline
    Write-Host "[2/2] Downloading CapsWriter-Offline v2.5-alpha..." -ForegroundColor Yellow
    $capswriterUrl = "https://github.com/HaujetZhao/CapsWriter-Offline/releases/download/v2.5-alpha/CapsWriter-Offline-Windows-64bit.zip"
    $capswriterZip = Join-Path $toolsDir "capswriter_v2.5-alpha.zip"

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $capswriterUrl -OutFile $capswriterZip -UseBasicParsing -TimeoutSec 30
        Write-Host "[OK] CapsWriter-Offline downloaded successfully!" -ForegroundColor Green

        # Extract CapsWriter-Offline
        Write-Host "[2/2] Extracting CapsWriter-Offline..." -ForegroundColor Cyan
        $capswriterDir = Join-Path $toolsDir "CapsWriter-Offline"
        if (-not (Test-Path $capswriterDir)) {
            New-Item -ItemType Directory -Path $capswriterDir -Force
        }
        Expand-Archive -Path $capswriterZip -DestinationPath $capswriterDir -Force
        Remove-Item $capswriterZip -Force
        Write-Host "[OK] CapsWriter-Offline extracted successfully!" -ForegroundColor Green

    } catch {
        Write-Host "[ERROR] CapsWriter-Offline failed: $_" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Deployment Summary" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $translumoExists = Test-Path (Join-Path $toolsDir "Translumo\Translumo.exe")
    $capswriterExists = Test-Path (Join-Path $toolsDir "CapsWriter-Offline\start_server.exe")

    if ($translumoExists) {
        Write-Host "[OK] Translumo: tools\Translumo\Translumo.exe" -ForegroundColor Green
    } else {
        Write-Host "[MISSING] Translumo not found" -ForegroundColor Red
    }

    if ($capswriterExists) {
        Write-Host "[OK] CapsWriter-Offline: tools\CapsWriter-Offline\start_server.exe" -ForegroundColor Green
    } else {
        Write-Host "[MISSING] CapsWriter-Offline not found" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Download CapsWriter models (required):" -ForegroundColor White
    Write-Host "   Visit: https://github.com/HaujetZhao/CapsWriter-Offline/releases" -ForegroundColor White
    Write-Host "   Download models.zip" -ForegroundColor White
    Write-Host "   Extract to: tools\CapsWriter-Offline\models\" -ForegroundColor White
    Write-Host ""
    Write-Host "2. Configure Qwen API:" -ForegroundColor White
    Write-Host "   Edit: config\qwen-config.json" -ForegroundColor White
    Write-Host "   Get API key from: https://dashscope.aliyuncs.com/" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Quick Start:" -ForegroundColor White
    Write-Host "   Run: scripts\startup.bat" -ForegroundColor White
    Write-Host "   Or run: scripts\quick_launch.bat" -ForegroundColor White
    Write-Host ""
    Write-Host "Press any key to continue..." -ForegroundColor White
    Read-Host

} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Deployment Failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download manually:" -ForegroundColor Yellow
    Write-Host "1. Translumo: https://github.com/ramjke/Translumo/releases" -ForegroundColor White
    Write-Host "   Download: Translumo_1.0.2.zip" -ForegroundColor White
    Write-Host ""
    Write-Host "2. CapsWriter-Offline: https://github.com/HaujetZhao/CapsWriter-Offline/releases" -ForegroundColor White
    Write-Host "   Download: CapsWriter-Offline-Windows-64bit.zip" -ForegroundColor White
    Write-Host "   And models.zip (required)" -ForegroundColor White
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Red
    Read-Host
    exit 1
}