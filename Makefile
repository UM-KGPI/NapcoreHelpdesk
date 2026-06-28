SHELL := /bin/bash

.PHONY: help diagrams-c4 diagrams-erd diagrams-bpmn diagrams-sequence openapi-validate backend-check backend-migrate backend-run backend-run-controller-local backend-run-controller-local-all backend-llm-server-local backend-run-narration-server-local backend-run-full-local dev-up dev-down backend-index backend-controller-smoke-local frontend-install frontend-dev frontend-build frontend-test graphdb-up graphdb-down graphdb-logs graphdb-init graphdb-load graphdb-verify graphdb-bootstrap ontology-scan-examples ontology-alignment-gap docker-dev-build docker-dev-up docker-dev-up-local-db docker-dev-up-graphdb docker-dev-up-external-postgres docker-dev-init-once docker-dev-down docker-dev-logs docker-dev-backup docker-dev-doctor docker-dev-safe-prune docker-dev-restore pre-commit-install pre-commit-run pre-commit-update hooks-install version-print version-bump-patch version-bump-minor version-bump-major shared-postgres-up shared-postgres-down shared-postgres-logs shared-postgres-bootstrap-app shared-postgres-audit up down status status-external health

## ─── Shortcut ────────────────────────────────────────────────────────────────
help: ## Show this help message
	@printf "\nUsage: make <target> [VAR=value ...]\n\n"
	@printf "%-38s %s\n" "Target" "Description"
	@printf "%-38s %s\n" "──────────────────────────────────" "───────────────────────────────────────────────"
	@grep -E '^(##[[:space:]]|[a-zA-Z0-9_-]+:.*##)' $(MAKEFILE_LIST) \
		| sed -e 's/^## /\n/' \
		      -e 's/Makefile://g' \
		      -e 's/:[^#]*##[[:space:]]*/\t/' \
		| awk -F'\t' '{ if (NF==1) print $$1; else printf "  %-36s %s\n", $$1, $$2 }'
	@printf "\nRequired variables (where noted): REPO_URL, REPO_PATH, PROFILE, INCREMENTAL, BACKUP_ID\n"
	@printf "Start everything: make dev-up  |  Stop everything: make dev-down\n\n"

## ─── Diagrams ───────────────────────────────────────────────────────
diagrams-c4: ## Render all C4 architecture diagrams (PlantUML)
	@bash scripts/render-plantuml.sh .mylocal/docs/architecture/c4-system-context.puml .mylocal/docs/architecture/c4-container.puml .mylocal/docs/architecture/c4-orchestrator-components.puml

diagrams-erd: ## Render ERD architecture diagram (PlantUML -> SVG)
	@bash scripts/render-plantuml.sh docs/diagrams/erd-schema.puml

diagrams-bpmn: ## Render BPMN process diagrams (PlantUML -> SVG)
	@bash scripts/render-plantuml.sh .mylocal/docs/architecture/editor-review-process-bpmn.puml .mylocal/docs/architecture/question-answer-process-bpmn.puml

diagrams-sequence: ## Render sequence diagrams (PlantUML -> SVG)
	@bash scripts/render-plantuml.sh .mylocal/docs/architecture/editorial-workflow-sequence.puml .mylocal/docs/architecture/editorial-workflow-sequence-v2.puml

## ─── API ─────────────────────────────────────────────────────────────────────
openapi-validate: ## Validate api/openapi.yaml against OpenAPI spec
	@bash scripts/validate-openapi.sh api/openapi.yaml

## ─── All-in-one ──────────────────────────────────────────────────────────────
dev-up: ## Start the full Docker dev stack (single entrypoint)
	@echo "==> Starting full dev stack via docker-dev-up..."
	@$(MAKE) docker-dev-up
	@echo ""
	@echo "Services running:"
	@echo "  Backend API : http://localhost:8000/api/v1/"
	@echo "  Frontend    : http://localhost:5173"
	@echo "Stop with: make dev-down"

dev-down: ## Stop the full Docker dev stack (single entrypoint)
	@echo "==> Stopping full dev stack via docker-dev-down..."
	@$(MAKE) docker-dev-down
	@echo "Done."

## ─── Backend ─────────────────────────────────────────────────────────────────
backend-check: ## Run Django system checks
	@cd backend && ../.venv/bin/python manage.py check

backend-migrate: ## Apply all pending database migrations
	@cd backend && ../.venv/bin/python manage.py migrate

