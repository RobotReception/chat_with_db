@echo off
echo ========================================
echo Starting PostgreSQL Chat API
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher
    pause
    exit /b 1
)

REM Start the application
echo Starting application...
echo.
echo Options:
echo 1. Using python -m app.main
echo 2. Using uvicorn directly
echo.
echo Starting with option 1...
echo.

python -m app.main

REM Alternative: uncomment the line below to use uvicorn
REM python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3300

pause
