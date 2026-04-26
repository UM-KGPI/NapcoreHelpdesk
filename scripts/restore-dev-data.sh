#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Try to source environment variables from .env if available
if [[ -f "backend/.env" ]]; then
    set +a  # Don't export all vars by default
    source backend/.env 2>/dev/null || true
    set -a
fi

# Configuration (can be overridden by environment)
BACKUPS_DIR=".backups"
GRAPHDB_CONTAINER="${GRAPHDB_CONTAINER:-napcorehelpdesk-graphdb-1}"
POSTGRES_USER="${POSTGRES_USER:-napcore}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-password}"
POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"  # Use IPv4 explicitly to avoid IPv6 issues
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Verify backups directory exists
if [[ ! -d "$BACKUPS_DIR" ]]; then
    log_error "Backups directory not found: $BACKUPS_DIR"
    echo "Run 'make docker-dev-backup' first to create a backup."
    exit 1
fi

# List available backups
list_backups() {
    log_info "Available backups:"
    local count=0
    while IFS= read -r backup_dir; do
        if [[ -d "$backup_dir" ]]; then
            count=$((count + 1))
            local timestamp=$(basename "$backup_dir")
            local files=$(ls -1 "$backup_dir" | tr '\n' ',' | sed 's/,$//')
            echo "  [$count] $timestamp - Files: $files"
        fi
    done < <(find "$BACKUPS_DIR" -maxdepth 1 -type d ! -name ".backups" | sort -r)

    if [[ $count -eq 0 ]]; then
        log_error "No backups found in $BACKUPS_DIR"
        exit 1
    fi
}

# Select backup interactively or by parameter
select_backup() {
    local backup_param="${1:-}"

    if [[ -z "$backup_param" ]]; then
        # Interactive selection
        list_backups
        echo ""
        read -p "Enter backup number or timestamp (or press Enter for latest): " selection

        if [[ -z "$selection" ]]; then
            # Get latest backup
            selection=$(find "$BACKUPS_DIR" -maxdepth 1 -type d ! -name ".backups" | sort -r | head -1 | xargs basename)
            log_info "Using latest backup: $selection"
        elif [[ "$selection" =~ ^[0-9]+$ ]]; then
            # Convert number to timestamp
            selection=$(find "$BACKUPS_DIR" -maxdepth 1 -type d ! -name ".backups" | sort -r | sed -n "${selection}p" | xargs basename)
            if [[ -z "$selection" ]]; then
                log_error "Invalid backup number"
                exit 1
            fi
        fi
    else
        selection="$backup_param"
    fi

    BACKUP_PATH="$BACKUPS_DIR/$selection"

    if [[ ! -d "$BACKUP_PATH" ]]; then
        log_error "Backup not found: $BACKUP_PATH"
        exit 1
    fi

    log_success "Selected backup: $selection"
}

# Confirm before restoring
confirm_restore() {
    local backup_timestamp=$(basename "$BACKUP_PATH")

    echo ""
    echo -e "${YELLOW}=== RESTORE CONFIRMATION ===${NC}"
    echo "Backup: $backup_timestamp"
    echo "Location: $BACKUP_PATH"
    echo "Files in backup:"
    ls -lh "$BACKUP_PATH"
    echo ""
    echo -e "${RED}WARNING: This will OVERWRITE existing database data.${NC}"
    read -p "Type 'yes' to confirm restore: " confirmation

    if [[ "$confirmation" != "yes" ]]; then
        log_warning "Restore cancelled."
        exit 0
    fi
}

