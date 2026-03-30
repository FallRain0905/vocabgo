# Translumo Download Script
# Download latest version of Translumo OCR tool

Write-Host "Downloading Translumo OCR tool..." -ForegroundColor Green
Write-Host ""

# Create tools directory
$toolsDir = Join-Path $PSScriptRoot "..\tools"
if (-not (Test-Path $toolsDir)) {
    New-Item -ItemType Directory -Path $toolsDir -Force
    Write-Host "Created tools directory: $toolsDir" -ForegroundColor Cyan
}

$translumoDir = Join-Path $toolsDir "Translumo"

try {
    Write-Host "Downloading Translumo from GitHub..." -ForegroundColor Yellow

    # Download main software
    $softwareUrl = "https://github.com/ramjke/Translumo/releases/download/v1.0.2/Translumo_1.0.2.zip"
    $softwareZip = Join-Path $toolsDir "Translumo.zip"

    Write-Host "Downloading main software..." -ForegroundColor Cyan
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $softwareUrl -OutFile $softwareZip -UseBasicParsing
    Write-Host "Download completed!" -ForegroundColor Green

    # Extract files
    Write-Host "Extracting files..." -ForegroundColor Yellow
    Expand-Archive -Path $softwareZip -DestinationPath $translumoDir -Force
    Write-Host "Extraction completed!" -ForegroundColor Green

    # Clean up
    Remove-Item $softwareZip -Force
    Write-Host "Cleaned up temporary files" -ForegroundColor Cyan

    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Translumo installed successfully!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Installation path: $translumoDir" -ForegroundColor White
    Write-Host "Run file: $translumoDir\Translumo.exe" -ForegroundColor White
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "1. Double-click Translumo.exe" -ForegroundColor White
    Write-Host "2. Press Alt+G to open settings" -ForegroundColor White
    Write-Host "3. Press Alt+Q to select screen area" -ForegroundColor White
    Write-Host "4. Press ~ to start translation" -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
    Write-Host "Please download manually: https://github.com/ramjke/Translumo/releases" -ForegroundColor Yellow
    exit 1
}