# Installation

This page covers local and Docker installation.

## Prerequisites

- macOS/Linux with shell access
- Python environment available at `.venv`
- Node.js and npm
- Docker + Docker Compose (for container mode)

## Local installation

1. Apply backend migrations:

```bash
make backend-migrate
```

2. Start backend:

```bash
make backend-run
```

3. In a second terminal, install and run frontend:

```bash
make frontend-install
make frontend-dev
```

4. Open:
- Frontend user UI: `http://localhost:5173/user`
- Frontend editor UI: `http://localhost:5173/editor`
- Backend API: `http://localhost:8000/api/v1`

## Docker installation

1. Start full stack:

```bash
make docker-dev-up
```

2. Open:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000/api/v1`
- GraphDB: `http://localhost:7200`

3. Stop stack:

```bash
make docker-dev-down
```

## Optional GraphDB bootstrap

```bash
make graphdb-bootstrap
```

Use this when you need GraphDB repository initialization plus ontology load and verification.
