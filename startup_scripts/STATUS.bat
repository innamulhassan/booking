@echo off
title THERAPY BOOKING SYSTEM - STATUS CHECK
color 0B
cls

echo.
echo ████████████████████████████████████████████████████████████████
echo ███                                                          ███
echo ███        THERAPY BOOKING SYSTEM STATUS MONITOR            ███
echo ███                                                          ███
echo ████████████████████████████████████████████████████████████████
echo.

echo 📅 Status Check: %DATE% %TIME%
echo 📂 Working Directory: %CD%
echo.

echo ===============================================================================
echo 🔍 SYSTEM COMPONENT STATUS
echo ===============================================================================
echo.

REM Check webhook server status
echo 📊 WEBHOOK SERVER STATUS:
netstat -an | findstr ":8000" >nul
if %errorlevel%==0 (
    echo    ✅ RUNNING - Webhook server active on port 8000
    echo    🌐 Local access: http://localhost:8000
    echo    📋 Health check: http://localhost:8000/health
) else (
    echo    ❌ STOPPED - No service detected on port 8000
)

echo.
echo 📊 CLOUDFLARE TUNNEL STATUS:
tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find "cloudflared.exe" >nul
if %errorlevel%==0 (
    echo    ✅ RUNNING - Cloudflare tunnel process active
    echo    🌐 Public access: https://webhook-booking.innamul.com
    echo    📋 Health check: https://webhook-booking.innamul.com/health
) else (
    echo    ❌ STOPPED - Cloudflare tunnel not running
)

echo.
echo ===============================================================================
echo 🌐 ENDPOINT STATUS
echo ===============================================================================

netstat -an | findstr ":8000" >nul
set server_running=%errorlevel%

tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find "cloudflared.exe" >nul
set tunnel_running=%errorlevel%

if %server_running%==0 if %tunnel_running%==0 (
    echo 🎉 SYSTEM STATUS: FULLY OPERATIONAL
    echo.
    echo 📱 WHATSAPP WEBHOOK URL: 
    echo    https://webhook-booking.innamul.com/webhook
    echo.
    echo 📊 MONITORING ENDPOINTS:
    echo    • Health: https://webhook-booking.innamul.com/health
    echo    • Stats: https://webhook-booking.innamul.com/stats
    echo    • Docs: https://webhook-booking.innamul.com/docs
    echo.
    echo 📋 LOCAL ENDPOINTS (for testing):
    echo    • Health: http://localhost:8000/health
    echo    • Stats: http://localhost:8000/stats
    echo    • Docs: http://localhost:8000/docs
    echo.
) else if %server_running%==0 (
    echo ⚠️  SYSTEM STATUS: PARTIAL - Server only
    echo    ✅ Webhook server running locally
    echo    ❌ Cloudflare tunnel not active
    echo    💡 Run: START-ALL.bat to start tunnel
    echo.
) else if %tunnel_running%==0 (
    echo ⚠️  SYSTEM STATUS: PARTIAL - Tunnel only
    echo    ❌ Webhook server not running  
    echo    ✅ Cloudflare tunnel active (but no backend)
    echo    💡 Run: START-ALL.bat to start server
    echo.
) else (
    echo ❌ SYSTEM STATUS: STOPPED
    echo    ❌ Webhook server not running
    echo    ❌ Cloudflare tunnel not active
    echo    💡 Run: START-ALL.bat to start system
    echo.
)

echo ===============================================================================
echo 📁 LOG FILES
echo ===============================================================================
echo.

REM Find latest session logs
if exist "logs\" (
    echo 📝 Available log directories:
    for /f "delims=" %%i in ('dir "logs\session_*" /b /ad /o-d 2^>nul') do (
        echo    📂 %%i (Latest session logs)
        goto :found_logs
    )
    echo    📄 logs\app_*.log (Application logs)
    echo    📂 No session logs found
    :found_logs
    echo.
    echo 💡 To view logs: Use text editor or 'type logs\filename.log'
) else (
    echo    📂 logs\ directory not found
)

echo.
echo ===============================================================================
echo 🎛️  QUICK ACTIONS
echo ===============================================================================
echo.
echo [1] Start complete system (if stopped)
echo [2] Stop complete system (if running)  
echo [3] Refresh status check
echo [4] Open log directory
echo [5] Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo 🚀 Starting complete system...
    call START-ALL.bat
) else if "%choice%"=="2" (
    echo.
    echo 🛑 Stopping complete system...
    call STOP-ALL.bat
) else if "%choice%"=="3" (
    echo.
    echo 🔄 Refreshing status...
    timeout /t 1 /nobreak >nul
    goto :eof
) else if "%choice%"=="4" (
    echo.
    echo 📂 Opening logs directory...
    if exist "logs\" (
        explorer logs\
    ) else (
        echo ❌ Logs directory not found
    )
    echo.
    pause
) else if "%choice%"=="5" (
    echo.
    echo 👋 Goodbye!
    exit
) else (
    echo.
    echo ❌ Invalid choice. Please try again.
    timeout /t 2 /nobreak >nul
    goto :eof
)
