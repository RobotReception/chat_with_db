# Activate virtual environment and start service
& .\venv\Scripts\Activate.ps1
venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3300
