<#
.SYNOPSIS
    Start all TerraIQ services in separate PowerShell windows.
    Usage: .\dev.ps1
           .\dev.ps1 -Stop   (brings down Docker)
#>

param([switch]$Stop)

$root = $PSScriptRoot

if ($Stop) {
    Write-Host "Stopping Docker services..." -ForegroundColor Yellow
    docker compose -f "$root\docker-compose.yml" down
    exit 0
}

# 1. Docker (runs in current window, detached)
Write-Host "Starting Docker services..." -ForegroundColor Cyan
docker compose -f "$root\docker-compose.yml" up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker failed to start. Is Docker Desktop running?" -ForegroundColor Red
    exit 1
}

# 2. FastAPI
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root'; `$host.UI.RawUI.WindowTitle = 'TerraIQ - FastAPI'; .\venv\Scripts\Activate.ps1; uvicorn api.main:app --reload"
)

# 3. Celery worker
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root'; `$host.UI.RawUI.WindowTitle = 'TerraIQ - Celery'; .\venv\Scripts\Activate.ps1; celery -A api.workers.celery_app worker --loglevel=info"
)

# 4. Frontend dev server
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root\frontend'; `$host.UI.RawUI.WindowTitle = 'TerraIQ - Frontend'; npm run dev"
)

Write-Host ""
Write-Host "All services started." -ForegroundColor Green
Write-Host "  Frontend  -> http://localhost:5173" -ForegroundColor White
Write-Host "  API docs  -> http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Run '.\dev.ps1 -Stop' to stop Docker." -ForegroundColor DarkGray
