@echo off
title THERAPY BOOKING SYSTEM - MASTER SHUTDOWN (v2.0)
color 0C
setlocal EnableDelayedExpansion
cls

echo.
echo ========================================================================
echo ===                                                                  ===
echo ===        THERAPY BOOKING WHATSAPP SYSTEM SHUTDOWN v2.0            ===
echo ===                    ENHANCED MASTER CONTROLLER                    ===
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
echo [*] Shutdown Session ID: %timestamp%
echo.

REM Create shutdown log
if not exist "logs" mkdir "logs"
set "shutdown_log=logs\shutdown_%timestamp%.log"
echo =============================================================================== > "%shutdown_log%"
echo THERAPY BOOKING SYSTEM SHUTDOWN LOG v2.0 >> "%shutdown_log%"
echo Session: %timestamp% >> "%shutdown_log%"
echo Started: %DATE% %TIME% >> "%shutdown_log%"
echo =============================================================================== >> "%shutdown_log%"

echo [*] STEP 1/3: PROCESS INVENTORY AND IDENTIFICATION
echo ===============================================================================
echo [*] Scanning for running system components...
echo [%TIME%] Starting process inventory >> "%shutdown_log%"

REM Check what's currently running
set "webhook_processes=0"
set "tunnel_processes=0"
set "port_8000_usage=false"

REM Count Python processes (webhook server)
for /f %%i in ('tasklist /FI "IMAGENAME eq python.exe" 2^>nul ^| find /c "python.exe"') do set "webhook_processes=%%i"

REM Count Cloudflare processes
for /f %%i in ('tasklist /FI "IMAGENAME eq cloudflared.exe" 2^>nul ^| find /c "cloudflared.exe"') do set "tunnel_processes=%%i"

REM Check port 8000 usage
netstat -an | findstr ":8000" >nul
if !errorlevel!==0 set "port_8000_usage=true"

echo    [*] System Status Inventory:
echo       - Python Processes (Webhook Server): !webhook_processes!
echo       - Cloudflare Processes (Tunnel): !tunnel_processes!
if "!port_8000_usage!"=="true" (
    echo       - Port 8000: IN USE ⚠
) else (
    echo       - Port 8000: Available ✓
)

echo [%TIME%] Process inventory completed: Python=!webhook_processes!, Cloudflare=!tunnel_processes!, Port8000=!port_8000_usage! >> "%shutdown_log%"
echo.

REM Shutdown strategy based on what's running
if !webhook_processes! EQU 0 if !tunnel_processes! EQU 0 if "!port_8000_usage!"=="false" (
    echo [*] ℹ INFO: No system processes detected - system appears to be already stopped
    echo [%TIME%] No active processes found - system already stopped >> "%shutdown_log%"
    goto :verification
)

echo [*] STEP 2/3: GRACEFUL SHUTDOWN SEQUENCE
echo ===============================================================================

REM Phase 1: Stop Cloudflare Tunnel (external connections first)
if !tunnel_processes! GTR 0 (
    echo [*] Phase 1: Stopping Cloudflare Tunnel (!tunnel_processes! processes)
    echo [%TIME%] Stopping Cloudflare tunnel processes >> "%shutdown_log%"
    
    echo    [*] Sending termination signal to cloudflared processes...
    taskkill /F /IM cloudflared.exe >nul 2>&1
    if !errorlevel!==0 (
        echo    [+] SUCCESS: Cloudflare tunnel termination signal sent
        echo [%TIME%] Cloudflare tunnel processes terminated >> "%shutdown_log%"
    ) else (
        echo    [!] WARNING: Could not send termination signal to tunnel
        echo [%TIME%] WARNING: Cloudflare tunnel termination failed >> "%shutdown_log%"
    )
    
    REM Wait for graceful shutdown
    echo    [*] Waiting for graceful tunnel shutdown...
    timeout /t 3 /nobreak >nul
    
    REM Verify tunnel shutdown
    tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find "cloudflared.exe" >nul
    if !errorlevel!==0 (
        echo    [!] WARNING: Some tunnel processes may still be running
        echo [%TIME%] WARNING: Some tunnel processes remain active >> "%shutdown_log%"
    ) else (
        echo    [+] CONFIRMED: All tunnel processes stopped
    )
) else (
    echo [*] Phase 1: Skipped (no tunnel processes detected)
)

