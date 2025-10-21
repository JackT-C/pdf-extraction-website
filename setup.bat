@echo off
echo ===================================================
echo PDF Medical Report Data Extraction Tool Setup
echo ===================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not found on this system.
    echo.
    echo SETUP REQUIRED:
    echo 1. Install Python 3.8+ from https://python.org
    echo 2. During installation, make sure to check "Add Python to PATH"
    echo 3. After installation, restart this command prompt
    echo 4. Run this setup script again
    echo.
    echo Alternatively, you can install Python from Microsoft Store:
    echo 1. Open Microsoft Store
    echo 2. Search for "Python"
    echo 3. Install Python 3.11 or later
    echo.
    echo Once Python is installed, run this script again.
    echo.
    pause
    exit /b 1
)

echo Python found: 
python --version

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo This might be because pip is not installed
    echo Try running: python -m ensurepip --upgrade
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip first
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo ===================================================
echo Setup completed successfully!
echo.
echo The following packages were installed:
echo - Flask (web framework)
echo - pdfplumber (PDF text extraction)
echo - pandas (data manipulation)
echo - xlsxwriter (Excel file creation)
echo - openpyxl (Excel file handling)
echo.
echo To run the application:
echo   1. Run: start_server.bat
echo   2. Open your browser to: http://localhost:5000
echo.
echo To test without the web interface:
echo   1. Place your PDF file in this folder
echo   2. Run: python example_usage.py
echo ===================================================
echo.
pause