backend-run: ## Start the Django development server
	@cd backend && SERVICE_BUILD_REF="$$(../scripts/build_ref.sh)" ../.venv/bin/python manage.py runserver

backend-run-controller-local: ## Start local Django server with controller subprocess wired to local Qwen3-8B
	@cd backend && CONTROLLER_LLM_ENABLED=True CONTROLLER_LLM_PROVIDER=subprocess CONTROLLER_LLM_EXECUTABLE="$${CONTROLLER_LLM_EXECUTABLE:-/Users/andrejt/Research/repositories/git/llama.cpp/build/bin/llama-cli}" CONTROLLER_LLM_MODEL_PATH="$${CONTROLLER_LLM_MODEL_PATH:-/Users/andrejt/Research/repositories/git/llama.cpp/models/qwen3-8b/Qwen3-8B-Q4_K_M.gguf}" CONTROLLER_LLM_DEVICE="$${CONTROLLER_LLM_DEVICE:-none}" CONTROLLER_LLM_CTX_SIZE="$${CONTROLLER_LLM_CTX_SIZE:-1024}" CONTROLLER_LLM_MAX_TOKENS="$${CONTROLLER_LLM_MAX_TOKENS:-96}" CONTROLLER_LLM_THREADS="$${CONTROLLER_LLM_THREADS:-8}" CONTROLLER_LLM_TEMPERATURE="$${CONTROLLER_LLM_TEMPERATURE:-0.0}" CONTROLLER_LLM_TIMEOUT_SECONDS="$${CONTROLLER_LLM_TIMEOUT_SECONDS:-45}" ../.venv/bin/python manage.py runserver

backend-run-controller-local-all: ## Start local infra deps (db, redis, graphdb) then run local Django with controller subprocess
	@docker compose -f docker-compose.dev.yml --profile local-db up -d db redis graphdb
	@$(MAKE) backend-run-controller-local

backend-llm-server-local: ## Start llama-server with Qwen3-8B on port 8080 (chat UI at http://localhost:8080, OpenAI API at /v1)
	@"$${LLAMA_SERVER:-/Users/andrejt/Research/repositories/git/llama.cpp/build/bin/llama-server}" \
		-m "$${QWEN3_MODEL:-/Users/andrejt/Research/repositories/git/llama.cpp/models/qwen3-8b/Qwen3-8B-Q4_K_M.gguf}" \
		--host 127.0.0.1 --port 8080 \
		-c 8192 -t 8 --device none \
		-np 2

backend-run-narration-server-local: ## Start infra + llama-server + Django with narration via HTTP only (controller off; test narration first)
	@docker compose -f docker-compose.dev.yml --profile local-db up -d db redis graphdb
	@echo "Starting llama-server on port 8080..."
	@"$${LLAMA_SERVER:-/Users/andrejt/Research/repositories/git/llama.cpp/build/bin/llama-server}" \
		-m "$${QWEN3_MODEL:-/Users/andrejt/Research/repositories/git/llama.cpp/models/qwen3-8b/Qwen3-8B-Q4_K_M.gguf}" \
		--host 127.0.0.1 --port 8080 \
		-c 8192 -t 8 --device none \
		-np 2 &
	@echo "Waiting for llama-server to be ready..."
	@for i in $$(seq 1 60); do curl -sf http://127.0.0.1:8080/health > /dev/null 2>&1 && echo "llama-server ready" && break || ([ $$i -eq 60 ] && echo "ERROR: llama-server did not start in 60s" && exit 1) || sleep 2; done
	@cd backend && \
		CONTROLLER_LLM_ENABLED=False \
		LLM_ENABLED=True \
		LLM_PROVIDER=openai-compatible \
		LLM_API_BASE_URL=http://127.0.0.1:8080/v1 \
		LLM_MODEL=qwen3-8b \
		../.venv/bin/python manage.py runserver

