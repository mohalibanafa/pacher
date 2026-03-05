@echo off
setIOENCODING=utf8
title Cloud Patcher Loader 🚀

echo ==========================================
echo    Cloud Patcher - Professional Edition
echo ==========================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Error: Python is not installed on this system.
    echo [!] Please install Python 3.x from python.org and add it to PATH.
    pause
    exit /b
)

:: Check for core folder
if not exist "pacher\main.py" (
    if exist "main.py" (
        set SCRIPT_PATH=main.py
    ) else (
        echo [!] Error: main.py file not found.
        echo [!] Make sure to run this file from the project root directory.
        pause
        exit /b
    )
) else (
    set SCRIPT_PATH=pacher\main.py
)

echo [*] Starting application... 
echo [*] Dependencies will be checked automatically on startup.
echo.

python %SCRIPT_PATH%

if %errorlevel% neq 0 (
    echo.
    echo [-] An unexpected error occurred during execution.
    echo [-] Try running the script as administrator or review the errors above.
    pause
)
