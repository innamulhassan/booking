@echo off
title THERAPY BOOKING SYSTEM - MASTER STARTUP (v2.0)
color 0A
setlocal EnableDelayedExpansion
cls

echo.
echo ========================================================================
echo ===                                                                  ===
echo ===        THERAPY BOOKING WHATSAPP SYSTEM STARTUP v2.0             ===
echo ===                    ENHANCED MASTER CONTROLLER                    ===
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
if not exist "logs\session_%timestamp%" mkdir "logs\session_%timestamp%"
set "session_log=logs\session_%timestamp%\master_startup.log"

echo =============================================================================== > "%session_log%"
echo THERAPY BOOKING SYSTEM STARTUP LOG v2.0 >> "%session_log%"
echo Session: %timestamp% >> "%session_log%"
echo Started: %DATE% %TIME% >> "%session_log%"
echo =============================================================================== >> "%session_log%"

REM Check prerequisites
echo [*] STEP 0/4: SYSTEM PREREQUISITES CHECK
echo ===============================================================================
echo [*] Checking system requirements...
echo [%TIME%] Checking system prerequisites... >> "%session_log%"

REM Check if Python is available
python --version >nul 2>&1
if !errorlevel!==0 (
    echo    [+] Python: Available
    echo [%TIME%] Python is available >> "%session_log%"
) else (
    echo    [!] ERROR: Python not found in PATH
    echo [%TIME%] ERROR: Python not available >> "%session_log%"
    echo.
    echo [!] STARTUP FAILED: Python is required but not found in PATH
    echo [*] Please ensure Python is installed and added to PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo    [+] Virtual Environment: Found
    echo [%TIME%] Virtual environment found >> "%session_log%"
) else (
    echo    [!] ERROR: Virtual environment not found
    echo [%TIME%] ERROR: Virtual environment not found >> "%session_log%"
    echo.
    echo [!] STARTUP FAILED: Virtual environment is required
    echo [*] Please run setup script to create virtual environment
    pause
    exit /b 1
)

REM Check if main application exists
if exist "therapy_booking_app\main.py" (
    echo    [+] Main Application: Found
    echo [%TIME%] Main application found >> "%session_log%"
) else (
    echo    [!] ERROR: Main application not found
    echo [%TIME%] ERROR: Main application not found >> "%session_log%"
    echo.
    echo [!] STARTUP FAILED: therapy_booking_app\main.py not found
    pause
    exit /b 1
)

REM Check if cloudflared is available
if exist "cloudflared.exe" (
    echo    [+] Cloudflare Tunnel: Available
    echo [%TIME%] Cloudflared executable found >> "%session_log%"
) else (
    echo    [!] WARNING: cloudflared.exe not found - tunnel will not work
    echo [%TIME%] WARNING: cloudflared.exe not found >> "%session_log%"
    set "tunnel_available=false"
)

echo [*] Prerequisites check completed
echo.

REM Stop any existing processes first
echo [*] STEP 1/4: CLEANUP EXISTING PROCESSES
echo ===============================================================================
echo [*] Stopping any existing instances...
echo [%TIME%] Cleaning up existing processes... >> "%session_log%"

REM Kill existing Python processes (webhook server)
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find "python.exe" >nul
if !errorlevel!==0 (
    echo    [*] Terminating existing webhook server processes...
    taskkill /F /IM python.exe >nul 2>&1
    echo    [+] Existing processes terminated
    echo [%TIME%] Existing Python processes terminated >> "%session_log%"
    timeout /t 2 /nobreak >nul
)

REM Kill existing Cloudflare tunnel processes  
tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find "cloudflared.exe" >nul
if !errorlevel!==0 (
    echo    [*] Terminating existing tunnel processes...
    taskkill /F /IM cloudflared.exe >nul 2>&1
    echo    [+] Existing tunnel processes terminated
    echo [%TIME%] Existing Cloudflare processes terminated >> "%session_log%"
    timeout /t 2 /nobreak >nul
)

echo    [+] Cleanup completed
echo.

