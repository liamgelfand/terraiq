# TerraIQ — developer shortcuts
# Windows: make uses PowerShell as its shell (no sh.exe dependency)

SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command

.PHONY: dev stop up down backend worker frontend install logs help

# ── Default ────────────────────────────────────────────────────────────────────
help:
	@Write-Host ""
	@Write-Host "  make dev        Start all services (Docker + API + Celery + Frontend)"
	@Write-Host "  make stop       Stop Docker services"
	@Write-Host "  make up         docker compose up -d"
	@Write-Host "  make down       docker compose down"
	@Write-Host "  make backend    Run FastAPI dev server"
	@Write-Host "  make worker     Run Celery worker"
	@Write-Host "  make frontend   Run Vite dev server"
	@Write-Host "  make install    Install all Python + Node dependencies"
	@Write-Host "  make logs       Tail Docker logs"
	@Write-Host ""

# ── All-in-one ────────────────────────────────────────────────────────────────
dev:
	docker compose up -d; \
	Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$(CURDIR)'; $$host.UI.RawUI.WindowTitle='TerraIQ - FastAPI'; .\venv\Scripts\Activate.ps1; uvicorn api.main:app --reload"; \
	Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$(CURDIR)'; $$host.UI.RawUI.WindowTitle='TerraIQ - Celery'; .\venv\Scripts\Activate.ps1; celery -A api.workers.celery_app worker --loglevel=info"; \
	Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$(CURDIR)\frontend'; $$host.UI.RawUI.WindowTitle='TerraIQ - Frontend'; npm run dev"; \
	Write-Host ''; \
	Write-Host 'All services started.' -ForegroundColor Green; \
	Write-Host '  Frontend -> http://localhost:5173'; \
	Write-Host '  API docs -> http://localhost:8000/docs'

stop:
	docker compose down

# ── Docker ────────────────────────────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

# ── Individual services ───────────────────────────────────────────────────────
backend:
	.\venv\Scripts\Activate.ps1; uvicorn api.main:app --reload

worker:
	.\venv\Scripts\Activate.ps1; celery -A api.workers.celery_app worker --loglevel=info

frontend:
	Set-Location frontend; npm run dev

# ── Setup ─────────────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt; pip install -e .; Set-Location frontend; npm install

