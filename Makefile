SHELL := /bin/bash

.PHONY: help diagrams-db diagrams-c4 slides-pdf slides-pptx openapi-validate backend-check backend-migrate backend-run backend-index frontend-install frontend-dev frontend-build frontend-test graphdb-up graphdb-down graphdb-logs graphdb-init graphdb-load graphdb-verify graphdb-bootstrap docker-dev-build docker-dev-up docker-dev-up-local-db docker-dev-up-graphdb docker-dev-up-external-postgres docker-dev-init-once docker-dev-down docker-dev-logs docker-dev-backup docker-dev-doctor docker-dev-safe-prune docker-dev-restore pre-commit-install pre-commit-run pre-commit-update shared-postgres-up shared-postgres-down shared-postgres-logs shared-postgres-bootstrap-app shared-postgres-audit up down status status-external health

## ─── Shortcut ────────────────────────────────────────────────────────────────
help: ## Show this help message
	@printf "\nUsage: make <target> [VAR=value ...]\n\n"
	@printf "%-38s %s\n" "Target" "Description"
	@printf "%-38s %s\n" "──────────────────────────────────" "───────────────────────────────────────────────"
	@grep -E '^##[[:space:]]' $(MAKEFILE_LIST) | sed 's/^## /\n/' ; \
	grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) \
		| sed 's/:.*## */\t/' \
		| sort \
		| awk -F'\t' '{ printf "  %-36s %s\n", $$1, $$2 }'
	@printf "\nRequired variables (where noted): REPO_URL, REPO_PATH, PROFILE, INCREMENTAL, BACKUP_ID\n"
	@printf "Optional toggles: CONTROLLER_LLM=1 enables local Qwen controller sidecar for docker-dev-up targets\n\n"

## ─── Diagrams & Slides ───────────────────────────────────────────────────────
diagrams-db: ## Render database ER diagram (PlantUML)
	@bash scripts/render-plantuml.sh db/database-er-diagram.puml

diagrams-c4: ## Render all C4 architecture diagrams (PlantUML)
	@bash scripts/render-plantuml.sh docs/architecture/c4-system-context.puml docs/architecture/c4-container.puml docs/architecture/c4-orchestrator-components.puml

slides-pdf: ## Build presentation slides as PDF (pandoc)
	@bash scripts/render-slides.sh pdf docs/presentation/napcore-helpdesk-presentation-pandoc.md dist/napcore-helpdesk-presentation.pdf

slides-pptx: ## Build presentation slides as PPTX (pandoc)
	@bash scripts/render-slides.sh pptx docs/presentation/napcore-helpdesk-presentation-pandoc-with-diagrams.md dist/napcore-helpdesk-presentation.pptx

## ─── API ─────────────────────────────────────────────────────────────────────
openapi-validate: ## Validate api/openapi.yaml against OpenAPI spec
	@bash scripts/validate-openapi.sh api/openapi.yaml

## ─── Backend ─────────────────────────────────────────────────────────────────
backend-check: ## Run Django system checks
	@cd backend && ../.venv/bin/python manage.py check

backend-migrate: ## Apply all pending database migrations
	@cd backend && ../.venv/bin/python manage.py migrate

backend-run: ## Start the Django development server
	@cd backend && ../.venv/bin/python manage.py runserver

backend-index: ## Index a source repository (REPO_URL, REPO_PATH required; PROFILE, INCREMENTAL optional)
	@test -n "$(REPO_URL)" || (echo "REPO_URL is required" && exit 1)
	@test -n "$(REPO_PATH)" || (echo "REPO_PATH is required" && exit 1)
	@cd backend && ../.venv/bin/python manage.py build_source_index --repo-url "$(REPO_URL)" --repo-path "$(REPO_PATH)" --profile "$${PROFILE:-netex}" $$( [ "$${INCREMENTAL:-0}" = "1" ] && echo "--incremental" ) --prune

## ─── Frontend ────────────────────────────────────────────────────────────────
frontend-install: ## Install frontend npm dependencies
	@cd frontend && npm install

frontend-dev: ## Start the Vite development server
	@cd frontend && npm run dev

frontend-build: ## Build the frontend for production
	@cd frontend && npm run build

frontend-test: ## Run frontend tests (vitest)
	@cd frontend && npm run test

## ─── GraphDB ─────────────────────────────────────────────────────────────────
graphdb-up: ## Start GraphDB container
	@docker-compose -f docker-compose.graphdb.yml up -d

