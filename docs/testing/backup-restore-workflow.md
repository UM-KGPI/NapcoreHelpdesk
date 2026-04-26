# Backup & Restore Workflow

This document describes how to backup and restore NAPCORE Helpdesk development environment data.

## Overview

The NAPCORE Helpdesk development setup includes automated backup and restore capabilities to protect against accidental data loss during development:

- **Backup**: Captures PostgreSQL databases (napcore_helpdesk, digital_twin) and GraphDB configuration
- **Restore**: Hydrates databases from saved backups
- **Safe Prune**: Combines backup → prune workflow to prevent data loss during cleanup

## Backup

### Automatic Backup

Backup is performed automatically before destructive operations:

```bash
make docker-dev-safe-prune    # Backs up before pruning
make docker-dev-backup        # Manually create backup
```

### Manual Backup

Create a backup manually at any time:

```bash
make docker-dev-backup
```

This creates a timestamped directory under `.backups/` containing:
- `napcore_helpdesk.sql` — Complete PostgreSQL database dump (274 MB typical)
- `digital_twin.sql` — Secondary project database (small)
- `graphdb-home.tar.gz` — GraphDB configuration and repositories

### Backup Structure

```
.backups/
├── 20260426_115421/
│   ├── napcore_helpdesk.sql
│   ├── digital_twin.sql
│   └── graphdb-home.tar.gz
└── 20260426_120518/
    ├── napcore_helpdesk.sql
    ├── digital_twin.sql
    └── graphdb-home.tar.gz
```

## Restore

### Interactive Restore

Restore from the latest backup or choose interactively:

```bash
make docker-dev-restore
```

This will:
1. List all available backups
2. Prompt you to select one (defaults to latest if you press Enter)
3. Show confirmation with file sizes
4. Require you to type "yes" to proceed
5. Restore PostgreSQL databases
6. Restore GraphDB configuration (if applicable)
7. Validate the restore

### Restore with Specific Backup

Restore a specific backup by timestamp (non-interactive):

```bash
make docker-dev-restore BACKUP_ID=20260426_120518
```

Or use the script directly:

```bash
bash scripts/restore-dev-data.sh 20260426_120518
```

### What Gets Restored

#### PostgreSQL Databases
- `napcore_helpdesk`: Main application database with FAQ entries, answers, and editorial workflow
- `digital_twin`: Secondary project database (if it exists in backup)

Both databases are fully restored including all tables, data, and sequences.

#### GraphDB
- GraphDB repositories and ontology configuration
- GraphDB restore is **manual** (see below)

### GraphDB Manual Restore

GraphDB restoration requires manual steps. After running restore, GraphDB data can be restored by:

```bash
# 1. Stop GraphDB container
docker exec napcorehelpdesk-graphdb-1 pkill -f java

# 2. Extract backup locally
tar -xzf .backups/20260426_120518/graphdb-home.tar.gz -C /tmp

# 3. Copy into container
docker cp /tmp/graphdb/home napcorehelpdesk-graphdb-1:/opt/graphdb/

# 4. Restart container
docker restart napcorehelpdesk-graphdb-1
```

Or use Docker directly:

```bash
BACKUP_ID=20260426_120518
docker exec napcorehelpdesk-graphdb-1 bash -c \
  "pkill -f java; sleep 2; cd /opt/graphdb && rm -rf home && tar -xzf - < /dev/null" < \
  ".backups/$BACKUP_ID/graphdb-home.tar.gz"
docker restart napcorehelpdesk-graphdb-1
```

## Safe Prune Workflow

The safe prune workflow ensures data safety:

```bash
make docker-dev-safe-prune
```

This performs:
1. ✅ **Health check** — Verifies DB mode and container health
2. 📦 **Backup** — Creates timestamped backup
3. 📊 **Disk report (before)** — Shows current disk usage
4. 🧹 **Prune** — Removes unused Docker images and builder cache
5. 📊 **Disk report (after)** — Shows recovered disk space

Example output:

