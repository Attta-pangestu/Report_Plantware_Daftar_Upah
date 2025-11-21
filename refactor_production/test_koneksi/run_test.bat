@echo off
echo ============================================
echo    REMOTE SQL SERVER CONNECTION TEST
echo ============================================
echo.
echo Server: 10.0.0.110,1433
echo Username: sa
echo Password: ptrj@123
echo Database: db_ptrj
echo ============================================
echo.

cd /d "%~dp0"

echo Installing required package if needed...
pip show pyodbc >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing pyodbc...
    pip install pyodbc
)

echo.
echo Starting connection test...
echo.

python test_remote_sql.py

echo.
echo Test completed. Check results above.
echo.
pause