graphdb-down: ## Stop GraphDB container
	@docker-compose -f docker-compose.graphdb.yml down

graphdb-logs: ## Stream GraphDB container logs
	@docker-compose -f docker-compose.graphdb.yml logs -f graphdb

graphdb-init: ## Initialise GraphDB repository (run once)
	@bash scripts/init-graphdb-repo.sh

graphdb-load: ## Load all ontology TTL files into GraphDB
	@cd backend && ../.venv/bin/python manage.py load_graphdb_ontologies --apply --replace --include-artifact-rules

graphdb-verify: ## Verify ontology state in GraphDB
	@bash scripts/verify-graphdb-ontology-state.sh

graphdb-bootstrap: graphdb-up graphdb-init graphdb-load graphdb-verify ## Full GraphDB setup: up + init + load + verify

## ─── Docker dev stack ────────────────────────────────────────────────────────
docker-dev-build: ## Build Docker dev images
	@docker compose -f docker-compose.dev.yml --profile local-db build

docker-dev-up: ## Start Docker dev stack (alias for docker-dev-up-local-db; set CONTROLLER_LLM=1 to enable Qwen controller)
	@$(MAKE) docker-dev-up-local-db

docker-dev-up-local-db: ## Start Docker dev stack with local PostgreSQL (set CONTROLLER_LLM=1 to include controller-llm)
	@CONTROLLER_LLM_ENABLED="$$( [ "$${CONTROLLER_LLM:-0}" = "1" ] && echo True || echo False )"; \
	CONTROLLER_PROFILE_ARGS="$$( [ "$${CONTROLLER_LLM:-0}" = "1" ] && echo "--profile controller-llm" )"; \
	echo "Starting dev stack (CONTROLLER_LLM=$${CONTROLLER_LLM:-0})"; \
	CONTROLLER_LLM_ENABLED="$$CONTROLLER_LLM_ENABLED" docker compose -f docker-compose.dev.yml --profile local-db $$CONTROLLER_PROFILE_ARGS up -d --build

docker-dev-up-graphdb: ## Start only the GraphDB service in the dev stack
	@docker compose -f docker-compose.dev.yml --profile local-db up -d --build graphdb

docker-dev-up-external-postgres: ## Start dev stack using external PostgreSQL (set CONTROLLER_LLM=1 to include controller-llm)
	@CONTROLLER_LLM_ENABLED="$$( [ "$${CONTROLLER_LLM:-0}" = "1" ] && echo True || echo False )"; \
	CONTROLLER_PROFILE_ARGS="$$( [ "$${CONTROLLER_LLM:-0}" = "1" ] && echo "--profile controller-llm" )"; \
	echo "Starting external-postgres stack (CONTROLLER_LLM=$${CONTROLLER_LLM:-0})"; \
	CONTROLLER_LLM_ENABLED="$$CONTROLLER_LLM_ENABLED" docker compose -f docker-compose.dev.yml -f docker-compose.external-postgres.yml $$CONTROLLER_PROFILE_ARGS up -d --build backend celery-worker celery-beat frontend redis graphdb $$( [ "$${CONTROLLER_LLM:-0}" = "1" ] && echo controller-llm )

docker-dev-init-once: ## Initialise GraphDB repo and load ontologies inside running containers
	@docker compose -f docker-compose.dev.yml --profile local-db exec -T backend bash /app/scripts/init-graphdb-repo.sh
	@docker compose -f docker-compose.dev.yml --profile local-db exec -T backend python manage.py load_graphdb_ontologies --apply --replace --include-artifact-rules --skip-checks

docker-dev-down: ## Stop and remove Docker dev stack containers
	@docker compose -f docker-compose.dev.yml --profile local-db down

docker-dev-logs: ## Stream Docker dev stack logs
	@docker compose -f docker-compose.dev.yml --profile local-db logs -f

docker-dev-backup: ## Backup dev data (PostgreSQL + uploads)
	@bash scripts/backup-dev-data.sh

docker-dev-doctor: ## Run health diagnostics on the dev stack
	@bash scripts/doctor-dev-mode.sh

docker-dev-safe-prune: ## Safely prune unused dev Docker volumes and images
	@bash scripts/safe-prune-dev.sh

docker-dev-restore: ## Restore dev data from backup (BACKUP_ID required)
	@bash scripts/restore-dev-data.sh $(BACKUP_ID)

