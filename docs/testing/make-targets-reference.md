# Make Targets Reference

Comprehensive guide to all NAPCORE Helpdesk Make targets organized by function.

## Quick Reference

| Target | Purpose | Parameters | Time |
|--------|---------|-----------|------|
| `make up` | Start dev environment (local DB) | - | ~30s |
| `make down` | Stop dev environment | - | ~5s |
| `make status` | Show container status | - | ~1s |
| `make health` | Check API health endpoints | - | ~2s |
| `make docker-dev-doctor` | Diagnose setup health | - | ~10s |

## Backend Targets

### Build & Migration
```bash
make backend-check          # Django system checks
make backend-migrate        # Apply database migrations
```

**When to use:**
- `backend-check`: Before deploying to verify configuration integrity
- `backend-migrate`: On first setup or after pulling new migrations

**Details:**
- `backend-check` runs Django's system check framework, validating installed apps, model constraints, and settings
- `backend-migrate` applies pending migrations to the PostgreSQL database

### Running Backend
```bash
make backend-run            # Start Django development server
```

**When to use:**
- During local development for direct backend testing
- Alternative to Docker-based backend (when testing local changes rapidly)
- Listens on `http://localhost:8000`

**Details:**
- Runs `manage.py runserver` in the `.venv` environment
- Requires `backend-migrate` to be run first
- Requires PostgreSQL running

### Indexing & Data
```bash
make backend-index REPO_URL=<url> REPO_PATH=<path> PROFILE=netex INCREMENTAL=1
```

**Parameters:**
- `REPO_URL`: GitHub repository URL (must be allow-listed in `ALLOWED_SOURCE_REPOSITORIES`)
- `REPO_PATH`: Absolute local path to cloned repository
- `PROFILE`: Index profile from `helpdesk/index_profiles/` (default: `netex`)
- `INCREMENTAL`: Set to `1` for incremental indexing (skips previously indexed files)

**When to use:**
- After cloning a new source repository for FAQ indexing
- When source repository content changes and needs re-indexing
- With `INCREMENTAL=1` for faster updates after minor content changes

**Example:**
```bash
make backend-index \
  REPO_URL=https://github.com/TransmodelEcosystem/NeTEx \
  REPO_PATH=/Users/you/repos/NeTEx \
  PROFILE=netex \
  INCREMENTAL=1
```

**Details:**
- Builds full-text + embedding search indices
- Supported file types: `.md`, `.txt`, `.yaml`, `.yml`, `.xml`, `.json`
- Profile rules filter paths and set chunk sizing
- With `--prune`: Removes chunks from repositories not in the allow-list
- Takes 30-60 minutes for large repositories like NeTEx

## Frontend Targets

### Setup & Development
```bash
make frontend-install       # Install npm dependencies
make frontend-dev           # Start Vite dev server
make frontend-build         # Build for production
make frontend-test          # Run tests
```

**When to use:**
- `frontend-install`: On first setup or after `package.json` changes
- `frontend-dev`: For local development (hot reload enabled)
- `frontend-build`: Before deployment or to validate production build
- `frontend-test`: Before commits to catch regressions

**Details:**
- `frontend-dev` uses Vite dev server with hot module replacement
- Listens on `http://localhost:5173`
- Proxies `/api/v1/*` to `http://localhost:8000/api/v1/*` to avoid CORS issues
- Routes: `/user` for chat, `/editor` for editorial console

## GraphDB Targets

### Standalone GraphDB (without Docker)
```bash
make graphdb-up             # Start GraphDB container
make graphdb-down           # Stop GraphDB container
make graphdb-logs           # Follow GraphDB logs
make graphdb-bootstrap      # Up + Init + Load + Verify (full setup)
```

**Individual steps:**
```bash
make graphdb-init           # Initialize ontology repository
make graphdb-load           # Load NAPCORE ontology + artifact rules
make graphdb-verify         # Verify ontology loaded correctly
```

**When to use:**
- If running GraphDB as a separate service (not in Docker Compose)
- `graphdb-bootstrap` for first-time setup (combines all 4 steps)
- `graphdb-logs` for troubleshooting query issues

