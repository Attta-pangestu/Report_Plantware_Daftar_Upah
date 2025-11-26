@echo off
setlocal enabledelayedexpansion

:: ===================================================
:: Payroll System Network Launcher for Windows
:: ===================================================

echo.
echo ========================================
echo     PAYROLL SYSTEM NETWORK LAUNCHER
echo ========================================
echo.

:: Get IP Address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "ipv4"') do (
    set ip=%%a
    set ip=!ip: =!
)

if "!ip!"=="" (
    echo [ERROR] Could not detect IP address
    echo Please check your network connection
    pause
    exit /b 1
)

echo [INFO] Detected IP Address: !ip!
echo.

:: Create environment file
echo # Network Configuration > .env.network
echo VITE_BACKEND_HOST=!ip! >> .env.network
echo VITE_BACKEND_PORT=8002 >> .env.network
echo VITE_DEV_MODE=true >> .env.network

echo [SUCCESS] Created .env.network file
echo.

:: Menu
:menu
echo ========================================
echo           SELECT MODE
echo ========================================
echo.
echo 1. Start Backend Only
echo 2. Start Frontend Only
echo 3. Start Both Services
echo 4. Show IP Configuration
echo 5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto backend_only
if "%choice%"=="2" goto frontend_only
if "%choice%"=="3" goto start_both
if "%choice%"=="4" goto show_config
if "%choice%"=="5" goto exit

echo [ERROR] Invalid choice. Please try again.
goto menu

:backend_only
echo.
echo [INFO] Starting Backend Server...
echo [INFO] Backend will be available at: http://!ip!:8002
echo.
cd backend
start "Payroll Backend" cmd /k "python main.py"
echo [SUCCESS] Backend started in new window
echo.
echo Access URLs:
echo   Backend API: http://!ip!:8002
echo   API Docs:   http://!ip!:8002/docs
echo.
pause
goto menu

:frontend_only
echo.
echo [INFO] Starting Frontend Server...
echo [INFO] Frontend will be available at: http://!ip!:5175
echo [INFO] Make sure backend is running first!
echo.
cd frontend
start "Payroll Frontend" cmd /k "npm run dev:lan"
echo [SUCCESS] Frontend started in new window
echo.
echo Access URLs:
echo   Frontend:   http://!ip!:5175
echo   Backend:    http://!ip!:8002 (if running)
echo.
pause
goto menu

:start_both
echo.
echo [INFO] Starting Both Services...
echo.
echo [INFO] Starting Backend...
cd backend
start "Payroll Backend" cmd /k "python main.py"
timeout /t 3 /nobreak > nul

echo [INFO] Starting Frontend...
cd ..\frontend
start "Payroll Frontend" cmd /k "npm run dev:lan"

echo [SUCCESS] Both services started!
echo.
echo Access URLs:
echo   Frontend:   http://!ip!:5175
echo   Backend:    http://!ip!:8002
echo   API Docs:   http://!ip!:8002/docs
echo.
pause
goto menu

:show_config
echo.
echo ========================================
echo        NETWORK CONFIGURATION
echo ========================================
echo.
echo Local IP Address: !ip!
echo.
echo Service URLs:
echo   Frontend:   http://!ip!:5175
echo   Backend:    http://!ip!:8002
echo   API Docs:   http://!ip!:8002/docs
echo   Health Check: http://!ip!:8002/health
echo.
echo Configuration Files:
echo   Environment: .env.network
echo   Frontend Config: frontend\vite.config.js
echo   Backend Config: backend\main.py
echo.
echo Firewall Ports to Open:
echo   - TCP 8002 (Backend)
echo   - TCP 5175 (Frontend)
echo.
pause
goto menu

:exit
echo.
echo [INFO] Payroll System Network Launcher exiting...
echo.
echo Quick Reference:
echo   Backend:  cd backend ^&^& python main.py
echo   Frontend: cd frontend ^&^& npm run dev:lan
echo.
pause
exit /b 0