backend-run-full-local: ## Start infra in Docker + llama-server on :8080 + Django with both LLMs via HTTP (full local stack)
	@docker compose -f docker-compose.dev.yml --profile local-db up -d db redis graphdb
	@echo "Starting llama-server on port 8080..."
	@"$${LLAMA_SERVER:-/Users/andrejt/Research/repositories/git/llama.cpp/build/bin/llama-server}" \
		-m "$${QWEN3_MODEL:-/Users/andrejt/Research/repositories/git/llama.cpp/models/qwen3-8b/Qwen3-8B-Q4_K_M.gguf}" \
		--host 127.0.0.1 --port 8080 \
		-c 8192 -t 8 --device none \
		-np 2 &
	@echo "Waiting for llama-server to be ready..."
	@for i in $$(seq 1 60); do curl -sf http://127.0.0.1:8080/health > /dev/null 2>&1 && echo "llama-server ready" && break || ([ $$i -eq 60 ] && echo "ERROR: llama-server did not start in 60s" && exit 1) || sleep 2; done
	@cd backend && \
		CONTROLLER_LLM_ENABLED=True \
		CONTROLLER_LLM_PROVIDER=openai-compatible \
		CONTROLLER_LLM_API_BASE_URL=http://127.0.0.1:8080/v1 \
		CONTROLLER_LLM_API_MODEL=qwen3-8b \
		LLM_ENABLED=True \
		LLM_PROVIDER=openai-compatible \
		LLM_API_BASE_URL=http://127.0.0.1:8080/v1 \
		LLM_MODEL=qwen3-8b \
		../.venv/bin/python manage.py runserver

backend-controller-smoke-local: ## Smoke-test local subprocess controller via host llama.cpp Qwen3-8B (outside Docker)
	@cd backend && CONTROLLER_LLM_ENABLED=True CONTROLLER_LLM_PROVIDER=subprocess CONTROLLER_LLM_EXECUTABLE="$${CONTROLLER_LLM_EXECUTABLE:-/Users/andrejt/Research/repositories/git/llama.cpp/build/bin/llama-cli}" CONTROLLER_LLM_MODEL_PATH="$${CONTROLLER_LLM_MODEL_PATH:-/Users/andrejt/Research/repositories/git/llama.cpp/models/qwen3-8b/Qwen3-8B-Q4_K_M.gguf}" CONTROLLER_LLM_DEVICE="$${CONTROLLER_LLM_DEVICE:-none}" CONTROLLER_LLM_CTX_SIZE="$${CONTROLLER_LLM_CTX_SIZE:-1024}" CONTROLLER_LLM_MAX_TOKENS="$${CONTROLLER_LLM_MAX_TOKENS:-96}" CONTROLLER_LLM_THREADS="$${CONTROLLER_LLM_THREADS:-8}" CONTROLLER_LLM_TEMPERATURE="$${CONTROLLER_LLM_TEMPERATURE:-0.0}" CONTROLLER_LLM_TIMEOUT_SECONDS="$${CONTROLLER_LLM_TIMEOUT_SECONDS:-45}" ../.venv/bin/python manage.py shell -c "from helpdesk.services.controller_llm import decide_route_with_controller_llm; q={'intent':'unknown','coreConcept':'nits:test','candidateStandards':['NeTEx']}; d=decide_route_with_controller_llm(question='How to map a new concept not in FAQ?', requested_scope=['NeTEx'], semantic_query=q); print('OK', d.route, d.intent, round(d.confidence,3))"

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
	@cd frontend && VITE_APP_VERSION="$$(../scripts/app_version.sh)" npm run build

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

ontology-scan-examples: ## Scan example XML dirs and write draft TTL stanzas for review (dry-run, never touches live files)
	@cd backend && ../.venv/bin/python manage.py scan_example_artifacts

ontology-alignment-gap: ## Report classes in standard ontologies with no NITS alignment entry
	@cd backend && ../.venv/bin/python manage.py ontology_alignment_gap

## ─── Docker dev stack ────────────────────────────────────────────────────────
docker-dev-build: ## Build Docker dev images
	@docker compose -f docker-compose.dev.yml --profile local-db build

docker-dev-up: ## Start Docker dev stack (alias for docker-dev-up-local-db; set CONTROLLER_LLM=1 to enable Qwen controller)
	@$(MAKE) docker-dev-up-local-db