**Details:**
- Requires `docker-compose.graphdb.yml` configuration
- GraphDB listens on `http://localhost:7200`
- Ontology stored in SPARQL repository `napcore-helpdesk`
- Repository: `https://github.com/NeTEx-CEN/napcore-its/ontologies/`

**Repository endpoint for queries:**
```
http://localhost:7200/repositories/napcore-helpdesk
```

## Docker Development Targets

### Startup Modes
```bash
make docker-dev-up              # Start with local PostgreSQL (default)
make docker-dev-up-local-db     # Explicit local DB mode
make docker-dev-up-external-postgres   # Use external PostgreSQL
```

**When to use:**
- `docker-dev-up`: Standard development (simplest)
- `docker-dev-up-external-postgres`: Multiple projects share one PostgreSQL instance

**Details:**
- `docker-dev-up-local-db` starts: backend, frontend, postgres, redis, graphdb, celery
- Builds images automatically with `--build`
- First startup takes 2-3 minutes, subsequent startups are faster

### Container Management
```bash
make docker-dev-build       # Rebuild all images
make docker-dev-up-graphdb  # Start only GraphDB container
make docker-dev-down        # Stop all containers
make docker-dev-logs        # Follow all container logs
```

**Details:**
- `docker-dev-build` rebuilds from `Dockerfile.dev` files
- `docker-dev-up-graphdb` useful for debugging only GraphDB issues
- `docker-dev-down` removes all containers (data persists in volumes)
- `docker-dev-logs` shows combined output from all services

### GraphDB & Django Init
```bash
make docker-dev-init-once   # Initialize GraphDB repo + load ontologies
```

**When to use:**
- After first `docker-dev-up` to populate GraphDB
- After major ontology changes (usually not needed after fresh start)

**Details:**
- Runs init script and Django management command inside backend container
- Creates `napcore-helpdesk` SPARQL repository
- Loads artifact rules and ontology mappings

## Backup & Restore Targets

See [backup-restore-workflow.md](backup-restore-workflow.md) for complete guide.

```bash
make docker-dev-backup      # Create timestamped backup
make docker-dev-restore     # Restore from backup (interactive)
make docker-dev-restore BACKUP_ID=<timestamp>  # Restore specific backup
make docker-dev-doctor      # Check health/mode/DB status
make docker-dev-safe-prune  # Backup + prune safely
```

**Details:**
- Backups stored in `.backups/{YYYYMMDD_HHMMSS}/`
- Includes PostgreSQL dumps and GraphDB configuration
- Safe-prune orchestrates: doctor → backup → prune → report

## Container Status Targets

```bash
make status                 # Show local-db containers
make status-external        # Show external-postgres containers
make health                 # Check API health endpoints
make docker-dev-doctor      # Extended health report with diagnostics
```

**Details:**
- `status`: Used with local PostgreSQL setup
- `status-external`: Used with shared external PostgreSQL
- `health`: Calls `/api/v1/health/live` and `/api/v1/health/ready`
- `docker-dev-doctor`: Reports DB mode, health checks, and recommendations

## Presentation Targets

```bash
make diagrams-db            # Render database ER diagram (PlantUML → PNG)
make diagrams-c4            # Render C4 architecture diagrams
make slides-pdf             # Build presentation as PDF
make slides-pptx            # Build presentation as PPTX
```

**When to use:**
- `diagrams-*`: Before updating architecture documentation
- `slides-pdf` / `slides-pptx`: Before presenting or sharing

**Dependencies:**
- PlantUML for diagrams (via `scripts/render-plantuml.sh`)
- Pandoc + LaTeX for PDF slides
- Pandoc for PPTX slides

**Details:**
- Diagrams output to `dist/`
- Slide sources in `docs/presentation/`
- See [docs/presentation/README.md](../presentation/README.md) for details

## API Validation Targets

```bash
make openapi-validate       # Validate OpenAPI schema
```

**When to use:**
- Before committing API changes
- To catch schema inconsistencies early

**Details:**
- Validates `api/openapi.yaml` against OpenAPI 3.0 spec
- Uses `swagger-cli` via `scripts/validate-openapi.sh`

## Pre-commit Targets

