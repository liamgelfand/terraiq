# TerraIQ — developer shortcuts
# Windows: make uses PowerShell as its shell (no sh.exe dependency)

SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command

.PHONY: dev dev-local stop up down backend worker frontend \
        install migrate migration logs simulate \
        test test-be test-unit test-integration test-fe test-e2e \
        help

# ── Default ────────────────────────────────────────────────────────────────────
help:
	@Write-Host ''
	@Write-Host '  ── Dev ───────────────────────────────────────────────────────────'
	@Write-Host '  make dev               Start full stack via Docker Compose'
	@Write-Host '  make dev-local         Docker (Postgres+Redis) + local API/Celery/Frontend'
	@Write-Host '  make stop              Stop and remove Docker containers'
	@Write-Host '  make backend           Run FastAPI dev server (local venv)'
	@Write-Host '  make worker            Run Celery worker (local venv)'
	@Write-Host '  make frontend          Run Vite dev server'
	@Write-Host '  make install           Install Python + Node dependencies'
	@Write-Host '  make migrate           Apply pending DB migrations'
	@Write-Host '  make migration msg=X   Generate a new migration from model changes'
	@Write-Host '  make simulate          Run single-route physics simulation (no API stack)'
	@Write-Host '  make logs              Tail Docker Compose logs'
	@Write-Host ''
	@Write-Host '  ── Tests ─────────────────────────────────────────────────────────'
	@Write-Host '  make test              Run all tests (backend + frontend)'
	@Write-Host '  make test-be           All backend tests (unit + integration)'
	@Write-Host '  make test-unit         Unit tests only — no I/O, runs in ~7s'
	@Write-Host '  make test-integration  Integration tests — SQLite + fakeredis'
	@Write-Host '  make test-fe           Frontend component tests (Vitest)'
	@Write-Host '  make test-e2e          E2E tests — requires: make dev first'
	@Write-Host ''

# ── Dev entrypoints ───────────────────────────────────────────────────────────

# Full Docker Compose stack (all services containerised)
dev:
	docker compose up -d
	Write-Host ''
	Write-Host '  All services started.' -ForegroundColor Green
	Write-Host '  Frontend -> http://localhost:5173'
	Write-Host '  API docs -> http://localhost:8000/docs'

# Docker for Postgres + Redis only; API/Celery/Frontend run locally in separate windows
dev-local:
	docker compose up -d postgres redis
	Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$(CURDIR)'; $$host.UI.RawUI.WindowTitle='TerraIQ - FastAPI'; .\venv\Scripts\Activate.ps1; uvicorn api.main:app --reload"
	Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$(CURDIR)'; $$host.UI.RawUI.WindowTitle='TerraIQ - Celery'; .\venv\Scripts\Activate.ps1; celery -A api.workers.celery_app worker --loglevel=info"
	Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$(CURDIR)\frontend'; $$host.UI.RawUI.WindowTitle='TerraIQ - Frontend'; npm run dev"
	Write-Host ''
	Write-Host '  Services started (3 new windows).' -ForegroundColor Green
	Write-Host '  Frontend -> http://localhost:5173'
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

# ── Individual services (for manual debugging) ────────────────────────────────
backend:
	.\venv\Scripts\Activate.ps1; uvicorn api.main:app --reload

worker:
	.\venv\Scripts\Activate.ps1; celery -A api.workers.celery_app worker --loglevel=info

frontend:
	Set-Location frontend; npm run dev

# ── Database ──────────────────────────────────────────────────────────────────
migrate:
	.\venv\Scripts\Activate.ps1; alembic upgrade head

migration:
	.\venv\Scripts\Activate.ps1; alembic revision --autogenerate -m "$(msg)"

# ── Scripts ───────────────────────────────────────────────────────────────────
simulate:
	.\venv\Scripts\Activate.ps1; python scripts/run_simulation.py

# ── Tests ─────────────────────────────────────────────────────────────────────

# All tests — backend first, then frontend
test: test-be test-fe

# All backend tests (unit + integration)
test-be:
	.\venv\Scripts\Activate.ps1; python -m pytest tests/ -v

# Unit tests only — pure functions, no DB or HTTP, runs in ~7s
test-unit:
	.\venv\Scripts\Activate.ps1; python -m pytest tests/unit/ -v

# Integration tests — SQLite in-memory + fakeredis + stubbed Celery
test-integration:
	.\venv\Scripts\Activate.ps1; python -m pytest tests/integration/ -v

# Frontend component tests (Vitest + React Testing Library)
test-fe:
	Set-Location frontend; npm test

# End-to-end tests via Playwright — requires all services running (make dev)
test-e2e:
	npx playwright test

# ── Setup ─────────────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt; pip install -e .; Set-Location frontend; npm install
