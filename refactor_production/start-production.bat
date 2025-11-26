@echo off
echo ========================================
echo   PAYROLL SYSTEM - PRODUCTION MODE
echo   Server IP: 10.0.0.110
echo ========================================
echo.

echo Starting Backend Server (10.0.0.110:8002)...
cd backend
start "Payroll Backend - Production" cmd /k "python main.py --mode prod --port 8002"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

echo Starting Frontend Server (10.0.0.110:5176)...
cd ../frontend
start "Payroll Frontend - Production" cmd /k "npm run prod:frontend"

echo.
echo ========================================
echo   PRODUCTION SERVERS STARTED
echo ========================================
echo Backend:  http://10.0.0.110:8002
echo Frontend: http://10.0.0.110:5176
echo.
echo Press any key to stop all servers...
pause >nul

echo.
echo Stopping production servers...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
echo Production servers stopped.
pause