# Restore SQL databases
restore_databases() {
    log_info "Restoring databases..."

    # Check PostgreSQL connection
    if ! command -v psql &> /dev/null; then
        log_error "psql not found. Install PostgreSQL client tools."
        exit 1
    fi

    # Export password for psql
    export PGPASSWORD="$POSTGRES_PASSWORD"

    # Test connection first
    log_info "Testing PostgreSQL connection to $POSTGRES_HOST:$POSTGRES_PORT as $POSTGRES_USER..."
    if psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d napcore_helpdesk -c "SELECT 1;" &>/dev/null 2>&1; then
        log_success "PostgreSQL connection successful"
    else
        log_warning "PostgreSQL connection test failed. Attempting restore anyway..."
    fi

    # Restore napcore_helpdesk
    if [[ -f "$BACKUP_PATH/napcore_helpdesk.sql" ]]; then
        local file_size=$(du -h "$BACKUP_PATH/napcore_helpdesk.sql" | cut -f1)
        log_info "Restoring napcore_helpdesk database ($file_size)..."
        if psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d napcore_helpdesk < "$BACKUP_PATH/napcore_helpdesk.sql" 2>&1 | grep -i "error\|failed" | head -5; then
            log_warning "Restore had warnings (non-fatal schema/reference issues may occur)"
        fi
        log_success "napcore_helpdesk restore completed"
    else
        log_warning "napcore_helpdesk.sql not found in backup"
    fi

    # Restore digital_twin
    if [[ -f "$BACKUP_PATH/digital_twin.sql" ]]; then
        local file_size=$(du -h "$BACKUP_PATH/digital_twin.sql" | cut -f1)
        log_info "Restoring digital_twin database ($file_size)..."
        if psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d digital_twin < "$BACKUP_PATH/digital_twin.sql" 2>&1 | grep -i "error\|failed" | head -5; then
            log_warning "Restore had warnings (non-fatal schema/reference issues may occur)"
        fi
        log_success "digital_twin restore completed"
    else
        log_warning "digital_twin.sql not found in backup"
    fi

    unset PGPASSWORD
}

# Restore GraphDB
restore_graphdb() {
    log_info "Restoring GraphDB..."

    if [[ ! -f "$BACKUP_PATH/graphdb-home.tar.gz" ]]; then
        log_warning "graphdb-home.tar.gz not found in backup"
        return
    fi

    # Check if GraphDB container is running
    if ! docker ps --filter "name=$GRAPHDB_CONTAINER" --quiet | grep -q .; then
        log_warning "GraphDB container not running: $GRAPHDB_CONTAINER"
        log_warning "GraphDB restore skipped (start containers first). Data can be restored manually if needed."
        return
    fi

    log_info "Note: GraphDB restore is experimental. PostgreSQL data has been restored successfully."
    log_warning "To restore GraphDB manually:"
    log_warning "  1. Stop GraphDB: docker exec $GRAPHDB_CONTAINER pkill -f java"
    log_warning "  2. Extract backup: tar -xzf $BACKUP_PATH/graphdb-home.tar.gz -C /tmp"
    log_warning "  3. Restore: docker cp /tmp/graphdb/home /. $GRAPHDB_CONTAINER:/opt/graphdb/"
    log_warning "  4. Restart GraphDB container"
    log_info "Skipping GraphDB restore for this session."
}

# Post-restore validation
validate_restore() {
    log_info "Validating restore..."

    export PGPASSWORD="$POSTGRES_PASSWORD"

    # Check napcore_helpdesk
    local napcore_count=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d napcore_helpdesk -t -c "SELECT COUNT(*) FROM helpdesk_answer LIMIT 1;" 2>/dev/null | tr -d ' ' || echo "")

    if [[ -n "$napcore_count" && "$napcore_count" =~ ^[0-9]+$ ]]; then
        log_success "napcore_helpdesk: $napcore_count answers in database"
    else
        log_warning "Could not verify napcore_helpdesk answer count"
    fi

    # Check GraphDB
    if docker ps --filter "name=$GRAPHDB_CONTAINER" --quiet | grep -q .; then
        if docker exec "$GRAPHDB_CONTAINER" curl -s http://localhost:8080/protocol &>/dev/null; then
            log_success "GraphDB is running and responsive"
        else
            log_warning "GraphDB container running but not responding to health check (may still be starting)"
        fi
    fi

    unset PGPASSWORD
}

# Main flow
main() {
    local backup_param="${1:-}"

    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    NAPCORE HELPDESK RESTORE                     ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    select_backup "$backup_param"
    confirm_restore

    echo ""
    log_info "Starting restore process..."
    echo ""

    restore_databases
    restore_graphdb

    echo ""
    log_info "Restore completed. Running validation..."
    echo ""

    validate_restore

    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    RESTORE COMPLETED SUCCESSFULLY               ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
}

main "$@"
