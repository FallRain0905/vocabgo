# CapsWriter-Offline Download Script
# Download latest version of CapsWriter-Offline tool

Write-Host "Downloading CapsWriter-Offline tool..." -ForegroundColor Green
Write-Host ""

# Create tools directory
$toolsDir = Join-Path $PSScriptRoot "..\tools"
if (-not (Test-Path $toolsDir)) {
    New-Item -ItemType Directory -Path $toolsDir -Force
    Write-Host "Created tools directory: $toolsDir" -ForegroundColor Cyan
}

$capswriterDir = Join-Path $toolsDir "CapsWriter-Offline"

try {
    Write-Host "Downloading CapsWriter-Offline from GitHub..." -ForegroundColor Yellow

    # Download main software
    $softwareUrl = "https://github.com/HaujetZhao/CapsWriter-Offline/releases/download/v2.5-alpha/CapsWriter-Offline-Windows-64bit.zip"
    $softwareZip = Join-Path $toolsDir "CapsWriter-Offline.zip"

    Write-Host "Downloading main software..." -ForegroundColor Cyan
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $softwareUrl -OutFile $softwareZip -UseBasicParsing
    Write-Host "Software download completed!" -ForegroundColor Green

    # Extract files
    Write-Host "Extracting files..." -ForegroundColor Yellow
    Expand-Archive -Path $softwareZip -DestinationPath $capswriterDir -Force
    Write-Host "Extraction completed!" -ForegroundColor Green

    # Clean up
    Remove-Item $softwareZip -Force
    Write-Host "Cleaned up temporary files" -ForegroundColor Cyan

    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "CapsWriter-Offline installed successfully!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Installation path: $capswriterDir" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Download models from Models Release page" -ForegroundColor White
    Write-Host "2. Extract models to models/folder_name/" -ForegroundColor White
    Write-Host "3. Run start_server.exe" -ForegroundColor White
    Write-Host "4. Run start_client.exe" -ForegroundColor White
    Write-Host "5. Press CapsLock to start recording" -ForegroundColor White
    Write-Host ""
    Write-Host "Models download page:" -ForegroundColor Yellow
    Write-Host "https://github.com/HaujetZhao/CapsWriter-Offline/releases" -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
    Write-Host "Please download manually:" -ForegroundColor Yellow
    Write-Host "1. Software: https://github.com/HaujetZhao/CapsWriter-Offline/releases" -ForegroundColor White
    Write-Host "2. Models: https://github.com/HaujetZhao/CapsWriter-Offline/releases" -ForegroundColor White
    exit 1
}