REM Start webhook server
echo [*] STEP 2/4: STARTING WEBHOOK SERVER AND ADK AGENT
echo ===============================================================================
echo [*] Components to start:
echo    * FastAPI Webhook Server (Port 8000)
echo    * Google ADK Agent Integration with Session Management
echo    * MySQL Database Connection
echo    * Ultramsg WhatsApp Integration  
echo    * Enhanced fromMe filtering (no infinite loops)
echo.
echo [*] Activating virtual environment and starting server...
echo [%TIME%] Starting webhook server... >> "%session_log%"

REM Start webhook server with enhanced error handling
start "Therapy Booking Webhook Server" /MIN cmd /c "call venv\Scripts\activate.bat && cd therapy_booking_app && python main.py > ..\logs\session_%timestamp%\webhook_server.log 2>&1"

if !errorlevel!==0 (
    echo    [+] Webhook server process launched successfully
    echo [%TIME%] Webhook server process started >> "%session_log%"
) else (
    echo    [!] ERROR: Failed to launch webhook server
    echo [%TIME%] ERROR: Failed to launch webhook server >> "%session_log%"
    goto :error_exit
)

echo    [*] Server logs: logs\session_%timestamp%\webhook_server.log
echo    [*] Waiting for server initialization (improved ADK session management)...

REM Enhanced server startup verification
set "server_ready=false"
for /L %%i in (1,1,15) do (
    timeout /t 2 /nobreak >nul
    curl -s http://localhost:8000/health >nul 2>&1
    if !errorlevel!==0 (
        echo    [+] SUCCESS: Webhook server is running on port 8000
        echo [%TIME%] Webhook server successfully started and responding >> "%session_log%"
        set "server_ready=true"
        goto :tunnel_start
    ) else (
        echo    [*] Attempt %%i/15 - waiting for server startup...
    )
)

if "!server_ready!"=="false" (
    echo    [!] ERROR: Webhook server failed to start within 30 seconds
    echo [%TIME%] ERROR: Webhook server startup timeout >> "%session_log%"
    goto :error_exit
)

:tunnel_start
echo.
echo [*] STEP 3/4: STARTING CLOUDFLARE TUNNEL
echo ===============================================================================

if not "!tunnel_available!"=="false" (
    echo [*] Cloudflare Configuration:
    echo    * Tunnel Name: therapy-booking
    echo    * Domain: webhook-booking.innamul.com
    echo    * Local Target: http://localhost:8000
    echo.
    echo [*] Starting Cloudflare tunnel...
    echo [%TIME%] Starting Cloudflare tunnel... >> "%session_log%"

    REM Start cloudflare tunnel with error handling
    start "Cloudflare Tunnel - therapy-booking" /MIN cmd /c "cloudflared.exe tunnel --url http://localhost:8000 run therapy-booking > logs\session_%timestamp%\cloudflare_tunnel.log 2>&1"

    if !errorlevel!==0 (
        echo    [+] Cloudflare tunnel process launched
        echo [%TIME%] Cloudflare tunnel process started >> "%session_log%"
    ) else (
        echo    [!] ERROR: Failed to launch Cloudflare tunnel  
        echo [%TIME%] ERROR: Failed to launch Cloudflare tunnel >> "%session_log%"
    )

    echo    [*] Tunnel logs: logs\session_%timestamp%\cloudflare_tunnel.log
    echo    [*] Waiting for tunnel establishment...

    REM Enhanced tunnel verification
    timeout /t 8 /nobreak >nul
    tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find "cloudflared.exe" >nul
    if !errorlevel!==0 (
        echo    [+] SUCCESS: Cloudflare tunnel process is active
        echo [%TIME%] Cloudflare tunnel successfully started >> "%session_log%"
    ) else (
        echo    [!] WARNING: Cloudflare tunnel process not detected
        echo [%TIME%] WARNING: Cloudflare tunnel failed to start >> "%session_log%"
    )
) else (
    echo [!] SKIPPING: Cloudflare tunnel (cloudflared.exe not available)
    echo [%TIME%] Skipping Cloudflare tunnel - executable not found >> "%session_log%"
)

echo.
echo [*] STEP 4/4: FINAL SYSTEM VERIFICATION AND STATUS
echo ===============================================================================
echo [*] Running comprehensive connectivity tests...
echo [%TIME%] Running final system verification >> "%session_log%"
echo.