## ─── Pre-commit ──────────────────────────────────────────────────────────────
pre-commit-install: ## Install pre-commit hooks into the local git repo
	@command -v pre-commit >/dev/null 2>&1 || { echo "pre-commit is not installed. Install with: pip install pre-commit"; exit 1; }
	@pre-commit install

pre-commit-run: ## Run all pre-commit hooks against all files
	@command -v pre-commit >/dev/null 2>&1 || { echo "pre-commit is not installed. Install with: pip install pre-commit"; exit 1; }
	@pre-commit run --all-files

pre-commit-update: ## Auto-update pre-commit hook revisions
	@command -v pre-commit >/dev/null 2>&1 || { echo "pre-commit is not installed. Install with: pip install pre-commit"; exit 1; }
	@pre-commit autoupdate

## ─── Shortcuts ──────────────────────────────────────────────────────────────
up: ## Start dev stack (alias for docker-dev-up)
	@$(MAKE) docker-dev-up

down: ## Stop dev stack (alias for docker-dev-down)
	@$(MAKE) docker-dev-down

status: ## Show running container status (local-db profile)
	@docker compose -f docker-compose.dev.yml --profile local-db ps

status-external: ## Show running container status (external-postgres profile)
	@docker compose -f docker-compose.dev.yml -f docker-compose.external-postgres.yml ps

health: ## Check liveness and readiness endpoints
	@curl -sS http://localhost:8000/api/v1/health/live && echo
	@curl -sS http://localhost:8000/api/v1/health/ready && echo

## ─── Shared PostgreSQL ──────────────────────────────────────────────────────
shared-postgres-up: ## Start shared PostgreSQL container
	@docker compose -f docker-compose.shared-postgres.yml up -d

shared-postgres-down: ## Stop shared PostgreSQL container
	@docker compose -f docker-compose.shared-postgres.yml down

shared-postgres-logs: ## Stream shared PostgreSQL logs
	@docker compose -f docker-compose.shared-postgres.yml logs -f

shared-postgres-bootstrap-app: ## Create app database and user in shared PostgreSQL (APP_DB, APP_USER, APP_PASSWORD)
	@APP_DB="$${APP_DB:-$${POSTGRES_DB:-napcore_helpdesk}}"; \
	APP_USER="$${APP_USER:-$${POSTGRES_USER:-napcore}}"; \
	APP_PASSWORD="$${APP_PASSWORD:-$${POSTGRES_PASSWORD:-napcore}}"; \
	ADMIN_USER="$${POSTGRES_USER:-napcore}"; \
	echo "Bootstrapping shared PostgreSQL app database/user: db=$${APP_DB} user=$${APP_USER}"; \
	docker compose -f docker-compose.shared-postgres.yml exec -T postgres \
		psql -v ON_ERROR_STOP=1 \
		-U "$$ADMIN_USER" \
		-d postgres \
		-v app_db="$$APP_DB" \
		-v app_user="$$APP_USER" \
		-v app_password="$$APP_PASSWORD" \
			-c "DO 'BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = ' || quote_literal(:'app_user') || ') THEN EXECUTE format(''CREATE ROLE %I LOGIN PASSWORD %L'', :'app_user', :'app_password'); ELSE EXECUTE format(''ALTER ROLE %I LOGIN PASSWORD %L'', :'app_user', :'app_password'); END IF; END';" \
			-c "DO 'BEGIN IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = ' || quote_literal(:'app_db') || ') THEN EXECUTE format(''CREATE DATABASE %I OWNER %I'', :'app_db', :'app_user'); END IF; END';" \
			-c "DO 'BEGIN EXECUTE format(''GRANT ALL PRIVILEGES ON DATABASE %I TO %I'', :'app_db', :'app_user'); END';"

shared-postgres-audit: ## List databases and login roles in shared PostgreSQL
	@ADMIN_USER="$${POSTGRES_USER:-napcore}"; \
	echo "Shared PostgreSQL databases:"; \
	docker compose -f docker-compose.shared-postgres.yml exec -T postgres \
		psql -U "$$ADMIN_USER" -d postgres \
		-c "SELECT datname AS database_name FROM pg_database WHERE datistemplate = false ORDER BY datname;"; \
	echo; \
	echo "Shared PostgreSQL login roles:"; \
	docker compose -f docker-compose.shared-postgres.yml exec -T postgres \
		psql -U "$$ADMIN_USER" -d postgres \
		-c "SELECT rolname AS role_name FROM pg_roles WHERE rolcanlogin = true ORDER BY rolname;"
