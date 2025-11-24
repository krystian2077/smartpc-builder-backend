@echo off
echo ========================================
echo   SmartPC Builder Backend - Starter
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo.

REM Install dependencies if needed
echo Checking dependencies...
pip install -r requirements.txt --quiet
echo.

REM Initialize database
echo Initializing database...
python -m app.core.init_db
echo.

REM Seed database with TechLipton presets
echo Seeding database with TechLipton presets...
python -m app.core.seed_techlipton
echo.

REM Start server
echo Starting FastAPI server...
echo.
echo Backend will be available at: http://localhost:8000
echo API docs will be available at: http://localhost:8000/api/docs
echo.
echo Press Ctrl+C to stop the server
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

