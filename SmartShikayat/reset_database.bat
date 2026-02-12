@echo off
echo ========================================
echo Stopping Django Server and Resetting Database
echo ========================================
echo.

echo Step 1: Killing all Python processes...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo Step 2: Deleting database...
if exist db.sqlite3 (
    del /F db.sqlite3
    if exist db.sqlite3 (
        echo ERROR: Could not delete db.sqlite3 - file is still locked
        echo Please close any programs that might be using the database
        pause
        exit /b 1
    ) else (
        echo SUCCESS: Database deleted
    )
) else (
    echo Database file not found (already deleted)
)

echo.
echo Step 3: Running migrations...
python manage.py migrate

echo.
echo Step 4: Checking database schema...
python check_ai_lang_constraint.py

echo.
echo ========================================
echo Done! You can now start the server with:
echo python manage.py runserver
echo ========================================
pause