```
[INFO] Running health checks...
[SUCCESS] Database mode: external-db
[SUCCESS] Health checks passed

[INFO] Creating backup...
[SUCCESS] Backup created: .backups/20260426_120518

[INFO] Disk usage before prune:
...
total: 15.2 GB

[INFO] Pruning...
Deleted Images
...
freed 1.082 GB

[INFO] Disk usage after prune:
...
total: 14.1 GB
```

## Recovery Scenarios

### Scenario 1: Accidental Data Change

If you made an unwanted change to the database:

```bash
# List available backups
make docker-dev-restore

# Select the backup from before the change and confirm restore
# Type "yes" when prompted
```

### Scenario 2: Testing with Clean State

Create a backup before testing, then restore if needed:

```bash
# Create baseline backup
make docker-dev-backup

# Run tests/experiments
...

# Restore clean state
make docker-dev-restore BACKUP_ID=<your-baseline>
```

### Scenario 3: Disk Space Recovery

Use safe-prune to reclaim space while protecting data:

```bash
make docker-dev-safe-prune

# Backup is created automatically before pruning
# Disk space is reclaimed
# Restore available if needed
```

## Troubleshooting

### Restore Fails - "Connection Failed"

The PostgreSQL server must be running:

```bash
# Start containers first
make docker-dev-up

# Then restore
make docker-dev-restore
```

### Restore Shows "Password Authentication Failed"

Verify PostgreSQL credentials in `backend/.env`:

```bash
grep POSTGRES_ backend/.env
```

Should show:
```
POSTGRES_USER=napcore
POSTGRES_PASSWORD=napcore
POSTGRES_DB=napcore_helpdesk
```

If using external PostgreSQL, verify connection:

```bash
psql postgresql://napcore:napcore@localhost:5432/napcore_helpdesk -c "SELECT 1;"
```

### GraphDB Not Responding After Restore

GraphDB may take time to start. Wait a moment and check:

```bash
docker exec napcorehelpdesk-graphdb-1 curl http://localhost:8080/protocol
```

### Backup File Is Large (274 MB)

This is normal for a production-scale database. If space is limited:

- Create backups only when needed
- Store old backups on external media
- Use PostgreSQL binary backup format (future enhancement)

```bash
# Remove old backups (be careful!)
rm -rf .backups/20260426_115421
```

## Best Practices

1. **Backup before major changes**
   ```bash
   make docker-dev-backup
   ```

2. **Use safe-prune instead of manual prune**
   ```bash
   make docker-dev-safe-prune  # Auto-backs up
   ```

3. **Test restore periodically**
   ```bash
   # Restore from old backup to verify it works
   make docker-dev-restore BACKUP_ID=<old-timestamp>
   ```

4. **Archive backups**
   ```bash
   # Move old backups to archive
   mkdir -p backups-archive
   mv .backups/20260426_115421 backups-archive/
   ```

5. **Monitor disk space**
   ```bash
   make docker-dev-doctor
   ```

## Implementation Details

### Backup Script (`scripts/backup-dev-data.sh`)

- Uses `pg_dump` for SQL exports
- Includes PostgreSQL schema, data, and sequences
- Supports multiple databases
- Creates tar.gz of GraphDB home directory
- Stores backups in `.backups/{YYYYMMDD_HHMMSS}/`

### Restore Script (`scripts/restore-dev-data.sh`)

- Interactive backup selection
- Reads credentials from `backend/.env`
- Restores PostgreSQL databases via `psql`
- Validates restore with sample queries
- Provides recovery instructions for GraphDB
- Supports non-interactive mode via `BACKUP_ID` parameter

### Make Targets

```bash
make docker-dev-backup        # Create backup
make docker-dev-restore       # Interactive restore
make docker-dev-doctor        # Check health/mode
make docker-dev-safe-prune    # Backup + prune safely
```

## See Also

- [Local Run Quickstart](local-run-quickstart.md) — Getting started
- [PostgreSQL + pgvector Runbook](../architecture/postgresql-pgvector-runbook.md) — DB operations
- [Docker Compose Setup](../../docker-compose.dev.yml) — Container configuration
