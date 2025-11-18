@echo off
echo Starting Frontend and Backend in Test Mode...

REM Set environment variables for test mode
set TEST_MODE=true
set VITE_DEV_MODE=true

REM Start backend in a new window
start "Backend Server" cmd /k "cd backend && python -c \"from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8002, reload=True)\""

REM Wait a bit for backend to start
timeout /t 5 /nobreak >nul

REM Start frontend in a new window
start "Frontend Server" cmd /k "cd frontend && npm run dev"

REM Open browser with test URL
echo Opening test page...
start http://localhost:5174/

pause