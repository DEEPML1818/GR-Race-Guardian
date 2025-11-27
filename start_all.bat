@echo off
REM GR Race Guardian - Enhanced Master Startup Script
REM Starts all services with dependency checks, auto-restart, log routing, and process cleanup

setlocal enabledelayedexpansion

echo ========================================
echo  GR Race Guardian - Starting Services
echo ========================================
echo.

REM Create logs directory
if not exist "logs" mkdir logs
if not exist "logs\python" mkdir logs\python
if not exist "logs\node" mkdir logs\node
if not exist "logs\frontend" mkdir logs\frontend

REM Kill old processes on ports 8000, 3001, 3000
echo [INFO] Checking for existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000"') do (
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel!==0 echo [INFO] Killed process on port 8000 (PID: %%a)
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3001"') do (
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel!==0 echo [INFO] Killed process on port 3001 (PID: %%a)
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000"') do (
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel!==0 echo [INFO] Killed process on port 3000 (PID: %%a)
)
timeout /t 2 /nobreak >nul

REM ========================================
REM Dependency Checks
REM ========================================
echo.
echo [CHECK] Verifying dependencies...
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.8+
    echo [INFO] Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo [OK] Python found: !PYTHON_VERSION!

REM Check Node.js installation
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found! Please install Node.js 18+
    echo [INFO] Download from: https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=1" %%v in ('node --version 2^>^&1') do set NODE_VERSION=%%v
echo [OK] Node.js found: !NODE_VERSION!

REM Check npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm not found!
    pause
    exit /b 1
)
echo [OK] npm found

REM Check pip
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip not found!
    pause
    exit /b 1
)
echo [OK] pip found

REM Check if ports are available (after cleanup)
netstat -an | findstr ":8000" >nul
if not errorlevel 1 (
    echo [WARNING] Port 8000 is still in use. Python API may not start.
)

netstat -an | findstr ":3001" >nul
if not errorlevel 1 (
    echo [WARNING] Port 3001 is still in use. Node.js API may not start.
)

netstat -an | findstr ":3000" >nul
if not errorlevel 1 (
    echo [WARNING] Port 3000 is still in use. Frontend may not start.
)

echo.
echo [OK] All dependency checks passed!
echo.

REM ========================================
REM Start Python FastAPI Service
REM ========================================
echo [1/4] Starting Python FastAPI service...
cd backend-python

REM Check if Python dependencies are installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing Python dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install Python dependencies
        echo [INFO] Check requirements.txt and pip installation
        pause
        exit /b 1
    )
    echo [OK] Python dependencies installed
)

REM Start Python API with log routing and auto-restart
set PYTHON_STARTED=0
set PYTHON_ATTEMPTS=0
set MAX_PYTHON_ATTEMPTS=3

:python_start_loop
set /a PYTHON_ATTEMPTS+=1
echo [INFO] Starting Python API (attempt !PYTHON_ATTEMPTS!/!MAX_PYTHON_ATTEMPTS!)...

REM Start Python API in new window with log routing
start "GR Race Guardian - Python API" cmd /k "cd /d %~dp0backend-python && python app.py 2>&1 | tee logs\python\python_api_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"

REM Wait for Python API to boot (delay)
echo [INFO] Waiting for Python API to initialize...
timeout /t 5 /nobreak >nul

REM Check if Python API is responding
curl -s http://localhost:8000/health >nul 2>&1
if not errorlevel 1 (
    set PYTHON_STARTED=1
    echo [OK] Python API started successfully on http://localhost:8000
    goto :python_ok
)

if !PYTHON_ATTEMPTS! LSS !MAX_PYTHON_ATTEMPTS! (
    echo [WARNING] Python API not responding, retrying... (attempt !PYTHON_ATTEMPTS!/!MAX_PYTHON_ATTEMPTS!)
    timeout /t 3 /nobreak >nul
    goto :python_start_loop
)

:python_ok
cd ..

