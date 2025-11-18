@echo off
echo ========================================
echo Starting Frontend and Backend in Test Mode...
echo ========================================

REM Change to the project directory
cd /d %~dp0

REM Set environment variables for test mode
set TEST_MODE=true
set VITE_DEV_MODE=true
set DEV_MODE=true

echo.
echo Starting Backend Server on Port 8002...
echo ========================================

REM Start backend server
start "Backend Payroll System" cmd /c "cd backend && python -c \"import sys; from main import app; import uvicorn; print('Backend started on port 8002'); uvicorn.run(app, host='0.0.0.0', port=8002)\""

timeout /t 5 /nobreak >nul

echo.
echo Starting Frontend Server on Port 5175...
echo ========================================

REM Start frontend server 
start "Frontend Payroll UI" cmd /c "cd frontend && set PORT=5175 && npx vite --config ../vite.config.test.js"

echo.
echo ========================================
echo Servers are starting...
echo.
echo Backend: http://localhost:8002
echo Frontend: http://localhost:5175
echo ========================================

REM Open browser after a delay
timeout /t 15 /nobreak >nul
start http://localhost:5175