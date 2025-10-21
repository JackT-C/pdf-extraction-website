@echo off
echo Starting PDF Medical Report Data Extraction Tool...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start the Flask application
echo Server starting at http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python app.py