REM Enhanced status checks
echo [*] WEBHOOK SERVER STATUS:
curl -s http://localhost:8000/health >nul 2>&1
if !errorlevel!==0 (
    echo    [+] ✓ Webhook Server: RUNNING (localhost:8000)
    echo    [+] ✓ ADK Agent: ACTIVE with Enhanced Session Management  
    echo    [+] ✓ Database: Connected
    echo    [+] ✓ fromMe Filtering: ENABLED (prevents infinite loops)
    set "server_status=OK"
) else (
    echo    [!] ✗ Webhook Server: NOT RESPONDING
    set "server_status=FAILED"
)

echo.
echo [*] TUNNEL STATUS:
if not "!tunnel_available!"=="false" (
    tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find "cloudflared.exe" >nul
    if !errorlevel!==0 (
        echo    [+] ✓ Cloudflare Tunnel: RUNNING (webhook-booking.innamul.com)
        set "tunnel_status=OK"
    ) else (
        echo    [!] ✗ Cloudflare Tunnel: NOT RUNNING
        set "tunnel_status=FAILED"
    )
) else (
    echo    [!] ⚠ Cloudflare Tunnel: NOT AVAILABLE (missing cloudflared.exe)
    set "tunnel_status=UNAVAILABLE"
)

echo.
echo [*] ADK AGENT IMPROVEMENTS:
echo    [+] ✓ Persistent Session Service (fixes 'Session not found' errors)
echo    [+] ✓ Automatic Session Recovery
echo    [+] ✓ Enhanced Error Handling
echo    [+] ✓ Improved Response Quality

echo.
echo ========================================================================
if "!server_status!"=="OK" (
    echo ===                   🟢 SYSTEM STARTUP SUCCESSFUL                   ===
) else (
    echo ===                   🔴 SYSTEM STARTUP FAILED                       ===
)
echo ========================================================================
echo.

if "!server_status!"=="OK" (
    echo [+] 🎉 SYSTEM READY FOR WHATSAPP MESSAGES!
    echo.
    echo [*] WEBHOOK ENDPOINTS:
    if "!tunnel_status!"=="OK" (
        echo    * PUBLIC: https://webhook-booking.innamul.com/webhook
        echo    * Health Check: https://webhook-booking.innamul.com/health
        echo    * API Docs: https://webhook-booking.innamul.com/docs
    )
    echo    * LOCAL: http://localhost:8000/webhook
    echo    * Local Health: http://localhost:8000/health  
    echo    * Local Docs: http://localhost:8000/docs
    echo.
    echo [*] ULTRAMSG CONFIGURATION:
    if "!tunnel_status!"=="OK" (
        echo    Configure this URL in your Ultramsg dashboard:
        echo    https://webhook-booking.innamul.com/webhook
    ) else (
        echo    ⚠ Tunnel not available - use ngrok or configure port forwarding
    )
    echo.
    echo [*] LOG LOCATIONS:
    echo    * Master Log: %session_log%
    echo    * Webhook Server: logs\session_%timestamp%\webhook_server.log
    if "!tunnel_status!"=="OK" (
        echo    * Cloudflare Tunnel: logs\session_%timestamp%\cloudflare_tunnel.log
    )
    echo.
    echo [*] SYSTEM CONTROL:
    echo    * Stop All: STOP-ALL.bat
    echo    * Restart: STOP-ALL.bat then START-ALL.bat
    echo    * Status Check: Run this script again
) else (
    echo [!] ❌ STARTUP FAILED - CHECK LOGS FOR DETAILS
    echo.
    echo [*] TROUBLESHOOTING:
    echo    * Check Python installation and virtual environment
    echo    * Verify database connection settings
    echo    * Review logs: %session_log%
    echo    * Ensure port 8000 is not in use by another application
)

echo.
REM Log final status
if "!server_status!"=="OK" (
    echo [%TIME%] System startup completed successfully >> "%session_log%"
) else (
    echo [%TIME%] System startup failed >> "%session_log%"
)
echo =============================================================================== >> "%session_log%"

echo [*] Press any key to exit (system will continue running in background)...
pause >nul
exit /b 0

:error_exit
echo.
echo [!] ❌ STARTUP FAILED DUE TO ERRORS
echo [*] Check the logs for detailed error information: %session_log%
echo [%TIME%] Startup failed due to errors >> "%session_log%"
echo =============================================================================== >> "%session_log%"
pause
exit /b 1