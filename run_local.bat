@echo off
REM Helper: run pipeline, server, or frontend
if "%1"=="pipeline" (
  python backend-python\run_pipeline.py
  goto :eof
)
if "%1"=="server" (
  pushd backend-python
  call run_server.bat
  popd
  goto :eof
)
if "%1"=="frontend" (
  pushd frontend-demo
  if exist node_modules ( ) else ( npm install )
  npm start
  popd
  goto :eof
)
echo Usage: run_local.bat ^(pipeline^|server^|frontend^)
