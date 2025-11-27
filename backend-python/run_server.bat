@echo off
REM Start uvicorn server for backend-python (Windows)
cd /d "%~dp0"
echo Activating virtual environment if present...
if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)
echo Starting uvicorn on http://127.0.0.1:8000
python -m uvicorn app:app --host 127.0.0.1 --port 8000
