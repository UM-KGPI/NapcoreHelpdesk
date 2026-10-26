# Production Deployment Guide

Target: Docker Compose on a Fedora Linux VM, deployed via GitHub Actions on a self-hosted runner on the VM.

## Table of contents

1. [Prerequisites](#1-prerequisites)
2. [Server bootstrap](#2-server-bootstrap)
3. [Environment configuration](#3-environment-configuration)
4. [Place local-only assets on the server](#4-place-local-only-assets-on-the-server)
5. [GitHub Actions runner](#5-github-actions-runner)
6. [First deployment](#6-first-deployment)
7. [Populate the knowledge base](#7-populate-the-knowledge-base)
8. [Verify the deployment](#8-verify-the-deployment)
9. [Subsequent deployments](#9-subsequent-deployments)
10. [Data migration from dev](#10-data-migration-from-dev)
11. [Operational notes](#11-operational-notes)
12. [Rolling out an update to the knowledge base](#12-rolling-out-an-update-to-the-knowledge-base)

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

The GitHub Actions workflow runs `scripts/deploy.sh` on the server through the self-hosted runner (section 5). Make it executable:

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

# --- Keep this enabled until real authentication exists ---
DEV_JWT_AUTO_ISSUE=True
```

`DEV_JWT_AUTO_ISSUE=True` is how browsers get their token today: `POST /auth/dev-token` is the only way to
obtain a JWT, and every visitor receives the same generic identity. The name suggests a development
setting, but turning it off locks out every user whose browser has no cached token, and the Send button
stays disabled with no error shown. Switch it off only after a scoped authentication system replaces it.

Protect the file:

```bash
chmod 600 /opt/napcore-helpdesk/backend/.env.prod
```

---

## 4. Place local-only assets on the server

These files are gitignored and must be copied from your local machine. Only the GraphDB license is
still local-only.

### 4.1 Ontology TTL files

Nothing to copy. The ontology files are committed under `docs/ontology/` and reach the server with the
repository: `docker-compose.prod.yml` mounts `./docs` into the backend and Celery containers, so a deploy
(`git pull`) also updates the files that `load_graphdb_ontologies` reads. The OpRa, SIRI and NeTEx
files are generated from the upstream repositories (`docs/ontology/GENERATION.md`) and reviewed
through GitHub.

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

## 5. GitHub Actions runner

GitHub-hosted runners cannot reach the server over SSH, so the **Deploy to Production**
workflow runs on a self-hosted runner installed on the server itself. It needs no SSH key and no
deployment secrets in GitHub.

### 5.1 Register the runner (once)

1. In GitHub open **Repository → Settings → Actions → Runners → New self-hosted runner**
   and choose Linux x64. That page shows the download commands for the current runner release,
   with its checksum, and a registration token. Use those commands; do not copy version numbers
   from this guide.
2. On the server, as the user that owns `/opt/napcore-helpdesk` and belongs to the `docker` group
   (the runner uses that user's home, and so its deploy key for `git pull`):

```bash
mkdir -p ~/actions-runner && cd ~/actions-runner
# download, verify the checksum and extract, exactly as shown on the GitHub page

./config.sh --url https://github.com/UM-KGPI/NapcoreHelpdesk \
            --token <registration token from the GitHub page> \
            --labels napcore-prod --unattended

sudo ./svc.sh install "$USER"
sudo ./svc.sh start
sudo ./svc.sh status
```

The registration token is shown only on that page and expires after an hour. Never commit it
or paste it into a chat. The runner then appears under **Settings → Actions → Runners** as
**Idle** with the label `napcore-prod`.

### 5.2 Rules for the runner

- Only the deploy job uses `runs-on: [self-hosted, napcore-prod]`. Never use that label in a
  workflow that pull requests can start: the workflow code would run on the production host.
- The deploy workflow starts only by hand (`workflow_dispatch`) and only with the word `deploy`.
- The runner user has access to Docker, which is equivalent to root on the server. Keep the
  repository private and the list of people who can run workflows short.
- If the runner is offline, a started deployment waits in the queue. Check
  **Settings → Actions → Runners**, or on the server `sudo ./svc.sh status` in `~/actions-runner`.
- To remove the runner: `sudo ./svc.sh stop && sudo ./svc.sh uninstall`, then
  `./config.sh remove --token <removal token from the GitHub page>`.

### 5.3 Old SSH secrets

`PROD_HOST`, `PROD_USER` and `PROD_SSH_KEY` are no longer used by any workflow. After the
first successful deployment through the runner, delete them under **Settings → Secrets and
variables → Actions**, and remove the dedicated Actions key from the server's
`~/.ssh/authorized_keys`.

---

## 6. First deployment

The first deploy must be done manually from the server because the production images
have not been built yet and the runner (section 5) is not registered yet.

```bash
# On the server
cd /opt/napcore-helpdesk

# Without these variables, the frontend build falls back to a hardcoded default
# version and the backend reports build reference "dev".
. scripts/build_env.sh
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

The ontology graphs go into a GraphDB repository named `napcore-helpdesk`
(`GRAPHDB_REPOSITORY` in `docker-compose.prod.yml`). **Nothing in this repository creates that
repository, and its configuration (type and ruleset) is not recorded here.** On a new server, create
it in the GraphDB Workbench (Setup, Repositories) with the same settings as the existing production
repository, read from its Workbench page before you build the new one.

Then load the ontology graphs. The command is a dry run until `--apply` is given:

```bash
docker compose -f docker-compose.prod.yml exec -T backend \
  python manage.py load_graphdb_ontologies            # prints the plan only

docker compose -f docker-compose.prod.yml exec -T -e GRAPHDB_TIMEOUT_SECONDS=1800 backend \
  python manage.py load_graphdb_ontologies --apply --replace
```

The long timeout is for this command only: the compose default of 30 seconds is meant for answering
questions, not for replacing a large graph. Do not add `--include-artifact-rules` unless the
artifact-rule graphs are meant to be active.

Verify in the GraphDB UI at `http://your-vm:7200` (only accessible if you open port
7200 in your firewall; otherwise use SSH port forwarding:
`ssh -L 7200:localhost:7200 user@your-vm`), or with the count query in section 12.

### 7.2 Index source repositories

One command fetches the three repositories (NeTEx, SIRI, OpRa) into the `source-repos` volume
and indexes each with its own profile (`netex`, `siri`, `opra`). The repositories are public,
so no token is needed. The first time, index everything (`--full`) so every chunk records the
real commit SHA:

```bash
docker compose -f docker-compose.prod.yml exec -T celery-worker \
  python manage.py refresh_source_indexes --full
```

Each repository prints one line (`ok`, the commit, the number of files scanned and chunks
created, updated and deleted, and `alias_removed`: chunks deleted because they were stored under
another spelling of the same repository) or `FAILED` with the reason; the command exits with an error if any
repository failed. `--only SIRI` refreshes one repository. Indexing can take several minutes
(NeTEx is the largest). Follow it in another terminal:

```bash
docker compose -f docker-compose.prod.yml logs -f celery-worker
```

### 7.3 Daily refresh

The same refresh can run every day. It is off until you switch it on, in `.env.prod`:

```
SOURCE_REFRESH_ENABLED=True
# Optional, UTC. Defaults: 3 and 30.
SOURCE_REFRESH_HOUR=3
SOURCE_REFRESH_MINUTE=30
```

Then recreate the scheduler so it reads the setting:
`docker compose -f docker-compose.prod.yml up -d --force-recreate celery-beat`.

What it does each day: for every repository, fetch the remote default branch (a shallow
clone under `/app/repos`), then index only the changed files and remove the chunks of deleted
files (`incremental` with `prune`). A repository that fails does not stop the others, and the task
then fails, so the problem shows in the worker log. Check the last run:

```bash
docker compose -f docker-compose.prod.yml logs celery-worker | grep "Source refresh"
```

Things to know:
- It follows the repositories' default branches, so the knowledge base changes when upstream
  does. The CI benchmark pins its own commits and is not affected.
- The first scheduled run after a long gap can delete and create many chunks; run the command
  from 7.2 by hand once and read its counts before enabling the schedule.
- It does not touch GraphDB. The ontology files under `docs/ontology` are generated and
  reviewed through GitHub, then loaded with `load_graphdb_ontologies`.
- A refresh that starts while another is running is skipped.
- To switch it off set `SOURCE_REFRESH_ENABLED=False` and recreate `celery-beat`.

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

The workflow re-runs the full CI suite first, then the self-hosted runner on the server
executes `scripts/deploy.sh`, which:

- Pulls the latest code (`git pull origin main`) and then re-runs itself from the pulled copy, so a change to `deploy.sh` applies to the same deployment
- Rebuilds changed images (`docker compose build --pull`); the site keeps running meanwhile
- Switches on the maintenance page (creates `maintenance/on`, see "Maintenance page" in section 11)
- Restarts the services (`up -d --remove-orphans`). The backend container applies migrations before it starts serving
- Waits until `/api/v1/health/ready` answers (the backend can reach its database), then confirms migrations (`manage.py migrate --noinput`)
- Switches the maintenance page off again. This also happens if the deploy fails or is cancelled, so the site is never left in maintenance
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

### Running `docker compose` by hand

`scripts/deploy.sh` sets the version variables before it builds and starts the services. When you
run `docker compose ... build` or `up` yourself, set them first, from the repository root:

```bash
. scripts/build_env.sh
docker compose -f docker-compose.prod.yml up -d
```

Without them the services are recreated with defaults: the backend reports build reference
`dev`, and the frontend falls back to its hardcoded version when it is rebuilt.
`docker compose restart` does not recreate containers and does not need them.

### Maintenance page

The frontend's nginx shows a maintenance page while the file `/opt/napcore-helpdesk/maintenance/on`
exists. Browsers get a short HTML page that reloads itself; API calls get HTTP 503 with a JSON error
(`SERVICE_UNAVAILABLE`) and `Retry-After: 30`, which the web app shows as a message. nginx checks the
file on every request, so no restart is needed. `deploy.sh` switches it on and off; for planned
maintenance do it by hand:

```bash
touch /opt/napcore-helpdesk/maintenance/on   # on
rm /opt/napcore-helpdesk/maintenance/on      # off
```

The same API response also appears, without the file, whenever the backend cannot be reached (for
example while its container restarts). Errors returned by the backend itself are passed through
unchanged. Two limits: the page is served by the frontend container, so while that container is
being recreated the proxy in front of it answers instead; and the directory must stay readable by
others (the default for a cloned repository), or nginx cannot see the file.

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

---

## 12. Rolling out an update to the knowledge base

Use this order after a deploy that changes the ontology files, the indexing, or the answer logic.
Stop at the first check that fails. Run from `/opt/napcore-helpdesk`; every stage assumes:

```bash
cd /opt/napcore-helpdesk
C="docker compose -f docker-compose.prod.yml"
```

### 12.0 Before changing anything (read-only)

```bash
git rev-parse --short HEAD
$C ps
$C exec -T backend curl -s http://localhost:8000/api/v1/health/ready

# triples per graph (save the output; compare after stage 2)
$C exec -T backend sh -c 'curl -s -u "$GRAPHDB_USER:$GRAPHDB_PASSWORD" -H "Accept: text/csv" \
  --data-urlencode "query=SELECT ?g (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g ORDER BY ?g" \
  http://graphdb:7200/repositories/napcore-helpdesk'

# chunks per repository
$C exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "select repository_url, count(*) from helpdesk_sourcechunk group by 1 order by 1"'

# backup of every GraphDB graph
$C exec -T backend sh -c 'curl -sf -u "$GRAPHDB_USER:$GRAPHDB_PASSWORD" -H "Accept: application/n-quads" \
  http://graphdb:7200/repositories/napcore-helpdesk/statements' > ~/graphdb-before-$(date +%F).nq
ls -lh ~/graphdb-before-*.nq
```

`-u` with empty credentials is accepted by a GraphDB without security (checked against a local one).
Note whether the graph list includes `artifact-rules/*` graphs; stage 12.2 leaves them alone.

### 12.1 Deploy

Run **Actions, Deploy to Production** (section 9). Check that the workflow is green, that
`http://localhost:8000/api/v1/health/live` (from inside the backend container, as `deploy.sh` does)
reports the new version and a build reference that matches `git rev-parse --short HEAD`, and ask one
real question. Roll back by deploying the previous commit through GitHub, never by editing the server.

### 12.2 Ontology graphs

Run the two commands from 7.1, then repeat the count query. The expected triples are those of the
committed files; compute them on any machine with rdflib:

```python
import rdflib
g = rdflib.Graph(); g.parse("docs/ontology/standards/netex.ttl", format="turtle"); print(len(g))
```

The NeTEx figure (27,129 for the file committed in #147, generated from upstream `dc6f162` with the class
hierarchy of #95) equals the count GraphDB reports for it. Do this at a quiet time and do not re-run a command
that seems to hang: read its output and the GraphDB log first. The backup from 12.0 restores the previous state.

Then restart the backend and the worker. They read the concepts and labels from GraphDB once, when a process
starts, so until they restart they keep answering with the graphs loaded before:

```bash
$C restart backend celery-worker
```

A regenerated file whose triples are unchanged (only reordered, as in #147) needs none of this. Check with rdflib
before loading:

```python
import rdflib
from rdflib.compare import isomorphic
old = rdflib.Graph().parse("netex_before.ttl")   # git show <previous commit>:docs/ontology/standards/netex.ttl
new = rdflib.Graph().parse("docs/ontology/standards/netex.ttl")
print(isomorphic(old, new))                       # True: nothing to load
```

### 12.3 Source index refresh

```bash
$C exec -T celery-worker python manage.py refresh_source_indexes --full
$C logs -f celery-worker
```

Each repository prints `ok` with a commit and counts, or `FAILED`. Compare the per-repository chunk counts
with 12.0 (SIRI must not double: that was the duplicate source removed in #40). OpRa was indexed under the old
name `OpRa-CEN/OpRa`, the same GitHub repository as `TransmodelEcosystem/OpRa`: the first refresh after the alias
fix creates the OpRa chunks under the canonical URL and then deletes the old ones, so expect `alias_removed=423`
for OpRa (or the count from 12.0) and 0 for the others, and afterwards one OpRa entry in the chunk table,
under `TransmodelEcosystem/OpRa`, then ask a SIRI question and
confirm it cites the SIRI repository. Only then switch on the daily refresh (7.3).

### 12.4 Relevance check (optional)

`RELEVANCE_CHECK_ENABLED` is off by default. When on, a question that names no standard and no artifact is
put to the controller model, which answers RELEVANT or IRRELEVANT; a failed call falls back to the keyword
rules. First prove the model call works from the server (it prints `None` when it does not):

```bash
$C exec -T backend python manage.py shell -c "
from helpdesk.services.relevance_check import is_relevant
for q in ['What is the weather in Ljubljana tomorrow?','fares','Can roadwork warnings be exchanged in real time?']:
    print(repr(is_relevant(q)), '|', q)"
```

Expect `False`, `True`, `True`. If that matches, set `RELEVANCE_CHECK_ENABLED=True` in `backend/.env.prod` and
recreate the backend:

```bash
. scripts/build_env.sh
$C up -d --force-recreate backend
```

Check that a weather question abstains, and that "fares" and "What is SIRI?" are answered. To switch it
off set the variable to `False` and recreate the backend. It uses the `CONTROLLER_LLM_*` settings.
