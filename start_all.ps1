# GR Race Guardian - Master Startup Script (PowerShell)
# Starts all services: Python FastAPI, Node.js API, and Frontend

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " GR Race Guardian - Starting Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[✓] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found! Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check Node.js installation
try {
    $nodeVersion = node --version
    Write-Host "[✓] Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js not found! Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[1/4] Starting Python FastAPI service..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend-python; python app.py"

Start-Sleep -Seconds 3

Write-Host "[2/4] Starting Node.js API service..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend-node; npm install; node server.js"

Start-Sleep -Seconds 3

Write-Host "[3/4] Starting Next.js Frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend-next; npm install; npm run dev"

Write-Host "[4/4] All services starting..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Services Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Python API: http://localhost:8000" -ForegroundColor White
Write-Host "  Node.js API: http://localhost:3001" -ForegroundColor White
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host ""

Start-Sleep -Seconds 2

# Open frontend in browser
Write-Host "Opening frontend in browser..." -ForegroundColor Cyan
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "Services are running in separate windows." -ForegroundColor Green
Write-Host "Close those windows to stop the services." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

