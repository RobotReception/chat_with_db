@echo off
REM Activate virtual environment and start service
call venv\Scripts\activate.bat
venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3300
pause
