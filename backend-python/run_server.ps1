# PowerShell script to start uvicorn for backend-python
Set-Location -Path $PSScriptRoot
if (Test-Path -Path ".venv\Scripts\Activate.ps1") {
    Write-Output "Activating virtualenv"
    . .\venv\Scripts\Activate.ps1
}
Write-Output "Starting uvicorn on http://127.0.0.1:8000"
python -m uvicorn app:app --host 127.0.0.1 --port 8000
