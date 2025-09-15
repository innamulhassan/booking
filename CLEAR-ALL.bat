@echo off
REM Clear All - Master Cleanup Batch Script
REM Calls both log clearing and database clearing scripts

setlocal enabledelayedexpansion
set "SCRIPT_NAME=CLEAR-ALL"
set "START_TIME=%date% %time%"

echo 🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹
echo 🧹 COMPLETE SYSTEM CLEANUP - CLEAR ALL
echo 🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹🧹
echo ⏰ Started at: %START_TIME%
echo 📂 Working directory: %CD%
echo.
echo This script will:
echo    1️⃣ Clear all logs and session directories
echo    2️⃣ Clear database conversion data and messages
echo    3️⃣ Prepare system for fresh start
echo.

REM Initialize status variables
set LOGS_SUCCESS=0
set DB_SUCCESS=0

echo 🗂️ STEP 1/2: LOG CLEANUP
echo ============================================================
echo 🔄 Executing: Clear All Logs

REM Check if CLEAR-LOGS.bat exists
if not exist "CLEAR-LOGS.bat" (
    echo ❌ CLEAR-LOGS.bat not found!
    set LOGS_SUCCESS=0
    goto :database_cleanup
)

REM Run log cleanup script
call "CLEAR-LOGS.bat"
set LOGS_RESULT=!errorlevel!

if !LOGS_RESULT! equ 0 (
    echo ✅ Clear All Logs completed successfully!
    set LOGS_SUCCESS=1
) else (
    echo ❌ Clear All Logs failed with exit code !LOGS_RESULT!
    set LOGS_SUCCESS=0
)

:database_cleanup
echo.
echo 💾 STEP 2/2: DATABASE CLEANUP
echo ============================================================
echo 🔄 Executing: Clear Database Conversion ^& Messages

REM Check if CLEAR-DATABASE.bat exists
if not exist "CLEAR-DATABASE.bat" (
    echo ❌ CLEAR-DATABASE.bat not found!
    set DB_SUCCESS=0
    goto :summary
)

REM Run database cleanup script
call "CLEAR-DATABASE.bat"
set DB_RESULT=!errorlevel!

if !DB_RESULT! equ 0 (
    echo ✅ Clear Database Conversion ^& Messages completed successfully!
    set DB_SUCCESS=1
) else (
    echo ❌ Clear Database Conversion ^& Messages failed with exit code !DB_RESULT!
    set DB_SUCCESS=0
)

:summary
echo.
echo 🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁
echo 🏁 CLEANUP SUMMARY
echo 🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁

echo 📊 Results:
if !LOGS_SUCCESS! equ 1 (
    echo    • Log Cleanup: ✅ SUCCESS
) else (
    echo    • Log Cleanup: ❌ FAILED
)

if !DB_SUCCESS! equ 1 (
    echo    • Database Cleanup: ✅ SUCCESS
) else (
    echo    • Database Cleanup: ❌ FAILED
)

echo.
if !LOGS_SUCCESS! equ 1 if !DB_SUCCESS! equ 1 (
    echo 🎉 ALL CLEANUP OPERATIONS COMPLETED SUCCESSFULLY!
    echo 🚀 System Status:
    echo    • All logs cleared and fresh logs directory created
    echo    • All message history and conversation data cleared
    echo    • Database ready for fresh conversion
    echo    • System ready for clean startup
    echo.
    echo 📋 Next Steps:
    echo    1. Run database_setup.py if you need to reinitialize database
    echo    2. Run START-ALL.bat to start the system fresh
    echo    3. All previous session data has been cleared
    set FINAL_EXIT_CODE=0
) else (
    echo ⚠️ SOME OPERATIONS FAILED
    if !LOGS_SUCCESS! equ 0 (
        echo    • Log cleanup failed - check file permissions
    )
    if !DB_SUCCESS! equ 0 (
        echo    • Database cleanup failed - check database connection
    )
    echo.
    echo 💡 Troubleshooting:
    echo    • Ensure virtual environment is activated
    echo    • Check database connection settings in .env
    echo    • Verify file permissions in project directory
    
    if !LOGS_SUCCESS! equ 1 (
        set FINAL_EXIT_CODE=2
    ) else if !DB_SUCCESS! equ 1 (
        set FINAL_EXIT_CODE=2
    ) else (
        set FINAL_EXIT_CODE=1
    )
)

echo.
echo 🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁🏁

endlocal & set "EXIT_CODE=%FINAL_EXIT_CODE%"
pause
exit /b %EXIT_CODE%