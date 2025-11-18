@echo off
echo Starting Backend Server...
cd backend
start /min cmd /c "python -c "from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8002)""
cd ..

timeout /t 5 /nobreak >nul

echo Starting Frontend Server...
cd frontend
start /min cmd /c "set PORT=5175&& npx vite --config ../vite.config.test.js"
cd ..

echo Servers are starting on:
echo Backend: http://localhost:8002
echo Frontend: http://localhost:5175

timeout /t 10 /nobreak >nul
start http://localhost:5175