docker-dev-up-local-db: ## Start Docker dev stack with local PostgreSQL (CONTROLLER_LLM=1, CONTROLLER_LLM_MODE=subprocess|server)
	@if [ -n "$${CONTROLLER_LLM+x}" ]; then \
		CONTROLLER_LLM_ENABLED="$$( [ "$$CONTROLLER_LLM" = "1" ] && echo True || echo False )"; \
		CONTROLLER_LLM_MODE="$${CONTROLLER_LLM_MODE:-subprocess}"; \
		CONTROLLER_LLM_PROVIDER="$$( [ "$$CONTROLLER_LLM_MODE" = "server" ] && echo openai-compatible || echo subprocess )"; \
		CONTROLLER_PROFILE_ARGS="$$( [ "$$CONTROLLER_LLM" = "1" ] && [ "$$CONTROLLER_LLM_MODE" = "server" ] && echo "--profile controller-llm" )"; \
		VITE_APP_VERSION="$$(bash scripts/app_version.sh)"; \
		echo "Starting dev stack (CONTROLLER_LLM=$$CONTROLLER_LLM, MODE=$$CONTROLLER_LLM_MODE)"; \
		VITE_APP_VERSION="$$VITE_APP_VERSION" CONTROLLER_LLM_ENABLED="$$CONTROLLER_LLM_ENABLED" CONTROLLER_LLM_PROVIDER="$$CONTROLLER_LLM_PROVIDER" docker compose -f docker-compose.dev.yml --profile local-db $$CONTROLLER_PROFILE_ARGS up -d --build; \
	else \
		VITE_APP_VERSION="$$(bash scripts/app_version.sh)"; \
		echo "Starting dev stack (using env/.env controller settings)"; \
		VITE_APP_VERSION="$$VITE_APP_VERSION" docker compose -f docker-compose.dev.yml --profile local-db up -d --build; \
	fi

docker-dev-up-graphdb: ## Start only the GraphDB service in the dev stack
	@docker compose -f docker-compose.dev.yml --profile local-db up -d --build graphdb

docker-dev-up-external-postgres: ## Start dev stack using external PostgreSQL (CONTROLLER_LLM=1, CONTROLLER_LLM_MODE=subprocess|server)
	@if [ -n "$${CONTROLLER_LLM+x}" ]; then \
		CONTROLLER_LLM_ENABLED="$$( [ "$$CONTROLLER_LLM" = "1" ] && echo True || echo False )"; \
		CONTROLLER_LLM_MODE="$${CONTROLLER_LLM_MODE:-subprocess}"; \
		CONTROLLER_LLM_PROVIDER="$$( [ "$$CONTROLLER_LLM_MODE" = "server" ] && echo openai-compatible || echo subprocess )"; \
		CONTROLLER_PROFILE_ARGS="$$( [ "$$CONTROLLER_LLM" = "1" ] && [ "$$CONTROLLER_LLM_MODE" = "server" ] && echo "--profile controller-llm" )"; \
		VITE_APP_VERSION="$$(bash scripts/app_version.sh)"; \
		echo "Starting external-postgres stack (CONTROLLER_LLM=$$CONTROLLER_LLM, MODE=$$CONTROLLER_LLM_MODE)"; \
		VITE_APP_VERSION="$$VITE_APP_VERSION" CONTROLLER_LLM_ENABLED="$$CONTROLLER_LLM_ENABLED" CONTROLLER_LLM_PROVIDER="$$CONTROLLER_LLM_PROVIDER" docker compose -f docker-compose.dev.yml -f docker-compose.external-postgres.yml $$CONTROLLER_PROFILE_ARGS up -d --build backend celery-worker celery-beat frontend redis graphdb $$( [ "$$CONTROLLER_LLM" = "1" ] && [ "$$CONTROLLER_LLM_MODE" = "server" ] && echo controller-llm ); \
	else \
		VITE_APP_VERSION="$$(bash scripts/app_version.sh)"; \
		echo "Starting external-postgres stack (using env/.env controller settings)"; \
		VITE_APP_VERSION="$$VITE_APP_VERSION" docker compose -f docker-compose.dev.yml -f docker-compose.external-postgres.yml up -d --build backend celery-worker celery-beat frontend redis graphdb; \
	fi

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

hooks-install: ## Enable repository-local git hooks (.githooks)
	@git config core.hooksPath .githooks
	@chmod +x .githooks/pre-commit scripts/bump_version.sh scripts/build_ref.sh scripts/app_version.sh
	@echo "Git hooks enabled from .githooks"

version-print: ## Print repo version and computed app version
	@echo "VERSION=$$(cat VERSION)"
	@echo "APP_VERSION=$$(bash scripts/app_version.sh)"
	@echo "BUILD_REF=$$(bash scripts/build_ref.sh)"

version-bump-patch: ## Bump VERSION patch component (x.y.z -> x.y.z+1)
	@bash scripts/bump_version.sh patch

version-bump-minor: ## Bump VERSION minor component (x.y.z -> x.y+1.0)
	@bash scripts/bump_version.sh minor

version-bump-major: ## Bump VERSION major component (x.y.z -> x+1.0.0)
	@bash scripts/bump_version.sh major

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
