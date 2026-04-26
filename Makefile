SHELL := /bin/bash

.PHONY: diagrams-db diagrams-c4 slides-pdf slides-pptx openapi-validate backend-check backend-migrate backend-run backend-index frontend-install frontend-dev frontend-build frontend-test graphdb-up graphdb-down graphdb-logs graphdb-init graphdb-load graphdb-verify graphdb-bootstrap docker-dev-build docker-dev-up docker-dev-up-local-db docker-dev-up-graphdb docker-dev-up-external-postgres docker-dev-init-once docker-dev-down docker-dev-logs docker-dev-backup docker-dev-doctor docker-dev-safe-prune docker-dev-restore pre-commit-install pre-commit-run pre-commit-update shared-postgres-up shared-postgres-down shared-postgres-logs shared-postgres-bootstrap-app shared-postgres-audit up down status status-external health

diagrams-db:
	@bash scripts/render-plantuml.sh db/database-er-diagram.puml

diagrams-c4:
	@bash scripts/render-plantuml.sh docs/architecture/c4-system-context.puml docs/architecture/c4-container.puml docs/architecture/c4-orchestrator-components.puml

slides-pdf:
	@bash scripts/render-slides.sh pdf docs/presentation/napcore-helpdesk-presentation-pandoc.md dist/napcore-helpdesk-presentation.pdf

slides-pptx:
	@bash scripts/render-slides.sh pptx docs/presentation/napcore-helpdesk-presentation-pandoc-with-diagrams.md dist/napcore-helpdesk-presentation.pptx

openapi-validate:
	@bash scripts/validate-openapi.sh api/openapi.yaml

backend-check:
	@cd backend && ../.venv/bin/python manage.py check

backend-migrate:
	@cd backend && ../.venv/bin/python manage.py migrate

backend-run:
	@cd backend && ../.venv/bin/python manage.py runserver

backend-index:
	@test -n "$(REPO_URL)" || (echo "REPO_URL is required" && exit 1)
	@test -n "$(REPO_PATH)" || (echo "REPO_PATH is required" && exit 1)
	@cd backend && ../.venv/bin/python manage.py build_source_index --repo-url "$(REPO_URL)" --repo-path "$(REPO_PATH)" --profile "$${PROFILE:-netex}" $$( [ "$${INCREMENTAL:-0}" = "1" ] && echo "--incremental" ) --prune

frontend-install:
	@cd frontend && npm install

frontend-dev:
	@cd frontend && npm run dev

frontend-build:
	@cd frontend && npm run build

frontend-test:
	@cd frontend && npm run test

graphdb-up:
	@docker-compose -f docker-compose.graphdb.yml up -d

graphdb-down:
	@docker-compose -f docker-compose.graphdb.yml down

graphdb-logs:
	@docker-compose -f docker-compose.graphdb.yml logs -f graphdb

graphdb-init:
	@bash scripts/init-graphdb-repo.sh

graphdb-load:
	@cd backend && ../.venv/bin/python manage.py load_graphdb_ontologies --apply --replace --include-artifact-rules

graphdb-verify:
	@bash scripts/verify-graphdb-ontology-state.sh

graphdb-bootstrap: graphdb-up graphdb-init graphdb-load graphdb-verify

docker-dev-build:
	@docker compose -f docker-compose.dev.yml --profile local-db build

docker-dev-up:
	@$(MAKE) docker-dev-up-local-db

docker-dev-up-local-db:
	@docker compose -f docker-compose.dev.yml --profile local-db up -d --build

docker-dev-up-graphdb:
	@docker compose -f docker-compose.dev.yml --profile local-db up -d --build graphdb

docker-dev-up-external-postgres:
	@docker compose -f docker-compose.dev.yml -f docker-compose.external-postgres.yml up -d --build backend celery-worker celery-beat frontend redis graphdb

docker-dev-init-once:
	@docker compose -f docker-compose.dev.yml --profile local-db exec -T backend bash /app/scripts/init-graphdb-repo.sh
	@docker compose -f docker-compose.dev.yml --profile local-db exec -T backend python manage.py load_graphdb_ontologies --apply --replace --include-artifact-rules --skip-checks

docker-dev-down:
	@docker compose -f docker-compose.dev.yml --profile local-db down

docker-dev-logs:
	@docker compose -f docker-compose.dev.yml --profile local-db logs -f

docker-dev-backup:
	@bash scripts/backup-dev-data.sh

docker-dev-doctor:
	@bash scripts/doctor-dev-mode.sh

docker-dev-safe-prune:
	@bash scripts/safe-prune-dev.sh

docker-dev-restore:
	@bash scripts/restore-dev-data.sh $(BACKUP_ID)

pre-commit-install:
	@command -v pre-commit >/dev/null 2>&1 || { echo "pre-commit is not installed. Install with: pip install pre-commit"; exit 1; }
	@pre-commit install

pre-commit-run:
	@command -v pre-commit >/dev/null 2>&1 || { echo "pre-commit is not installed. Install with: pip install pre-commit"; exit 1; }
	@pre-commit run --all-files

pre-commit-update:
	@command -v pre-commit >/dev/null 2>&1 || { echo "pre-commit is not installed. Install with: pip install pre-commit"; exit 1; }
	@pre-commit autoupdate

up:
	@$(MAKE) docker-dev-up

down:
	@$(MAKE) docker-dev-down

status:
	@docker compose -f docker-compose.dev.yml --profile local-db ps

status-external:
	@docker compose -f docker-compose.dev.yml -f docker-compose.external-postgres.yml ps

health:
	@curl -sS http://localhost:8000/api/v1/health/live && echo
	@curl -sS http://localhost:8000/api/v1/health/ready && echo

shared-postgres-up:
	@docker compose -f docker-compose.shared-postgres.yml up -d

shared-postgres-down:
	@docker compose -f docker-compose.shared-postgres.yml down

shared-postgres-logs:
	@docker compose -f docker-compose.shared-postgres.yml logs -f

shared-postgres-bootstrap-app:
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

shared-postgres-audit:
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
