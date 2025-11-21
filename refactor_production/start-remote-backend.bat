@echo off
echo ===========================================
echo    Starting Payroll Backend (Remote DB)
echo ===========================================
echo.

cd /d "%~dp0backend"

echo Setting environment for remote database...
set DB_PROFILE=remote

echo Checking Python dependencies...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting backend with remote database (10.0.0.110)...
echo Backend will run on: http://localhost:8002
echo Press Ctrl+C to stop
echo.

python main.py

pause