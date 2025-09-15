@echo off
title THERAPY BOOKING SYSTEM - MASTER SHUTDOWN
color 0C
cls

echo.
echo ========================================================================
echo ===                                                                  ===
echo ===        THERAPY BOOKING WHATSAPP SYSTEM SHUTDOWN                 ===
echo ===                    MASTER CONTROLLER                             ===
echo ===                                                                  ===
echo ========================================================================
echo.

REM Get current timestamp for logs
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%_%HH%-%Min%-%Sec%"

echo [*] Shutdown Started: %DATE% %TIME%
echo [*] Working Directory: %CD%
echo.

REM Find the latest session log
set "shutdown_log=..\logs\shutdown_%timestamp%.log"
echo =============================================================================== > "%shutdown_log%"
echo THERAPY BOOKING SYSTEM SHUTDOWN LOG >> "%shutdown_log%"
echo Session: %timestamp% >> "%shutdown_log%"
echo Started: %DATE% %TIME% >> "%shutdown_log%"
echo =============================================================================== >> "%shutdown_log%"

echo [*] STEP 1/2: STOPPING CLOUDFLARE TUNNEL
echo ===============================================================================
echo [*] Terminating Cloudflare tunnel processes...
echo [%TIME%] Stopping Cloudflare tunnel... >> "%shutdown_log%"

REM Kill cloudflared processes
tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find "cloudflared.exe" >nul
if %errorlevel%==0 (
    echo    [+] Found active Cloudflare tunnel process(es)
    echo    [*] Terminating tunnel connections...
    taskkill /F /IM cloudflared.exe >nul 2>&1
    if %errorlevel%==0 (
        echo    [+] SUCCESS: Cloudflare tunnel stopped
        echo [%TIME%] Cloudflare tunnel successfully terminated >> "%shutdown_log%"
    ) else (
        echo    [!] WARNING: Could not terminate tunnel (may require manual stop)
        echo [%TIME%] WARNING: Tunnel termination failed >> "%shutdown_log%"
    )
) else (
    echo    [i] INFO: No active Cloudflare tunnel found
    echo [%TIME%] No active Cloudflare tunnel found >> "%shutdown_log%"
)
echo.

echo [*] STEP 2/2: STOPPING WEBHOOK SERVER AND ADK AGENT  
echo ===============================================================================
echo [*] Terminating webhook server processes...
echo [%TIME%] Stopping webhook server... >> "%shutdown_log%"

REM Find and kill Python processes running the webhook server
echo    [*] Searching for webhook server processes...

REM First, kill all Python processes (most reliable method)
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find "python.exe" >nul
if %errorlevel%==0 (
    echo    [*] Found Python processes, terminating all...
    taskkill /F /IM python.exe >nul 2>&1
    if %errorlevel%==0 (
        echo    [+] SUCCESS: All Python processes terminated
        echo [%TIME%] All Python processes successfully terminated >> "%shutdown_log%"
    ) else (
        echo    [!] WARNING: Some Python processes could not be terminated
        echo [%TIME%] WARNING: Python process termination partially failed >> "%shutdown_log%"
    )
) else (
    echo    [i] INFO: No Python processes found
    echo [%TIME%] No Python processes found >> "%shutdown_log%"
)

REM Additional method: Kill any process using port 8000 (backup)
echo    [*] Checking for processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    if not "%%a"=="0" (
        echo    [*] Found process %%a using port 8000, terminating...
        taskkill /F /PID %%a >nul 2>&1
        if %errorlevel%==0 (
            echo    [+] SUCCESS: Process %%a terminated
            echo [%TIME%] Process %%a on port 8000 terminated >> "%shutdown_log%"
        )
    )
)

REM Additional cleanup - kill any remaining webhook server windows and processes
taskkill /F /FI "WINDOWTITLE eq Therapy Booking Webhook Server*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Webhook Server*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Cloudflare Tunnel*" >nul 2>&1

REM Final aggressive cleanup for any remaining processes
echo    [*] Final cleanup of any remaining processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM cloudflared.exe >nul 2>&1

REM Wait a moment for processes to fully terminate
timeout /t 2 /nobreak >nul

echo.
echo [*] FINAL SYSTEM VERIFICATION
echo ===============================================================================

REM Final status check
echo [*] Verifying complete shutdown...
echo.

echo [*] TUNNEL STATUS CHECK:
tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find "cloudflared.exe" >nul
if %errorlevel%==0 (
    echo    [!] WARNING: Cloudflare tunnel still running
    echo [%TIME%] WARNING: Tunnel still detected after shutdown attempt >> "%shutdown_log%"
) else (
    echo    [+] CONFIRMED: Cloudflare tunnel stopped
)

echo.
echo [*] SERVER STATUS CHECK:
netstat -an | findstr ":8000" >nul
if %errorlevel%==0 (
    echo    [!] WARNING: Port 8000 still in use
    echo [%TIME%] WARNING: Port 8000 still occupied after shutdown >> "%shutdown_log%"
) else (
    echo    [+] CONFIRMED: Port 8000 released
)

echo.
echo ========================================================================
echo ===                   SHUTDOWN COMPLETED                            ===
echo ========================================================================
echo.

REM Show final status
netstat -an | findstr ":8000" >nul
set webhook_status=%errorlevel%

tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find "cloudflared.exe" >nul  
set tunnel_status=%errorlevel%

if %webhook_status%==1 if %tunnel_status%==1 (
    echo [+] SUCCESS: Complete system shutdown confirmed
    echo    [+] Webhook server: STOPPED
    echo    [+] Cloudflare tunnel: STOPPED  
    echo    [+] All processes terminated successfully
    echo.
    echo [%TIME%] Complete successful shutdown >> "%shutdown_log%"
) else (
    echo [!] PARTIAL SHUTDOWN: Some processes may still be running
    if %webhook_status%==0 echo    [!] Webhook server may still be active
    if %tunnel_status%==0 echo    [!] Cloudflare tunnel may still be active
    echo.
    echo [*] TROUBLESHOOTING:
    echo    * Check Task Manager for remaining python.exe or cloudflared.exe
    echo    * Restart computer if processes cannot be terminated
    echo    * Check firewall/antivirus if shutdown fails repeatedly
    echo.
    echo [%TIME%] Partial shutdown - some processes may remain >> "%shutdown_log%"
)

echo [*] SHUTDOWN LOG SAVED: %shutdown_log%
echo.
echo [*] SYSTEM READY FOR:
echo    [*] Restart: Run START-ALL.bat
echo    [*] Troubleshooting: Check logs in logs\ directory
echo    [*] Configuration: Edit files in other_scripts\ directory
echo.

REM Log completion  
echo [%TIME%] Shutdown process completed >> "%shutdown_log%"
echo =============================================================================== >> "%shutdown_log%"

echo Press any key to exit...
pause >nul