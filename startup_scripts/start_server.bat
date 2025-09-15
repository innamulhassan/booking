@echo off
echo Starting Therapy Booking Server...
call ..\venv\Scripts\activate.bat
python ..\other_scripts\complete_webhook_integration.py
pause
