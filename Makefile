# TerraIQ — developer shortcuts
# Windows: make uses PowerShell as its shell (no sh.exe dependency)

SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command

.PHONY: dev dev-local dev-docker stop up down backend worker frontend install migrate migration logs \
        test test-unit test-integration test-be test-fe test-e2e help

# ── Default ────────────────────────────────────────────────────────────────────
help:
	@Write-Host ''
	@Write-Host '  ── Dev ───────────────────────────────────────────────'
	@Write-Host '  make dev               Start full Docker dev stack (default)'
	@Write-Host '  make dev-docker        Start full Docker dev stack'
	@Write-Host '  make dev-local         Start local API/Celery/Frontend + Docker Postgres/Redis'
	@Write-Host '  make stop              Stop Docker services'
	@Write-Host '  make up                docker compose up -d'
	@Write-Host '  make down              docker compose down'
	@Write-Host '  make backend           Run FastAPI dev server'
	@Write-Host '  make worker            Run Celery worker'
	@Write-Host '  make frontend          Run Vite dev server'
	@Write-Host '  make install           Install all Python + Node dependencies'
	@Write-Host '  make migrate           Apply pending DB migrations'
	@Write-Host '  make migration msg=X   Generate migration from model changes'
	@Write-Host '  make logs              Tail Docker logs'
	@Write-Host ''
	@Write-Host '  ── Tests ─────────────────────────────────────────────'
	@Write-Host '  make test              Run all tests (backend + frontend)'
	@Write-Host '  make test-be           Run all backend tests (unit + integration)'
	@Write-Host '  make test-unit         Run backend unit tests only'
	@Write-Host '  make test-integration  Run backend integration tests only'
	@Write-Host '  make test-fe           Run frontend component tests (Vitest)'
	@Write-Host '  make test-e2e          Run E2E tests (requires: make dev first)'
	@Write-Host ''

# ── Dev entrypoints ───────────────────────────────────────────────────────────
dev:
	docker compose up -d
	Write-Host ''
	Write-Host 'Docker dev stack started.' -ForegroundColor Green
	Write-Host '  Frontend -> http://localhost:5173'
	Write-Host '  API docs -> http://localhost:8000/docs'
	Write-Host '  Postgres -> localhost:5432'
	Write-Host '  Redis    -> localhost:6379'

dev-docker:
	docker compose up -d
	Write-Host ''
	Write-Host 'Docker dev stack started.' -ForegroundColor Green
	Write-Host '  Frontend -> http://localhost:5173'
	Write-Host '  API docs -> http://localhost:8000/docs'
	Write-Host '  Postgres -> localhost:5432'
	Write-Host '  Redis    -> localhost:6379'

dev-local:
	docker compose up -d postgres redis
	Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$(CURDIR)'; $$host.UI.RawUI.WindowTitle='TerraIQ - FastAPI'; .\venv\Scripts\Activate.ps1; uvicorn api.main:app --reload"
	Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$(CURDIR)'; $$host.UI.RawUI.WindowTitle='TerraIQ - Celery'; .\venv\Scripts\Activate.ps1; celery -A api.workers.celery_app worker --loglevel=info"
	Start-Process powershell -ArgumentList '-NoExit','-Command',"Set-Location '$(CURDIR)\frontend'; $$host.UI.RawUI.WindowTitle='TerraIQ - Frontend'; npm run dev"
	Write-Host ''
	Write-Host 'All services started.' -ForegroundColor Green
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

# ── Individual services ───────────────────────────────────────────────────────
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

# ── Tests ─────────────────────────────────────────────────────────────────────

# All tests — backend (unit + integration) then frontend
test: test-be test-fe

# All backend tests
test-be:
	.\venv\Scripts\Activate.ps1; python -m pytest tests/ -v

# Unit tests only (no DB, no HTTP, no external services)
test-unit:
	.\venv\Scripts\Activate.ps1; python -m pytest tests/unit/ -v

# Integration tests only (SQLite + fakeredis + stubbed Celery)
test-integration:
	.\venv\Scripts\Activate.ps1; python -m pytest tests/integration/ -v

# Frontend component tests (Vitest + React Testing Library)
test-fe:
	Set-Location frontend; npm test

# E2E tests — requires all services running (make dev)
test-e2e:
	npx playwright test

# ── Setup ─────────────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt; pip install -e .; Set-Location frontend; npm install

