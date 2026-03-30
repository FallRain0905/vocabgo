# Direct Download and Extract Script
# Downloads tools directly to tools directory

Write-Host "Starting direct download and deployment..." -ForegroundColor Green
Write-Host ""

# Set paths
$toolsDir = Join-Path $PSScriptRoot ".."
if (-not (Test-Path $toolsDir)) {
    New-Item -ItemType Directory -Path $toolsDir -Force
    Write-Host "Created tools directory: $toolsDir" -ForegroundColor Cyan
}

try {
    # Download Translumo - try different URL format
    Write-Host "[1/2] Downloading Translumo..." -ForegroundColor Yellow
    $translumoUrl = "https://github.com/ramjke/Translumo/releases/latest/download/Translumo_1.0.2.zip"
    $translumoZip = Join-Path $toolsDir "translumo_download.zip"

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $translumoUrl -OutFile $translumoZip -UseBasicParsing -TimeoutSec 30
        Write-Host "Translumo download completed!" -ForegroundColor Green

        # Extract Translumo
        Write-Host "Extracting Translumo..." -ForegroundColor Cyan
        $translumoDir = Join-Path $toolsDir "Translumo"
        if (-not (Test-Path $translumoDir)) {
            New-Item -ItemType Directory -Path $translumoDir -Force
        }
        Expand-Archive -Path $translumoZip -DestinationPath $translumoDir -Force
        Remove-Item $translumoZip -Force
        Write-Host "Translumo extraction completed!" -ForegroundColor Green

    } catch {
        Write-Host "Translumo download failed: $_" -ForegroundColor Red
    }

    # Download CapsWriter - try different URL format
    Write-Host "[2/2] Downloading CapsWriter-Offline..." -ForegroundColor Yellow
    $capswriterUrl = "https://github.com/HaujetZhao/CapsWriter-Offline/releases/latest/download/CapsWriter-Offline-Windows-64bit.zip"
    $capswriterZip = Join-Path $toolsDir "capswriter_download.zip"

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $capswriterUrl -OutFile $capswriterZip -UseBasicParsing -TimeoutSec 30
        Write-Host "CapsWriter-Offline download completed!" -ForegroundColor Green

        # Extract CapsWriter
        Write-Host "Extracting CapsWriter-Offline..." -ForegroundColor Cyan
        $capswriterDir = Join-Path $toolsDir "CapsWriter-Offline"
        if (-not (Test-Path $capswriterDir)) {
            New-Item -ItemType Directory -Path $capswriterDir -Force
        }
        Expand-Archive -Path $capswriterZip -DestinationPath $capswriterDir -Force
        Remove-Item $capswriterZip -Force
        Write-Host "CapsWriter-Offline extraction completed!" -ForegroundColor Green

    } catch {
        Write-Host "CapsWriter-Offline download failed: $_" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Deployment completed!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Translumo: tools\Translumo\Translumo.exe" -ForegroundColor White
    Write-Host "2. CapsWriter: tools\CapsWriter-Offline\start_server.exe" -ForegroundColor White
    Write-Host ""
    Write-Host "Note: CapsWriter needs model files" -ForegroundColor Yellow
    Write-Host "Download models from: https://github.com/HaujetZhao/CapsWriter-Offline/releases" -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host "Deployment failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download manually:" -ForegroundColor Yellow
    Write-Host "1. Translumo: https://github.com/ramjke/Translumo/releases" -ForegroundColor White
    Write-Host "2. CapsWriter: https://github.com/HaujetZhao/CapsWriter-Offline/releases" -ForegroundColor White
    exit 1
}