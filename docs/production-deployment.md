# Production Deployment Guide

Target: Docker Compose on a Fedora Linux VM, deployed via GitHub Actions over SSH.

## Table of contents

1. [Prerequisites](#1-prerequisites)
2. [Server bootstrap](#2-server-bootstrap)
3. [Environment configuration](#3-environment-configuration)
4. [Place local-only assets on the server](#4-place-local-only-assets-on-the-server)
5. [GitHub Actions secrets](#5-github-actions-secrets)
6. [First deployment](#6-first-deployment)
7. [Populate the knowledge base](#7-populate-the-knowledge-base)
8. [Verify the deployment](#8-verify-the-deployment)
9. [Subsequent deployments](#9-subsequent-deployments)
10. [Data migration from dev](#10-data-migration-from-dev)
11. [Operational notes](#11-operational-notes)

---

## 1. Prerequisites

**VM requirements (minimum):**

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 4 vCPUs | 8 vCPUs |
| RAM | 10 GB | 16 GB |
| Disk | 40 GB | 80 GB |
| OS | Fedora 39+ | Fedora 41 |

GraphDB holds the largest memory footprint (4–6 GB heap). The backend + Celery workers
need another 3–5 GB. Size accordingly.

**Required locally before you begin:**

- SSH access to the VM
- The GraphDB license file (`secrets/graphdb.license` in the repo root)
- The ontology TTL files from `.mylocal/docs/ontology/`
- A GitHub personal access token or deploy key with read access to the repo

---

## 2. Server bootstrap

Run these commands on the Fedora VM over SSH. This is a one-time setup.

### 2.1 Install Docker

```bash
sudo dnf -y install dnf-plugins-core
sudo dnf-3 config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable --now docker
```

Add your deploy user to the docker group so it can run `docker` without sudo:

```bash
sudo usermod -aG docker $USER
# Log out and back in for the group change to take effect
```

### 2.2 Create the deployment directory layout

```bash
sudo mkdir -p /opt/napcore-helpdesk/ontology
sudo mkdir -p /opt/napcore-helpdesk/secrets

# Give ownership to the deploy user
sudo chown -R $USER:$USER /opt/napcore-helpdesk
```

### 2.3 Clone the repository

```bash
cd /opt/napcore-helpdesk
git clone https://github.com/UM-KGPI/NapcoreHelpdesk.git .
```

If the repository is private, use a GitHub deploy key:

```bash
# Generate a key pair (no passphrase)
ssh-keygen -t ed25519 -C "deploy@napcore-vm" -f ~/.ssh/napcore_deploy -N ""

# Add the public key as a deploy key in GitHub:
# Repository → Settings → Deploy keys → Add deploy key (read-only is sufficient)
cat ~/.ssh/napcore_deploy.pub

# Clone using the deploy key
GIT_SSH_COMMAND="ssh -i ~/.ssh/napcore_deploy" \
  git clone git@github.com:UM-KGPI/NapcoreHelpdesk.git /opt/napcore-helpdesk

# Persist the key for future pulls
git -C /opt/napcore-helpdesk config core.sshCommand "ssh -i ~/.ssh/napcore_deploy"
```

### 2.4 Place the deploy script

The GitHub Actions workflow SSHs in and runs `scripts/deploy.sh`. Make it executable:

```bash
chmod +x /opt/napcore-helpdesk/scripts/deploy.sh
```

---

## 3. Environment configuration

Copy the example env file and fill in production values:

```bash
cp /opt/napcore-helpdesk/backend/.env.example /opt/napcore-helpdesk/backend/.env.prod
```

Edit `/opt/napcore-helpdesk/backend/.env.prod`. Required changes:

```bash
# --- Required ---
DJANGO_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(50))">
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=<your-server-ip-or-domain>

JWT_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">

POSTGRES_DB=napcore_helpdesk
POSTGRES_USER=napcore
POSTGRES_PASSWORD=<strong-random-password>
# POSTGRES_HOST and PORT are set in docker-compose.prod.yml; leave them out of .env.prod

# --- Recommended ---
GITHUB_API_TOKEN=<token with public_repo read scope — needed for indexing>

# --- Enable features you want in production ---
LLM_ENABLED=True
LLM_API_KEY=<your-llm-api-key>
LLM_API_BASE_URL=https://models.inference.ai.azure.com
LLM_MODEL=gpt-4o-mini

GRAPHDB_ENABLED=True
GRAPH_RAG_ENABLED=True

# --- Leave these disabled in production ---
DEV_JWT_AUTO_ISSUE=False
```

Protect the file:

```bash
chmod 600 /opt/napcore-helpdesk/backend/.env.prod
```

---

## 4. Place local-only assets on the server

These files are gitignored and must be copied from your local machine.

### 4.1 Ontology TTL files

```bash
# Run on your Mac
rsync -av --progress \
  .mylocal/docs/ontology/ \
  user@your-vm:/opt/napcore-helpdesk/ontology/
```

### 4.2 GraphDB license

```bash
# Run on your Mac
scp secrets/graphdb.license \
  user@your-vm:/opt/napcore-helpdesk/secrets/graphdb.license
```

Verify on the server:

```bash
ls -lh /opt/napcore-helpdesk/ontology/
ls -lh /opt/napcore-helpdesk/secrets/graphdb.license
```

---

## 5. GitHub Actions secrets

The deploy workflow authenticates over SSH. Add these three secrets in GitHub:

**Repository → Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `PROD_HOST` | VM IP address or hostname |
| `PROD_USER` | SSH user on the VM (e.g. `fedora` or your username) |
| `PROD_SSH_KEY` | Contents of the **private** SSH key used to reach the VM |

Generate a dedicated deploy key pair if you don't already have one:

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/napcore_actions -N ""

# Add the public key to the VM
ssh-copy-id -i ~/.ssh/napcore_actions.pub user@your-vm

# Paste the private key contents into the PROD_SSH_KEY GitHub secret
cat ~/.ssh/napcore_actions
```

---

## 6. First deployment

The first deploy must be done manually from the server because the production images
have not been built yet and GitHub Actions cannot verify the host key.

```bash
# On the server
cd /opt/napcore-helpdesk

docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Watch startup logs
docker compose -f docker-compose.prod.yml logs -f --tail=50
```

Wait for all services to reach a healthy state:

```bash
docker compose -f docker-compose.prod.yml ps
```

Expected status:

```
NAME              STATUS
db                healthy
redis             healthy
graphdb           healthy
backend           healthy
celery-worker     running
celery-beat       running
frontend          running
```

---

## 7. Populate the knowledge base

The database schema is created automatically by migrations (run inside `deploy.sh`
and also baked into the backend startup command). The actual knowledge — indexed
repository chunks and ontology graphs — must be loaded separately.

### 7.1 Bootstrap GraphDB

Create the GraphDB repository and load the ontology graphs:

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py init_graphdb_repository

docker compose -f docker-compose.prod.yml exec backend \
  python manage.py load_ontology_graphs
```

Verify in the GraphDB UI at `http://your-vm:7200` (only accessible if you open port
7200 in your firewall; otherwise use SSH port forwarding:
`ssh -L 7200:localhost:7200 user@your-vm`).

### 7.2 Index source repositories

Index pulls directly from GitHub. Requires `GITHUB_API_TOKEN` in `.env.prod`.

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python manage.py index_repository \
    --repo-url https://github.com/TransmodelEcosystem/NeTEx \
    --profile netex

docker compose -f docker-compose.prod.yml exec backend \
  python manage.py index_repository \
    --repo-url https://github.com/OpRa-CEN/OpRa \
    --profile opra

docker compose -f docker-compose.prod.yml exec backend \
  python manage.py index_repository \
    --repo-url https://github.com/SIRI-CEN/SIRI \
    --profile default
```

Indexing can take several minutes per repository. Monitor progress:

```bash
docker compose -f docker-compose.prod.yml logs -f celery-worker
```

---

## 8. Verify the deployment

```bash
# Liveness (should return 200)
curl -s http://your-vm/api/v1/health/live

# Readiness (returns 200 when DB + GraphDB are reachable)
curl -s http://your-vm/api/v1/health/ready

# Ask a question to confirm the full RAG pipeline
curl -s -X POST http://your-vm/api/v1/questions/answer \
  -H "Content-Type: application/json" \
  -d '{"question": "What is a NeTEx ServiceJourney?"}' | python3 -m json.tool
```

Open `http://your-vm` in a browser to verify the frontend loads.

---

## 9. Subsequent deployments

After the first manual deploy, all future deployments go through GitHub Actions:

1. Push a commit to `main` (or merge a PR)
2. Go to **Actions → Deploy to Production → Run workflow**
3. Type `deploy` in the confirmation field and click **Run workflow**

The workflow re-runs the full CI suite first, then SSHs into the server and executes
`scripts/deploy.sh`, which:

- Pulls the latest code (`git pull origin main`)
- Rebuilds changed images (`docker compose build --pull`)
- Restarts services with zero downtime where possible (`up -d --remove-orphans`)
- Runs pending database migrations (`manage.py migrate --noinput`)
- Prunes dangling images

---

## 10. Data migration from dev

If you want to transfer indexed chunks from your local dev database instead of
re-indexing from scratch, use a dump/restore.

### Export from local dev

```bash
# On your Mac — dump from the running dev stack
docker compose -f docker-compose.dev.yml exec db \
  pg_dump -U napcore napcore_helpdesk | gzip > napcore_helpdesk.dump.gz

# Transfer to server
scp napcore_helpdesk.dump.gz user@your-vm:/opt/napcore-helpdesk/
```

### Import into production

```bash
# On the server — production stack must be running
gunzip -c /opt/napcore-helpdesk/napcore_helpdesk.dump.gz | \
  docker compose -f docker-compose.prod.yml exec -T db \
  psql -U napcore napcore_helpdesk

# Clean up
rm /opt/napcore-helpdesk/napcore_helpdesk.dump.gz
```

> **Note:** Do not import your dev database if it contains dev-only users or tokens
> with `DEV_JWT_AUTO_ISSUE=True`. Review the data before importing.

---

## 11. Operational notes

### Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend
```

### Restart a service

```bash
docker compose -f docker-compose.prod.yml restart backend
```

### Database backup

```bash
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U napcore napcore_helpdesk | gzip \
  > /opt/napcore-helpdesk/backups/napcore_$(date +%Y%m%d_%H%M%S).dump.gz
```

Add this to a cron job for automated daily backups:

```bash
crontab -e
# Add:
0 3 * * * docker compose -f /opt/napcore-helpdesk/docker-compose.prod.yml exec -T db pg_dump -U napcore napcore_helpdesk | gzip > /opt/napcore-helpdesk/backups/napcore_$(date +\%Y\%m\%d).dump.gz
```

### Update environment variables

Edit `/opt/napcore-helpdesk/backend/.env.prod`, then restart the affected services:

```bash
docker compose -f docker-compose.prod.yml up -d backend celery-worker celery-beat
```

### Firewall

Open only the ports needed for public access:

```bash
sudo firewall-cmd --permanent --add-service=http    # port 80
sudo firewall-cmd --permanent --add-service=https   # port 443 (when you add TLS)
sudo firewall-cmd --reload

# GraphDB admin UI — only open if needed; prefer SSH port-forwarding
# sudo firewall-cmd --permanent --add-port=7200/tcp
```

### TLS / HTTPS

The current setup serves HTTP on port 80. For production with a domain name, place
a reverse proxy (Caddy or Nginx) in front of the frontend container and terminate
TLS there. Caddy with automatic Let's Encrypt is the simplest option:

```yaml
# Add to docker-compose.prod.yml
  caddy:
    image: caddy:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
```

```
# Caddyfile
your-domain.example.com {
    reverse_proxy frontend:80
}
```
