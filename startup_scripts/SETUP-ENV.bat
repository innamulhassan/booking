@echo off
title THERAPY BOOKING SYSTEM - ENVIRONMENT SETUP
color 0B
cls

echo.
echo ████████████████████████████████████████████████████████████████
echo ███                                                          ███
echo ███      THERAPY BOOKING SYSTEM - ENVIRONMENT SETUP         ███
echo ███                                                          ███
echo ████████████████████████████████████████████████████████████████
echo.

echo 🔧 VIRTUAL ENVIRONMENT SETUP AND MANAGEMENT
echo ===============================================================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo ✅ Virtual environment found: venv\
) else (
    echo ❌ Virtual environment not found. Creating new one...
    echo.
    echo 🔄 Creating virtual environment...
    python -m venv venv
    
    if exist "venv\Scripts\activate.bat" (
        echo ✅ Virtual environment created successfully
    ) else (
        echo ❌ Failed to create virtual environment
        echo    Make sure Python is installed and in PATH
        goto :error
    )
)

echo.
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

echo ✅ Virtual environment activated
echo    Current environment: %VIRTUAL_ENV%
echo.

REM Check if requirements.txt exists
if exist "requirements.txt" (
    echo 📋 Requirements file found: requirements.txt
    echo.
    echo 🔄 Installing/updating packages from requirements.txt...
    echo    This may take a few minutes...
    echo.
    
    pip install -r requirements.txt
    
    if %errorlevel%==0 (
        echo.
        echo ✅ All packages installed successfully
    ) else (
        echo.
        echo ⚠️  Some packages may have failed to install
        echo    Check the output above for details
    )
) else (
    echo ❌ requirements.txt not found
    echo    Creating basic requirements file...
    
    echo fastapi>=0.115.0 > requirements.txt
    echo uvicorn[standard]>=0.34.0 >> requirements.txt
    echo mysql-connector-python>=8.2.0 >> requirements.txt
    echo python-dotenv>=1.0.0 >> requirements.txt
    
    echo ✅ Basic requirements.txt created
    echo 🔄 Installing basic packages...
    pip install -r requirements.txt
)

echo.
echo ████████████████████████████████████████████████████████████████
echo ███                   SETUP COMPLETED                        ███  
echo ████████████████████████████████████████████████████████████████
echo.
echo 📊 ENVIRONMENT STATUS:
echo    • Virtual Environment: %VIRTUAL_ENV%
echo    • Python Version: 
python --version
echo    • Pip Version:
pip --version
echo.
echo 📝 INSTALLED PACKAGES:
echo    Run 'pip list' to see all installed packages
echo.
echo 🚀 NEXT STEPS:
echo    1. Run START-ALL.bat to launch the complete system
echo    2. Or run individual components from startup_scripts\
echo.
echo 💡 TIPS:
echo    • To activate venv manually: venv\Scripts\activate.bat
echo    • To deactivate venv: deactivate
echo    • To install new packages: pip install package_name
echo    • To update requirements: pip freeze > requirements.txt
echo.
goto :end

:error
echo.
echo ❌ Setup failed! Please check the errors above.
echo.
pause
exit /b 1

:end
echo Press any key to exit...
pause >nul