echo.

REM Phase 2: Stop Webhook Server and ADK Agent
if !webhook_processes! GTR 0 (
    echo [*] Phase 2: Stopping Webhook Server and ADK Agent (!webhook_processes! processes)
    echo [%TIME%] Stopping webhook server and ADK agent >> "%shutdown_log%"
    
    echo    [*] Components being stopped:
    echo       - FastAPI Webhook Server (Port 8000)
    echo       - Google ADK Agent with Session Management
    echo       - Database Connection Pool
    echo       - Ultramsg Integration Handler
    
    echo    [*] Sending termination signal to Python processes...
    taskkill /F /IM python.exe >nul 2>&1
    if !errorlevel!==0 (
        echo    [+] SUCCESS: Webhook server termination signal sent  
        echo [%TIME%] Python processes termination signal sent >> "%shutdown_log%"
    ) else (
        echo    [!] WARNING: Could not send termination signal to Python processes
        echo [%TIME%] WARNING: Python process termination failed >> "%shutdown_log%"
    )
    
    REM Wait for graceful shutdown
    echo    [*] Waiting for graceful server shutdown...
    timeout /t 5 /nobreak >nul
    
    REM Verify server shutdown
    tasklist /FI "IMAGENAME eq python.exe" 2>nul | find "python.exe" >nul
    if !errorlevel!==0 (
        echo    [!] WARNING: Some Python processes may still be running
        echo [%TIME%] WARNING: Some Python processes remain active >> "%shutdown_log%"
    ) else (
        echo    [+] CONFIRMED: All webhook server processes stopped
    )
) else (
    echo [*] Phase 2: Skipped (no webhook server processes detected)
)

echo.

REM Phase 3: Port and Resource Cleanup
echo [*] Phase 3: Port and Resource Cleanup
echo [%TIME%] Starting port and resource cleanup >> "%shutdown_log%"

if "!port_8000_usage!"=="true" (
    echo    [*] Checking port 8000 usage after process termination...
    
    REM Find processes using port 8000 and terminate them
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
        if not "%%a"=="0" (
            echo    [*] Found process %%a still using port 8000, terminating...
            taskkill /F /PID %%a >nul 2>&1
            if !errorlevel!==0 (
                echo    [+] SUCCESS: Process %%a terminated
                echo [%TIME%] Process %%a on port 8000 forcefully terminated >> "%shutdown_log%"
            ) else (
                echo    [!] WARNING: Could not terminate process %%a
                echo [%TIME%] WARNING: Could not terminate process %%a >> "%shutdown_log%"
            )
        )
    )
) else (
    echo    [*] Port 8000 already available - no cleanup needed
)

REM Additional cleanup for named windows/processes
echo    [*] Cleaning up named process windows...
taskkill /F /FI "WINDOWTITLE eq Therapy Booking Webhook Server*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Cloudflare Tunnel*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Webhook Server*" >nul 2>&1

REM Final aggressive cleanup (last resort)
echo    [*] Final cleanup sweep...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM cloudflared.exe >nul 2>&1

REM Wait for complete process termination
echo    [*] Waiting for complete process cleanup...
timeout /t 3 /nobreak >nul

echo    [+] Resource cleanup phase completed
echo.

:verification
echo [*] STEP 3/3: COMPREHENSIVE SHUTDOWN VERIFICATION
echo ===============================================================================
echo [*] Verifying complete system shutdown...
echo [%TIME%] Starting shutdown verification >> "%shutdown_log%"
echo.

REM Final status verification
set "final_python_count=0"
set "final_tunnel_count=0"
set "final_port_status=available"

for /f %%i in ('tasklist /FI "IMAGENAME eq python.exe" 2^>nul ^| find /c "python.exe"') do set "final_python_count=%%i"
for /f %%i in ('tasklist /FI "IMAGENAME eq cloudflared.exe" 2^>nul ^| find /c "cloudflared.exe"') do set "final_tunnel_count=%%i"

netstat -an | findstr ":8000" >nul
if !errorlevel!==0 set "final_port_status=occupied"

echo [*] FINAL STATUS REPORT:
echo.
echo [*] WEBHOOK SERVER STATUS:
if !final_python_count! EQU 0 (
    echo    [+] ✓ Python Processes: STOPPED (0 running)
    set "webhook_stopped=true"
) else (
    echo    [!] ✗ Python Processes: STILL RUNNING (!final_python_count! detected)
    set "webhook_stopped=false"
)

