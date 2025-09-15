@echo off
title THERAPY BOOKING SYSTEM - MASTER STARTUP
color 0A
cls

echo.
echo ========================================================================
echo ===                                                                  ===
echo ===        THERAPY BOOKING WHATSAPP SYSTEM STARTUP                  ===
echo ===                    MASTER CONTROLLER                             ===
echo ===                                                                  ===
echo ========================================================================
echo.

REM Get current timestamp for logs
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%_%HH%-%Min%-%Sec%"

echo [*] Session Started: %DATE% %TIME%
echo [*] Working Directory: %CD%
echo [*] Log Session ID: %timestamp%
echo.

REM Create session log directory
if not exist "..\logs\session_%timestamp%" mkdir "..\logs\session_%timestamp%"
set "session_log=..\logs\session_%timestamp%\master_startup.log"

echo =============================================================================== >> "%session_log%"
echo THERAPY BOOKING SYSTEM STARTUP LOG >> "%session_log%"
echo Session: %timestamp% >> "%session_log%"
echo Started: %DATE% %TIME% >> "%session_log%"
echo =============================================================================== >> "%session_log%"

echo [*] STEP 1/3: STARTING WEBHOOK SERVER AND ADK AGENT
echo ===============================================================================
echo [*] Components to start:
echo    * FastAPI Webhook Server (Port 8000)
echo    * Google ADK Agent Integration  
echo    * MySQL Database Connection
echo    * Ultramsg WhatsApp Integration
echo.
echo [*] Starting webhook server in background...
echo [%TIME%] Starting webhook server... >> "%session_log%"

REM Start webhook server in background and capture PID
start "Therapy Booking Webhook Server" /MIN cmd /c "cd /d "%CD%\.." && call venv\Scripts\activate.bat && cd therapy_booking_app && python main.py > logs\session_%timestamp%\webhook_server.log 2>&1"

echo    [+] Webhook server process launched
echo    [*] Server logs: ..\logs\session_%timestamp%\webhook_server.log
echo    [*] Waiting for server initialization...

REM Wait for server to start
timeout /t 5 /nobreak >nul

REM Check if webhook server is responding
echo    [*] Testing webhook server connectivity...
for /L %%i in (1,1,10) do (
    curl -s http://localhost:8000/health >nul 2>&1
    if !errorlevel!==0 (
        echo    [+] SUCCESS: Webhook server is running on port 8000
        echo [%TIME%] Webhook server successfully started and responding >> "%session_log%"
        goto :tunnel_start
    ) else (
        echo    [*] Attempt %%i/10 - waiting for server...
        timeout /t 2 /nobreak >nul
    )
)
echo    [!] WARNING: Webhook server may not be responding yet (continuing anyway)
echo [%TIME%] WARNING: Webhook server not responding after 20 seconds >> "%session_log%"

:tunnel_start
echo.
echo [*] STEP 2/3: STARTING CLOUDFLARE TUNNEL
echo ===============================================================================
echo [*] Cloudflare Configuration:
echo    * Tunnel Name: therapy-booking
echo    * Domain: webhook-booking.innamul.com
echo    * Local Target: http://localhost:8000
echo.
echo [*] Starting Cloudflare tunnel in background...
echo [%TIME%] Starting Cloudflare tunnel... >> "%session_log%"

REM Start cloudflare tunnel in background with proper URL parameter
start "Cloudflare Tunnel - therapy-booking" /MIN cmd /c "cd /d "%CD%" && cloudflared.exe tunnel --url http://localhost:8000 run therapy-booking > logs\session_%timestamp%\cloudflare_tunnel.log 2>&1"

echo    [+] Cloudflare tunnel process launched  
echo    [*] Tunnel logs: logs\session_%timestamp%\cloudflare_tunnel.log
echo    [*] Waiting for tunnel establishment...

REM Wait for tunnel to establish  
timeout /t 8 /nobreak >nul

REM Check if tunnel is running
echo    [*] Checking tunnel status...
tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find "cloudflared.exe" >nul
if %errorlevel%==0 (
    echo    [+] SUCCESS: Cloudflare tunnel process is active
    echo [%TIME%] Cloudflare tunnel successfully started >> "%session_log%"
) else (
    echo    [!] ERROR: Cloudflare tunnel process not found
    echo [%TIME%] ERROR: Cloudflare tunnel failed to start >> "%session_log%"
)

echo.
echo [*] STEP 3/3: FINAL SYSTEM VERIFICATION  
echo ===============================================================================
echo [*] Running connectivity tests...
echo.

echo [*] SERVER STATUS:
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel%==0 (
    echo    [+] Webhook Server: RUNNING (localhost:8000)
) else (
    echo    [!] Webhook Server: NOT DETECTED
)

echo.
echo [*] TUNNEL STATUS:  
tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find "cloudflared.exe" >nul
if %errorlevel%==0 (
    echo    [+] Cloudflare Tunnel: RUNNING (webhook-booking.innamul.com)
) else (
    echo    [!] Cloudflare Tunnel: NOT RUNNING
)

echo.
echo ========================================================================
echo ===                    SYSTEM STARTUP COMPLETED                     ===  
echo ========================================================================
echo.
echo [*] WEBHOOK ENDPOINT: https://webhook-booking.innamul.com/webhook
echo [*] Configure this URL in your Ultramsg dashboard
echo.
echo [*] MONITORING ENDPOINTS:
echo    * Health Check: https://webhook-booking.innamul.com/health
echo    * API Docs: https://webhook-booking.innamul.com/docs
echo    * Local Health: http://localhost:8000/health
echo    * Local Docs: http://localhost:8000/docs
echo.
echo [*] LOG LOCATIONS:
echo    * Session Logs: logs\session_%timestamp%\
echo    * Webhook Server: logs\session_%timestamp%\webhook_server.log
echo    * Cloudflare Tunnel: logs\session_%timestamp%\cloudflare_tunnel.log
echo.
echo [*] TO STOP SYSTEM: Run STOP-ALL.bat
echo.

REM Log completion
echo [%TIME%] System startup completed >> "%session_log%"
echo =============================================================================== >> "%session_log%"

echo [*] System is now ready to receive WhatsApp messages!
echo [*] Press any key to exit (system will continue running in background)...
pause >nul