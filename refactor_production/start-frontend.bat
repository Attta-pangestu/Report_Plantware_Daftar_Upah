@echo off
echo ==========================================
echo    Starting Payroll Frontend Server
echo ==========================================
echo.

cd /d "%~dp0frontend"

echo Checking Node.js dependencies...
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

echo Installing cross-env if needed...
npm list cross-env >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing cross-env...
    npm install cross-env --save-dev
)

echo.
echo Starting frontend server...
echo Frontend will run on: http://localhost:5175
echo Backend URL: http://localhost:8002
echo Press Ctrl+C to stop
echo.

npx cross-env VITE_BACKEND_URL=http://localhost:8002 npm run dev:test

pause