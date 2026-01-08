# PowerShell script to start the PostgreSQL Chat API

Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting PostgreSQL Chat API" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = py --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.11 or higher" -ForegroundColor Red
    exit 1
}

# Start the application
Write-Host "Starting application on http://localhost:3300" -ForegroundColor Yellow
Write-Host "Press CTRL+C to stop" -ForegroundColor Yellow
Write-Host ""

# Use py -m uvicorn instead of uvicorn directly to avoid path issues
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3300
