@echo off
set DEV_MODE=true
set VITE_DEV_MODE=true
set TEST_MODE=true
cd backend
start cmd /c python -m uvicorn main:app --host 0.0.0.0 --port 8002
cd ..\frontend
start cmd /c npm run dev:test
cd ..
echo ========================================
echo Starting Frontend and Backend in Test Mode...
echo ========================================

cd /d "%~dp0"

REM Set environment variables for test mode
set TEST_MODE=true
set VITE_DEV_MODE=true
set DEV_MODE=true

echo.
echo Starting Backend Server on Port 8002...
echo ========================================

REM Start backend server in a new window
start "Backend Server - Payroll System" cmd /k "cd backend && python -c \"from main import app; import uvicorn; print('Starting Backend Server...'); print('Access API at: http://localhost:8002'); uvicorn.run(app, host='0.0.0.0', port=8002, reload=False)\""

REM Wait for backend to initialize
echo.
echo Waiting for backend to start...
timeout /t 8 /nobreak >nul

echo.
echo Starting Frontend Server on Port 5175...
echo ========================================

REM Start frontend server in a new window with test configuration
start "Frontend Server - Payroll UI" cmd /k "cd frontend && set PORT=5175 && vite --config ../vite.config.test.js"

REM Wait for frontend to initialize
echo.
echo Waiting for frontend to start...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo Servers started successfully!
echo.
echo Backend API: http://localhost:8002
echo Frontend UI: http://localhost:5175
echo.
echo Test endpoint directly on backend: http://localhost:8002/payroll/headers?month=5&year=2025&gang_code=H1H
echo Test endpoint through frontend: http://localhost:5175/payroll/headers?month=5&year=2025&gang_code=H1H
echo ========================================

REM Open the browser to the frontend
echo.
echo Opening browser to frontend...
start http://localhost:5175

echo.
echo Press any key to exit...
pause >nul
