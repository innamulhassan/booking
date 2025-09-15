@echo off
REM Clear Database Conversion and Messages - Batch Script Version
REM Clears database tables, conversation data, and message history

setlocal enabledelayedexpansion
set "SCRIPT_NAME=CLEAR-DATABASE"
set "START_TIME=%date% %time%"

echo.
echo DATABASE CLEANUP - Clear Conversion and Messages
echo ============================================================
echo Started at: %START_TIME%
echo Working directory: %CD%

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found!
    echo Please ensure virtual environment is set up first
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo Environment file not found!
    echo Please ensure .env file exists with database configuration
    pause
    exit /b 1
)

echo.
echo Testing database connection...

REM Create a simple database test script
echo import os > temp_db_test.py
echo from dotenv import load_dotenv >> temp_db_test.py
echo import pymysql >> temp_db_test.py
echo load_dotenv() >> temp_db_test.py
echo try: >> temp_db_test.py
echo     config = {'host': os.getenv('DB_HOST', 'localhost'), 'port': int(os.getenv('DB_PORT', '3306')), 'user': os.getenv('DB_USER', 'root'), 'password': os.getenv('DB_PASSWORD', ''), 'database': os.getenv('DB_NAME', 'booking')} >> temp_db_test.py
echo     conn = pymysql.connect(host=config['host'], port=config['port'], user=config['user'], password=config['password']) >> temp_db_test.py
echo     print('   MySQL server connection successful') >> temp_db_test.py
echo     cursor = conn.cursor() >> temp_db_test.py
echo     cursor.execute(f"SHOW DATABASES LIKE '{config['database']}'") >> temp_db_test.py
echo     result = cursor.fetchone() >> temp_db_test.py
echo     if result: >> temp_db_test.py
echo         print('   Database exists') >> temp_db_test.py
echo     else: >> temp_db_test.py
echo         print('   Database not found') >> temp_db_test.py
echo         exit(1) >> temp_db_test.py
echo     cursor.close() >> temp_db_test.py
echo     conn.close() >> temp_db_test.py
echo except Exception as e: >> temp_db_test.py
echo     print(f'   Database connection failed: {e}') >> temp_db_test.py
echo     exit(1) >> temp_db_test.py

REM Run database test
venv\Scripts\python.exe temp_db_test.py
set DB_TEST_RESULT=!errorlevel!

REM Clean up temp file
del temp_db_test.py >nul 2>&1

if !DB_TEST_RESULT! neq 0 (
    echo.
    echo Database connection test failed!
    echo Please check:
    echo    MySQL service is running
    echo    Database credentials in .env file
    echo    Database exists
    pause
    exit /b 1
)

echo.
echo Running database cleanup...
echo ============================================================

REM Create database cleanup script
echo import os > temp_db_clear.py
echo from dotenv import load_dotenv >> temp_db_clear.py
echo import pymysql >> temp_db_clear.py
echo load_dotenv() >> temp_db_clear.py
echo config = {'host': os.getenv('DB_HOST'), 'port': int(os.getenv('DB_PORT', '3306')), 'user': os.getenv('DB_USER'), 'password': os.getenv('DB_PASSWORD'), 'database': os.getenv('DB_NAME')} >> temp_db_clear.py
echo conn = pymysql.connect(**config) >> temp_db_clear.py
echo cursor = conn.cursor() >> temp_db_clear.py
echo print('Connected to database') >> temp_db_clear.py
echo tables = ['messages', 'conversations', 'appointments', 'schema_migrations'] >> temp_db_clear.py
echo cursor.execute('SET FOREIGN_KEY_CHECKS = 0') >> temp_db_clear.py
echo total_cleared = 0 >> temp_db_clear.py
echo for table in tables: >> temp_db_clear.py
echo     try: >> temp_db_clear.py
echo         cursor.execute(f'SELECT COUNT(*) FROM {table}') >> temp_db_clear.py
echo         count = cursor.fetchone()[0] >> temp_db_clear.py
echo         cursor.execute(f'DELETE FROM {table}') >> temp_db_clear.py
echo         cursor.execute(f'ALTER TABLE {table} AUTO_INCREMENT = 1') >> temp_db_clear.py
echo         total_cleared += count >> temp_db_clear.py
echo         print(f'   Cleared {table}: {count} records') >> temp_db_clear.py
echo     except: >> temp_db_clear.py
echo         print(f'   Table {table} not found or empty') >> temp_db_clear.py
echo cursor.execute('SET FOREIGN_KEY_CHECKS = 1') >> temp_db_clear.py
echo cursor.execute('SELECT COUNT(*) FROM users') >> temp_db_clear.py
echo users_count = cursor.fetchone()[0] >> temp_db_clear.py
echo cursor.execute('SELECT COUNT(*) FROM therapist_availability') >> temp_db_clear.py
echo avail_count = cursor.fetchone()[0] >> temp_db_clear.py
echo conn.commit() >> temp_db_clear.py
echo cursor.close() >> temp_db_clear.py
echo conn.close() >> temp_db_clear.py
echo print('') >> temp_db_clear.py
echo print('DATABASE CLEANUP COMPLETED') >> temp_db_clear.py
echo print(f'Summary: {total_cleared} records cleared') >> temp_db_clear.py
echo print(f'Preserved: {users_count} users, {avail_count} availability records') >> temp_db_clear.py

REM Run database cleanup
venv\Scripts\python.exe temp_db_clear.py
set DB_CLEAR_RESULT=!errorlevel!

REM Clean up temp file  
del temp_db_clear.py >nul 2>&1

if !DB_CLEAR_RESULT! equ 0 (
    echo.
    echo ============================================================
    echo DATABASE CLEANUP COMPLETED SUCCESSFULLY!
    echo ============================================================
    echo System Status:
    echo    All message history cleared
    echo    All conversation data cleared
    echo    Database ready for fresh conversion
    echo    Essential user data preserved
    echo.
    echo Next Steps:
    echo    1. Run database_setup.py to reinitialize if needed
    echo    2. Run START-ALL.bat to start system fresh
    echo    3. All previous session data has been cleared
) else (
    echo.
    echo ============================================================
    echo DATABASE CLEANUP FAILED!
    echo ============================================================
    echo Troubleshooting:
    echo    Check database connection settings
    echo    Verify MySQL service is running
    echo    Ensure proper permissions
)

endlocal
pause
exit /b %DB_CLEAR_RESULT%