@echo off
echo ========================================
echo   TESTING PRODUCTION CONFIGURATION
echo   Target IP: 10.0.0.110
echo ========================================
echo.

echo Testing Backend Health Check...
curl -s http://10.0.0.110:8002/payroll/health
echo.
echo.

echo Testing Backend Mode Information...
curl -s http://10.0.0.110:8002/dev-mode
echo.
echo.

echo Testing Frontend Access...
curl -s -I http://10.0.0.110:5176
echo.

echo ========================================
echo   PRODUCTION CONFIGURATION TEST COMPLETE
echo ========================================
echo.
echo If all tests pass, the production configuration is working correctly.
echo.
pause