```bash
make pre-commit-install    # Install git pre-commit hook
make pre-commit-run        # Run all pre-commit checks on all files
make pre-commit-update     # Update pinned hook versions
```

**When to use:**
- `pre-commit-install`: Once per clone to activate automatic checks on commit
- `pre-commit-run`: Before opening a PR or after large refactors
- `pre-commit-update`: Periodically (for example monthly) to keep hook versions current

**Details:**
- Uses `.pre-commit-config.yaml` at repository root
- Runs core hygiene hooks (YAML/JSON/line endings/conflict markers)
- Runs backend Django checks + migration drift check
- Runs frontend build check

## Advanced: Shared PostgreSQL Targets

For multi-project development with isolated databases in one PostgreSQL instance:

```bash
make shared-postgres-up                 # Start shared PostgreSQL
make shared-postgres-down               # Stop shared PostgreSQL
make shared-postgres-logs               # Follow PostgreSQL logs
make shared-postgres-bootstrap-app      # Create app database/user
make shared-postgres-audit              # Show all databases and roles
```

**When to use:**
- Running multiple projects (NapcoreHelpdesk + DigitalTwin, etc.)
- To consolidate infrastructure and reduce resource usage

**Details:**
- Uses `docker-compose.shared-postgres.yml`
- Separate databases keep projects isolated
- `shared-postgres-bootstrap-app` creates database + user with full privileges
- Default database: `napcore_helpdesk`, user: `napcore`

**Create additional databases:**
```bash
make shared-postgres-bootstrap-app APP_DB=other_project APP_USER=other_user APP_PASSWORD=secret
```

## Workflow Examples

### First-time Local Setup
```bash
make backend-migrate        # Apply migrations
make backend-run            # Start backend (terminal 1)
make frontend-install       # Install frontend deps
make frontend-dev           # Start frontend (terminal 2)
# Open http://localhost:5173
```

### Docker-based Development
```bash
make docker-dev-up          # Start all containers
make docker-dev-init-once   # Initialize GraphDB
make health                 # Verify health
# Frontend at http://localhost:5173
# Backend at http://localhost:8000
```

### Index New Repository
```bash
make docker-dev-up          # Ensure containers running
make backend-index REPO_URL=https://github.com/TransmodelEcosystem/NeTEx \
                   REPO_PATH=/absolute/path/to/NeTEx \
                   PROFILE=netex \
                   INCREMENTAL=1
```

### Safe Cleanup with Backup
```bash
make docker-dev-safe-prune  # Backs up, prunes, reports disk saved
```

### Restore from Backup
```bash
make docker-dev-restore BACKUP_ID=20260426_120518
```

### Generate Presentation
```bash
make diagrams-c4            # Update architecture diagrams
make slides-pdf             # Generate PDF
# Output in dist/
```

## Troubleshooting

### Port Already in Use
```bash
# For backend (8000)
lsof -nP -iTCP:8000 -sTCP:LISTEN
pkill -f "manage.py runserver"

# For frontend (5173)
lsof -nP -iTCP:5173 -sTCP:LISTEN
pkill -f "vite"
```

### Database Connection Failed
```bash
make docker-dev-doctor      # Check database mode and health
make health                 # Verify API endpoints
psql postgresql://napcore:napcore@localhost:5432/napcore_helpdesk -c "SELECT 1;"
```

### GraphDB Not Responding
```bash
make graphdb-logs           # Check GraphDB container logs
make docker-dev-doctor      # General health check
curl http://localhost:7200/protocol  # Direct health check
```

### Lost Changes During Cleanup
```bash
make docker-dev-safe-prune  # Always use this, not manual prune
make docker-dev-restore BACKUP_ID=<timestamp>  # Restore if needed
```

## Related Documentation

- [Local Run Quickstart](local-run-quickstart.md) — Getting started
- [Backup & Restore Workflow](backup-restore-workflow.md) — Data protection
- [PostgreSQL + pgvector Runbook](../architecture/postgresql-pgvector-runbook.md) — Database operations
- [backend/README.md](../../backend/README.md) — Backend architecture
- [frontend/README.md](../../frontend/README.md) — Frontend features
- [docs/presentation/README.md](../presentation/README.md) — Presentation building
