@echo off
REM Test runner batch script for Windows
REM Usage: test.bat [unit|integration|scripts|coverage|install|status] [verbose]

set SCRIPT_DIR=%~dp0
set ROOT_DIR=%SCRIPT_DIR%..
cd /d "%ROOT_DIR%"

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found in PATH
    echo Please install Python or add it to your PATH
    exit /b 1
)

REM Parse arguments
set TEST_TYPE=%1
set VERBOSE_FLAG=
if "%2"=="verbose" set VERBOSE_FLAG=-v
if "%2"=="-v" set VERBOSE_FLAG=-v

REM Default to all tests if no argument provided
if "%TEST_TYPE%"=="" set TEST_TYPE=all

echo 🧪 Therapy Booking System Test Runner
echo =====================================
echo.

if "%TEST_TYPE%"=="install" (
    echo 📦 Installing test requirements...
    python -m pip install -r tests\requirements-test.txt
    goto :eof
)

if "%TEST_TYPE%"=="status" (
    echo 🔍 Checking system status...
    python tests\run_tests.py --status
    goto :eof
)

if "%TEST_TYPE%"=="unit" (
    echo 🧪 Running unit tests...
    python tests\run_tests.py --unit %VERBOSE_FLAG%
    goto :eof
)

if "%TEST_TYPE%"=="integration" (
    echo 🔗 Running integration tests...
    python tests\run_tests.py --integration %VERBOSE_FLAG%
    goto :eof
)

if "%TEST_TYPE%"=="scripts" (
    echo 📜 Running test scripts...
    python tests\run_tests.py --scripts %VERBOSE_FLAG%
    goto :eof
)

if "%TEST_TYPE%"=="coverage" (
    echo 📊 Running tests with coverage...
    python tests\run_tests.py --coverage
    goto :eof
)

if "%TEST_TYPE%"=="all" (
    echo 🚀 Running all tests...
    python tests\run_tests.py %VERBOSE_FLAG%
    goto :eof
)

REM Help message
echo Usage: test.bat [command] [verbose]
echo.
echo Commands:
echo   install      Install test requirements
echo   status       Check if system is running
echo   unit         Run unit tests only
echo   integration  Run integration tests only  
echo   scripts      Run test scripts only
echo   coverage     Run tests with coverage report
echo   all          Run all tests (default)
echo.
echo Options:
echo   verbose      Show detailed output (-v)
echo.
echo Examples:
echo   test.bat                    # Run all tests
echo   test.bat unit verbose       # Run unit tests with verbose output
echo   test.bat install            # Install test dependencies
echo   test.bat coverage           # Generate coverage report