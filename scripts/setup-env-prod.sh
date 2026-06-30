#!/bin/bash
# Production environment configuration script
# Sets up .env.prod with secure defaults and prompted values

set -e

ENV_FILE="/opt/napcore-helpdesk/backend/.env.prod"
EXAMPLE_FILE="/opt/napcore-helpdesk/backend/.env.example"

echo "=========================================="
echo "NapcoreHelpdesk Production Environment Setup"
echo "=========================================="
echo ""

# Check if env file already exists
if [ -f "$ENV_FILE" ]; then
    read -p ".env.prod already exists. Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Generate secure secrets
echo "Generating secure secrets..."
DJANGO_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(50))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo "✓ DJANGO_SECRET_KEY generated"
echo "✓ JWT_SECRET_KEY generated"
echo "✓ POSTGRES_PASSWORD generated"
echo ""

# Prompt for user inputs
echo "Please provide the following information:"
echo ""

read -p "Server IP address or domain (e.g., 192.168.1.100 or helpdesk.example.com): " SERVER_HOST
if [ -z "$SERVER_HOST" ]; then
    echo "ERROR: Server host is required"
    exit 1
fi

read -p "Frontend URL for CORS (e.g., https://kgpi.fgpa.um.si/napcore-helpdesk or leave empty to use server host): " FRONTEND_URL
if [ -z "$FRONTEND_URL" ]; then
    # Infer frontend URL from server host
    if [[ "$SERVER_HOST" == *"://"* ]]; then
        FRONTEND_URL="$SERVER_HOST/napcore-helpdesk"
    else
        # Assume HTTPS for non-IP domains
        if [[ "$SERVER_HOST" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            FRONTEND_URL="http://$SERVER_HOST/napcore-helpdesk"
        else
            FRONTEND_URL="https://$SERVER_HOST/napcore-helpdesk"
        fi
    fi
    echo "Using inferred frontend URL: $FRONTEND_URL"
fi

read -p "GitHub API Token (leave empty to skip): " GITHUB_TOKEN

read -p "Enable LLM? (y/n) [default: n]: " -n 1 -r
echo
ENABLE_LLM="False"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ENABLE_LLM="True"
    read -p "  LLM API Key (e.g., Azure, OpenAI): " LLM_API_KEY
    read -p "  LLM API Base URL [default: https://models.inference.ai.azure.com]: " LLM_API_BASE_URL
    LLM_API_BASE_URL=${LLM_API_BASE_URL:-"https://models.inference.ai.azure.com"}
    read -p "  LLM Model [default: gpt-4o-mini]: " LLM_MODEL
    LLM_MODEL=${LLM_MODEL:-"gpt-4o-mini"}
fi

read -p "Enable GraphDB? (y/n) [default: y]: " -n 1 -r
echo
GRAPHDB_ENABLED="True"
if [[ $REPLY =~ ^[Nn]$ ]]; then
    GRAPHDB_ENABLED="False"
fi

read -p "Enable Graph RAG? (y/n) [default: y]: " -n 1 -r
echo
GRAPH_RAG_ENABLED="True"
if [[ $REPLY =~ ^[Nn]$ ]]; then
    GRAPH_RAG_ENABLED="False"
fi

echo ""
echo "Creating $ENV_FILE..."
echo ""

# Create .env.prod file
cat > "$ENV_FILE" <<EOF
# ============================================
# NapcoreHelpdesk Production Environment
# Generated: $(date)
# ============================================

# --- Django Configuration ---
DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=$SERVER_HOST
CORS_ALLOWED_ORIGINS=$FRONTEND_URL
SERVICE_NAME=napcore-helpdesk

# --- JWT Configuration ---
JWT_SECRET_KEY=$JWT_SECRET_KEY

# --- Database Configuration ---
# (Host and port are set in docker-compose.prod.yml)
POSTGRES_DB=napcore_helpdesk
POSTGRES_USER=napcore
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# --- GitHub Integration ---
EOF

if [ -n "$GITHUB_TOKEN" ]; then
    echo "GITHUB_API_TOKEN=$GITHUB_TOKEN" >> "$ENV_FILE"
else
    echo "# GITHUB_API_TOKEN=<token with public_repo read scope for indexing>" >> "$ENV_FILE"
fi

cat >> "$ENV_FILE" <<EOF

# --- LLM Configuration ---
LLM_ENABLED=$ENABLE_LLM
EOF

if [ "$ENABLE_LLM" = "True" ]; then
    cat >> "$ENV_FILE" <<EOF
LLM_API_KEY=$LLM_API_KEY
LLM_API_BASE_URL=$LLM_API_BASE_URL
LLM_MODEL=$LLM_MODEL
EOF
fi

cat >> "$ENV_FILE" <<EOF

# --- GraphDB Configuration ---
GRAPHDB_ENABLED=$GRAPHDB_ENABLED
GRAPH_RAG_ENABLED=$GRAPH_RAG_ENABLED

# --- Development Flags (must be False in production) ---
DEV_JWT_AUTO_ISSUE=False
NAPCORE_SKIP_GRAPHDB_IMPORT=False
EOF

# Set secure permissions
chmod 600 "$ENV_FILE"
echo "✓ Environment file created: $ENV_FILE"
echo "✓ Permissions set to 600 (readable only by owner)"
echo ""

# Verify file
echo "File contents (first 10 lines):"
head -10 "$ENV_FILE"
echo "..."
echo ""

echo "=========================================="
echo "✓ Environment configuration complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review the generated .env.prod file"
echo "2. Proceed with: sudo /opt/napcore-helpdesk/scripts/deploy.sh"
echo ""
