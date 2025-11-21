@echo off
echo ========================================
echo    Starting Payroll Backend Server
echo ========================================
echo.

cd /d "%~dp0backend"

echo Configuration: REMOTE DATABASE (10.0.0.110)
echo Database: db_ptrj
echo Authentication: SQL Server (sa/ptrj@123)
echo.

echo Checking Python dependencies...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Testing database connection...
python test_config.py

echo.
echo Starting backend server with REMOTE database...
echo Backend will run on: http://localhost:8002
echo Remote Database: 10.0.0.110:1433
echo Press Ctrl+C to stop
echo.

python main.py

pause