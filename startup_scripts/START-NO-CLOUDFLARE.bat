@echo off
echo.
echo ================================================================================
echo STARTING THERAPY BOOKING SYSTEM (WITHOUT CLOUDFLARE)
echo ================================================================================
echo.

REM Activate virtual environment
echo [%time%] Activating virtual environment...
call "%~dp0venv\Scripts\activate.bat"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Create session directory with timestamp
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ("%TIME%") do (set mytime=%%a-%%b)
set session=session_%mydate%_%mytime::=-%
if not exist logs\%session% mkdir logs\%session%

echo [%time%] Session: %session%
echo.

REM Start webhook server
echo [%time%] Starting webhook server...
cd therapy_booking_app
start "Webhook Server" /D "%~dp0therapy_booking_app" cmd /k "python main.py > ..\logs\%session%\webhook_server.log 2>&1"
cd ..

REM Wait a bit for services to start
echo [%time%] Waiting for services to initialize...
timeout /t 5 /nobreak >nul

REM Check if webhook server is running
echo [%time%] Checking webhook server status...
netstat -an | findstr :8000 >nul
if %ERRORLEVEL% EQU 0 (
    echo [%time%] ✓ Webhook server is running on port 8000
) else (
    echo [%time%] ✗ Webhook server not detected on port 8000
)

echo.
echo ================================================================================
echo SYSTEM STARTUP COMPLETE (WITHOUT CLOUDFLARE)
echo ================================================================================
echo.
echo Webhook Server: http://localhost:8000
echo Health Check: http://localhost:8000/health
echo Demo Interface: http://localhost:8000/demo
echo Session Logs: logs\%session%
echo.
echo Press any key to view system status...
pause >nul

echo.
echo === SYSTEM STATUS ===
echo.
echo Active processes:
tasklist | findstr /i "python"
echo.
echo Network connections:
netstat -an | findstr :8000
echo.
echo Log files:
dir logs\%session% 2>nul
echo.
echo Press any key to exit...
pause >nul