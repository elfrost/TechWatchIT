@echo off
title TechWatchIT - Business Technology Monitor
color 0A

echo.
echo ================================================
echo    TechWatchIT - Business Technology Monitor
echo ================================================
echo    - Fetches today's business technology news
echo    - Automatic updates every 6 hours
echo    - CVE priority monitoring
echo ================================================
echo.

REM Set the working directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.11+ first.
    pause
    exit /B 1
)

echo [INFO] Python detected
python --version

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [INFO] Virtual environment activated
)

REM Check environment file
if not exist ".env" (
    echo.
    echo [WARNING] No .env file found!
    echo Please create .env with your configuration:
    echo   OPENAI_API_KEY=your_key_here
    echo   MYSQL_HOST=localhost
    echo   MYSQL_USER=root
    echo   MYSQL_PASSWORD=
    echo   MYSQL_DATABASE=techwatchit
    echo.
    pause
)

echo.
echo [STARTUP] Starting TechWatchIT with automatic scheduling...
echo.
echo - Fetching today's articles on startup
echo - Dashboard will be available at: http://localhost:5000  
echo - Automatic updates every 6 hours
echo - Press Ctrl+C to stop
echo.

REM Start the main application with scheduler
python main.py --auto-mode

pause