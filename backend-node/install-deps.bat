@echo off
REM Quick dependency installer for backend-node

echo Installing Node.js dependencies...
call npm install

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies
    echo Please run: npm install
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies installed successfully!
pause

