# Quick Fix Script for Replay 404 Error

Write-Host "=" * 60
Write-Host "GR RACE GUARDIAN - Replay 404 Quick Fix"
Write-Host "=" * 60

Write-Host "`nStep 1: Stopping any running servers..."
Write-Host "Looking for Python processes on port 8000..."

# Find process on port 8000
$port8000 = netstat -ano | findstr ":8000.*LISTENING"
if ($port8000) {
    $pid = ($port8000 -split '\s+')[-1]
    Write-Host "Found process $pid on port 8000"
    Write-Host "Killing process..."
    taskkill /F /PID $pid 2>$null
    Start-Sleep -Seconds 2
    Write-Host "[OK] Process stopped"
} else {
    Write-Host "[INFO] No process found on port 8000"
}

Write-Host "Looking for Node.js processes on port 3000..."
$port3000 = netstat -ano | findstr ":3000.*LISTENING"
if ($port3000) {
    $pid3000 = ($port3000 -split '\s+')[-1]
    Write-Host "Found process $pid3000 on port 3000"
    Write-Host "Killing process..."
    taskkill /F /PID $pid3000 2>$null
    Start-Sleep -Seconds 2
    Write-Host "[OK] Process stopped"
} else {
    Write-Host "[INFO] No process found on port 3000"
}

Write-Host "`nStep 2: Clearing Next.js build cache..."
$nextDir = "frontend-next\.next"
if (Test-Path $nextDir) {
    Remove-Item -Recurse -Force $nextDir
    Write-Host "[OK] Cleared .next directory"
} else {
    Write-Host "[INFO] No .next directory to clear"
}

Write-Host "`nStep 3: Starting backend server..."
Write-Host "Navigate to backend-python directory and run:"
Write-Host "  cd backend-python"
Write-Host "  python app.py"
Write-Host ""
Write-Host "Step 4: Starting frontend server (in a new terminal)..."
Write-Host "Navigate to frontend-next directory and run:"
Write-Host "  cd frontend-next"
Write-Host "  npm run dev"
Write-Host ""
Write-Host "Step 5: Access the application..."
Write-Host "  Open: http://localhost:3000/track-replay"
Write-Host ""
Write-Host "=" * 60
Write-Host "Manual Steps Required:"
Write-Host "=" * 60
Write-Host "1. Open a terminal and run: cd backend-python && python app.py"
Write-Host "2. Open another terminal and run: cd frontend-next && npm run dev"
Write-Host "3. Wait for both servers to start completely"
Write-Host "4. Open browser to http://localhost:3000/track-replay"
Write-Host "5. Hard refresh (Ctrl+Shift+R) if needed"
Write-Host "=" * 60
