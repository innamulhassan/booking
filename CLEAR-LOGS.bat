@echo off
REM Clear All Logs - Batch Script Version
REM Removes all log files, session directories, and project cache files

setlocal enabledelayedexpansion
set "SCRIPT_NAME=CLEAR-LOGS"
set "START_TIME=%date% %time%"

echo.
echo 🗂️ CLEAR ALL LOGS
echo ==================================================
echo ⏰ Started at: %START_TIME%
echo 📂 Working directory: %CD%

REM Initialize counters
set /a SESSION_DIRS=0
set /a LOG_FILES=0
set /a CACHE_DIRS=0

REM Step 1: Remove logs directory and contents
echo.
echo 📁 Removing logs directory and all contents...
if exist "logs" (
    REM Count items before removal
    for /d %%d in ("logs\session_*") do (
        set /a SESSION_DIRS+=1
    )
    for %%f in ("logs\*.log") do (
        set /a LOG_FILES+=1
    )
    
    REM Remove entire logs directory
    rmdir /s /q "logs" >nul 2>&1
    if !errorlevel! equ 0 (
        echo    ✅ Removed !SESSION_DIRS! session directories
        echo    ✅ Removed !LOG_FILES! log files
    ) else (
        echo    ⚠️ Warning: Could not remove some log files
    )
) else (
    echo    ℹ️ No logs directory found - nothing to clear
)

REM Step 2: Remove Python cache files in project directories
echo.
echo 🐍 Removing Python project cache files...

REM List of project directories to clean
set PROJECT_DIRS=therapy_booking_app test_scripts other_scripts startup_scripts

for %%d in (%PROJECT_DIRS%) do (
    if exist "%%d" (
        echo    🔍 Cleaning %%d directory...
        
        REM Remove __pycache__ directories
        for /d /r "%%d" %%p in (*__pycache__*) do (
            if exist "%%p" (
                rmdir /s /q "%%p" >nul 2>&1
                if !errorlevel! equ 0 (
                    set /a CACHE_DIRS+=1
                    echo       - Removed cache dir: %%~nxp
                )
            )
        )
        
        REM Remove .pyc and .pyo files
        for /r "%%d" %%f in (*.pyc *.pyo) do (
            if exist "%%f" (
                del "%%f" >nul 2>&1
                echo       - Removed cache file: %%~nxf
            )
        )
    )
)

REM Clean root-level cache files
for %%f in (*.pyc *.pyo) do (
    if exist "%%f" (
        del "%%f" >nul 2>&1
        echo    - Removed root cache file: %%f
    )
)

if !CACHE_DIRS! equ 0 (
    echo    ℹ️ No project cache files found to remove
)

REM Step 3: Remove temporary files
echo.
echo 🗑️ Removing temporary files...
set /a TEMP_FILES=0

for %%f in (*.tmp *.temp *~ .DS_Store Thumbs.db) do (
    if exist "%%f" (
        del "%%f" >nul 2>&1
        set /a TEMP_FILES+=1
        echo    - Removed temp file: %%f
    )
)

if !TEMP_FILES! equ 0 (
    echo    ℹ️ No temporary files found
)

REM Step 4: Recreate empty logs directory
echo.
echo 📁 Recreating empty logs directory...
mkdir "logs" >nul 2>&1
if !errorlevel! equ 0 (
    echo    ✅ Created: %CD%\logs
) else (
    echo    ⚠️ Warning: Could not create logs directory
)

REM Summary
echo.
echo ==================================================
echo ✅ LOG CLEANUP COMPLETED
echo ==================================================
echo 📊 Summary:
echo    • Session directories removed: !SESSION_DIRS!
echo    • Log files removed: !LOG_FILES!
echo    • Cache directories removed: !CACHE_DIRS!
echo    • Temporary files removed: !TEMP_FILES!
echo    • Fresh logs directory created
echo    • System ready for clean logging
echo.
echo 🎉 Log cleanup completed successfully!

endlocal
pause
exit /b 0