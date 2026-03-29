SHELL := /bin/bash

.PHONY: diagrams-db diagrams-c4 slides-pdf slides-pptx slides-odp openapi-validate backend-check backend-migrate backend-run backend-index frontend-install frontend-dev frontend-build frontend-test

diagrams-db:
	@bash scripts/render-plantuml.sh db/database-er-diagram.puml

diagrams-c4:
	@bash scripts/render-plantuml.sh docs/architecture/c4-system-context.puml docs/architecture/c4-container.puml docs/architecture/c4-orchestrator-components.puml

slides-pdf:
	@bash scripts/render-slides.sh pdf docs/presentation/napcore-helpdesk-presentation-pandoc.md dist/napcore-helpdesk-presentation.pdf

slides-pptx:
	@bash scripts/render-slides.sh pptx docs/presentation/napcore-helpdesk-presentation-pandoc-with-diagrams.md dist/napcore-helpdesk-presentation.pptx

slides-odp:
	@bash scripts/render-slides.sh odp docs/presentation/napcore-helpdesk-presentation-pandoc-with-diagrams.md dist/napcore-helpdesk-presentation.odp

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