if !PYTHON_STARTED!==0 (
    echo [ERROR] Python API failed to start after !MAX_PYTHON_ATTEMPTS! attempts
    echo [INFO] Check Python API window and logs\python\ for errors
    echo [INFO] Common issues: Port 8000 in use, missing dependencies, syntax errors
)

echo.

REM ========================================
REM Start Node.js API Service
REM ========================================
echo [2/4] Starting Node.js API service...
cd backend-node

REM Check if node_modules exists
if not exist "node_modules" (
    echo [INFO] Installing Node.js dependencies...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install Node.js dependencies
        echo [INFO] Check package.json and npm installation
        pause
        exit /b 1
    )
    echo [OK] Node.js dependencies installed
)

REM Start Node.js API with log routing and auto-restart
set NODE_STARTED=0
set NODE_ATTEMPTS=0
set MAX_NODE_ATTEMPTS=3

:node_start_loop
set /a NODE_ATTEMPTS+=1
echo [INFO] Starting Node.js API (attempt !NODE_ATTEMPTS!/!MAX_NODE_ATTEMPTS!)...

REM Start Node.js API in new window with log routing
start "GR Race Guardian - Node API" cmd /k "cd /d %~dp0backend-node && node server.js 2>&1 | tee logs\node\node_api_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"

REM Wait for Node API to start (delay)
echo [INFO] Waiting for Node.js API to initialize...
timeout /t 5 /nobreak >nul

REM Check if Node API is responding
curl -s http://localhost:3001/health >nul 2>&1
if not errorlevel 1 (
    set NODE_STARTED=1
    echo [OK] Node.js API started successfully on http://localhost:3001
    goto :node_ok
)

if !NODE_ATTEMPTS! LSS !MAX_NODE_ATTEMPTS! (
    echo [WARNING] Node.js API not responding, retrying... (attempt !NODE_ATTEMPTS!/!MAX_NODE_ATTEMPTS!)
    timeout /t 3 /nobreak >nul
    goto :node_start_loop
)

:node_ok
cd ..

if !NODE_STARTED!==0 (
    echo [WARNING] Node.js API may not be responding yet
    echo [INFO] Check Node.js API window and logs\node\ for errors
)

echo.

REM ========================================
REM Start Next.js Frontend
REM ========================================
echo [3/4] Starting Next.js Frontend...
cd frontend-next

REM Check if node_modules exists
if not exist "node_modules" (
    echo [INFO] Installing Frontend dependencies...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install Frontend dependencies
        echo [INFO] Check package.json and npm installation
        pause
        exit /b 1
    )
    echo [OK] Frontend dependencies installed
)

REM Start Frontend with log routing
start "GR Race Guardian - Frontend" cmd /k "cd /d %~dp0frontend-next && npm run dev 2>&1 | tee logs\frontend\frontend_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"

cd ..

echo.

REM ========================================
REM Final Status
REM ========================================
echo [4/4] All services starting...
echo.
echo ========================================
echo  Services Started!
echo ========================================
echo.
echo  Python API: http://localhost:8000
echo  Node.js API: http://localhost:3001
echo  Frontend: http://localhost:3000
echo.
echo  Log Files:
echo  - Python: logs\python\python_api_*.log
echo  - Node.js: logs\node\node_api_*.log
echo  - Frontend: logs\frontend\frontend_*.log
echo.
echo  Monitoring:
echo  - Check service windows for any errors
echo  - Services will auto-restart if they crash (check windows)
echo  - Logs are being written to logs\ directory
echo.
echo  Health Checks:
echo  - Python: curl http://localhost:8000/health
echo  - Node.js: curl http://localhost:3001/health
echo.
echo  Press any key to open frontend in browser...
pause >nul

REM Open frontend in browser
start http://localhost:3000

echo.
echo  Services are running in separate windows.
echo  Close those windows to stop the services.
echo.
echo  To stop all services:
echo  - Close all service windows
echo  - Or run: stop_all.bat (if available)
echo.
pause
