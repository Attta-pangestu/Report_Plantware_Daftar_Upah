@echo off
echo ===========================================
echo    Starting Payroll Backend (Local DB)
echo ===========================================
echo.

cd /d "%~dp0backend"

echo Setting environment for local database...
set DB_PROFILE=local

echo Checking Python dependencies...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting backend with local database (localhost)...
echo Backend will run on: http://localhost:8002
echo Press Ctrl+C to stop
echo.

python main.py

pause