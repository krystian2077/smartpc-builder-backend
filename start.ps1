# SmartPC Builder Backend - PowerShell Starter
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SmartPC Builder Backend - Starter" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host ""
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
Write-Host ""

# Install dependencies if needed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
Write-Host ""

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
python -m app.core.init_db
Write-Host ""

# Seed database with TechLipton presets
Write-Host "Seeding database with TechLipton presets..." -ForegroundColor Yellow
python -m app.core.seed_techlipton
Write-Host ""

# Start server
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host ""
Write-Host "Backend will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "API docs will be available at: http://localhost:8000/api/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

