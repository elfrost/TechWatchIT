@echo off
title TechWatchIT - Business Technology Monitoring
color 0A

echo.
echo ================================================
echo    TechWatchIT - Business Technology Monitor
echo ================================================
echo.

REM Set the working directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.11+ first.
    echo Download: https://python.org
    pause
    exit /B 1
)

echo [INFO] Python detected
python --version

REM Check if virtual environment exists
if not exist "venv" (
    echo.
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /B 1
    )
)

REM Activate virtual environment
echo.
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo.
echo [SETUP] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /B 1
)

REM Check environment file
if not exist ".env" (
    echo.
    echo [SETUP] Creating .env file from template...
    if exist "env.example" (
        copy "env.example" ".env" >nul 2>&1
    )
    echo.
    echo [WARNING] Please edit .env file with your API keys:
    echo   - OPENAI_API_KEY=your_openai_api_key
    echo   - MYSQL_* settings for your database
    echo.
    pause
)

REM Main menu
:MENU
cls
echo.
echo ================================================
echo    TechWatchIT - Main Menu
echo ================================================
echo.
echo [1] Run Complete Pipeline (Fetch + Process + Alerts)
echo [2] Initialize Database  
echo [3] Fetch RSS Feeds Only
echo [4] Process Articles with AI
echo [5] Launch Web Dashboard
echo [6] System Status
echo [7] Send Test Alert
echo [8] Exit
echo.
set /p choice="Select option (1-8): "

if "%choice%"=="1" goto PIPELINE
if "%choice%"=="2" goto INIT_DB
if "%choice%"=="3" goto FETCH
if "%choice%"=="4" goto PROCESS
if "%choice%"=="5" goto DASHBOARD
if "%choice%"=="6" goto STATUS
if "%choice%"=="7" goto ALERT
if "%choice%"=="8" goto EXIT

echo [ERROR] Invalid choice! Please select 1-8.
pause
goto MENU

:PIPELINE
echo.
echo [RUN] Starting complete pipeline...
python main.py --pipeline
if errorlevel 1 (
    echo [ERROR] Pipeline failed!
) else (
    echo [SUCCESS] Pipeline completed successfully!
)
pause
goto MENU

:INIT_DB
echo.
echo [RUN] Initializing database...
python main.py --init
if errorlevel 1 (
    echo [ERROR] Database initialization failed!
) else (
    echo [SUCCESS] Database initialized successfully!
)
pause
goto MENU

:FETCH
echo.
echo [RUN] Fetching RSS feeds...
python main.py --fetch
if errorlevel 1 (
    echo [ERROR] RSS fetch failed!
) else (
    echo [SUCCESS] RSS feeds fetched successfully!
)
pause
goto MENU

:PROCESS
echo.
echo [RUN] Processing articles with AI...
python main.py --process
if errorlevel 1 (
    echo [ERROR] Article processing failed!
) else (
    echo [SUCCESS] Articles processed successfully!
)
pause
goto MENU

:DASHBOARD
echo.
echo [RUN] Starting web dashboard...
echo.
echo Dashboard will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python main.py --api
pause
goto MENU

:STATUS
echo.
echo [RUN] Checking system status...
python main.py --status
pause
goto MENU

:ALERT
echo.
echo [RUN] Checking critical alerts...
python main.py --alerts
pause
goto MENU

:EXIT
echo.
echo [INFO] Deactivating virtual environment...
deactivate
echo [INFO] Goodbye!
pause
exit /B 0