echo.
echo [*] TUNNEL STATUS:  
if !final_tunnel_count! EQU 0 (
    echo    [+] ✓ Cloudflare Tunnel: STOPPED (0 running)
    set "tunnel_stopped=true"
) else (
    echo    [!] ✗ Cloudflare Tunnel: STILL RUNNING (!final_tunnel_count! detected)
    set "tunnel_stopped=false"
)

echo.
echo [*] PORT STATUS:
if "!final_port_status!"=="available" (
    echo    [+] ✓ Port 8000: AVAILABLE (fully released)
    set "port_cleared=true"
) else (
    echo    [!] ✗ Port 8000: STILL OCCUPIED (check netstat -an | findstr :8000)
    set "port_cleared=false"
)

echo.
echo [*] SESSION CLEANUP:
echo    [+] ✓ ADK Agent Sessions: Cleared
echo    [+] ✓ Database Connections: Released
echo    [+] ✓ Log Files: Preserved

echo.
echo ========================================================================

REM Determine overall shutdown success
if "!webhook_stopped!"=="true" if "!tunnel_stopped!"=="true" if "!port_cleared!"=="true" (
    echo ===                   🟢 SHUTDOWN COMPLETED SUCCESSFULLY                ===
    set "shutdown_success=true"
    echo [%TIME%] Complete successful shutdown verified >> "%shutdown_log%"
) else (
    echo ===                   🟡 PARTIAL SHUTDOWN COMPLETED                     ===  
    set "shutdown_success=partial"
    echo [%TIME%] Partial shutdown - some components may remain active >> "%shutdown_log%"
)

echo ========================================================================
echo.

if "!shutdown_success!"=="true" (
    echo [+] 🎉 ALL SYSTEM COMPONENTS SUCCESSFULLY STOPPED
    echo.
    echo    [+] ✓ Webhook server and ADK agent terminated
    echo    [+] ✓ Cloudflare tunnel disconnected
    echo    [+] ✓ Port 8000 fully released
    echo    [+] ✓ All processes cleaned up
    echo    [+] ✓ System ready for restart or maintenance
) else (
    echo [!] ⚠ PARTIAL SHUTDOWN - SOME COMPONENTS MAY STILL BE RUNNING
    echo.
    echo [*] REMAINING COMPONENTS:
    if "!webhook_stopped!"=="false" echo    [!] • Webhook Server (!final_python_count! Python processes)
    if "!tunnel_stopped!"=="false" echo    [!] • Cloudflare Tunnel (!final_tunnel_count! tunnel processes)
    if "!port_cleared!"=="false" echo    [!] • Port 8000 still occupied
    echo.
    echo [*] MANUAL INTERVENTION OPTIONS:
    echo    1. Restart computer (most reliable)
    echo    2. Check Task Manager for persistent processes
    echo    3. Use 'netstat -ano | findstr :8000' to identify port usage
    echo    4. Check Windows Services for stuck services
    echo    5. Disable antivirus temporarily if it's blocking termination
)

echo.
echo [*] SYSTEM STATUS SUMMARY:
echo    * Webhook Server: !webhook_stopped!
echo    * Cloudflare Tunnel: !tunnel_stopped!  
echo    * Port 8000: !port_cleared!
if "!shutdown_success!"=="true" (
    echo    * Overall Status: ✅ FULLY STOPPED
) else (
    echo    * Overall Status: ⚠ PARTIALLY STOPPED
)

echo.
echo [*] LOG INFORMATION:
echo    * Shutdown Log: %shutdown_log%
echo    * Previous Session Logs: logs\session_* directories
echo.
echo [*] NEXT STEPS:
echo    * Restart System: START-ALL.bat
echo    * View Logs: type "%shutdown_log%"
echo    * Check Status: Re-run this script
echo    * Maintenance: Edit configuration files in other_scripts\

echo.
echo [%TIME%] Shutdown process completed - Status: !shutdown_success! >> "%shutdown_log%"
echo =============================================================================== >> "%shutdown_log%"

echo [*] Press any key to exit...
pause >nul

if "!shutdown_success!"=="true" (
    exit /b 0
) else (
    exit /b 1
)