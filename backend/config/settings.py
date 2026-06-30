from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent


def _read_repo_version(default: str = "0.1.0") -> str:
    version_file = BASE_DIR.parent / "VERSION"
    try:
        version = version_file.read_text(encoding="utf-8").strip()
    except Exception:
        return default
    return version or default


REPO_VERSION = _read_repo_version(default="0.1.0")

env = environ.Env(
    DJANGO_DEBUG=(bool, True),
    SERVICE_NAME=(str, "napcore-helpdesk"),
    SERVICE_VERSION=(str, REPO_VERSION),
    SERVICE_BUILD_REF=(str, "dev"),
    JWT_SECRET_KEY=(str, ""),
    JWT_ALGORITHM=(str, "HS256"),
    JWT_ISSUER=(str, ""),
    JWT_AUDIENCE=(str, ""),
    DEV_JWT_AUTO_ISSUE=(bool, True),
    DEV_JWT_DEFAULT_SUBJECT=(str, "user-local"),
    DEV_JWT_DEFAULT_ROLES=(str, "editor,reviewer,publisher"),
    DEV_JWT_TTL_MINUTES=(int, 480),
    ALLOWED_SOURCE_REPOSITORIES=(
        str,
        "https://github.com/TransmodelEcosystem/NeTEx,https://github.com/SIRI-CEN/SIRI,https://github.com/OpRa-CEN/OpRa",
    ),
    INDEX_SCHEDULE_REPO_URL=(str, ""),
    INDEX_SCHEDULE_REPO_PATH=(str, ""),
    INDEX_SCHEDULE_PROFILE=(str, "netex"),
    GITHUB_API_TOKEN=(str, ""),
    GITHUB_API_VERIFY_SSL=(bool, True),
    GITHUB_CA_BUNDLE=(str, ""),
    LLM_ENABLED=(bool, False),
    LLM_PROVIDER=(str, "openai-compatible"),
    LLM_API_BASE_URL=(str, "https://api.openai.com/v1"),
    LLM_API_KEY=(str, ""),
    LLM_MODEL=(str, "gpt-4o-mini"),
    LLM_VERIFY_SSL=(bool, True),
    LLM_CA_BUNDLE=(str, ""),
    LLM_TIMEOUT_SECONDS=(int, 20),
    LLM_MAX_TOKENS=(int, 250),
    LLM_TEMPERATURE=(float, 0.2),
    LLM_MAX_EVIDENCE_CHUNKS=(int, 4),
    LLM_MAX_EVIDENCE_CHARS_PER_CHUNK=(int, 1200),
    CONTROLLER_LLM_ENABLED=(bool, False),
    CONTROLLER_LLM_PROVIDER=(str, "subprocess"),
    CONTROLLER_LLM_EXECUTABLE=(str, ""),
    CONTROLLER_LLM_MODEL_PATH=(str, ""),
    CONTROLLER_LLM_DEVICE=(str, "none"),
    CONTROLLER_LLM_TIMEOUT_SECONDS=(int, 20),
    CONTROLLER_LLM_CTX_SIZE=(int, 2048),
    CONTROLLER_LLM_MAX_TOKENS=(int, 96),
    CONTROLLER_LLM_THREADS=(int, 8),
    CONTROLLER_LLM_TEMPERATURE=(float, 0.0),
    CONTROLLER_LLM_API_BASE_URL=(str, ""),
    CONTROLLER_LLM_API_KEY=(str, ""),
    CONTROLLER_LLM_API_MODEL=(str, ""),
    CONTROLLER_LLM_VERIFY_SSL=(bool, True),
    CONTROLLER_LLM_CA_BUNDLE=(str, ""),
    EMBEDDING_ENABLED=(bool, False),
    EMBEDDING_PROVIDER=(str, "openai-compatible"),
    EMBEDDING_API_BASE_URL=(str, "https://api.openai.com/v1"),
    EMBEDDING_API_KEY=(str, ""),
    EMBEDDING_MODEL=(str, "text-embedding-3-small"),
    EMBEDDING_TIMEOUT_SECONDS=(int, 30),
    SEED_REPO_NETEX=(str, "https://github.com/TransmodelEcosystem/NeTEx"),
    SEED_REPO_SIRI=(str, "https://github.com/SIRI-CEN/SIRI"),
    SEED_REPO_OPRA=(str, "https://github.com/OpRa-CEN/OpRa"),
    GRAPH_RAG_ENABLED=(bool, False),
    SEMANTIC_LOW_CONFIDENCE_THRESHOLD=(float, 0.60),
    EVIDENCE_GATE_ENABLED=(bool, False),
    EVIDENCE_GATE_MIN_ALIGNMENT=(float, 0.30),
    EVIDENCE_GATE_MIN_CHUNKS=(int, 1),
    EVIDENCE_GATE_MIN_REPOSITORIES_MULTI_SCOPE=(int, 2),
    GRAPHDB_ENABLED=(bool, False),
    GRAPHDB_SPARQL_ENDPOINT=(str, ""),
    GRAPHDB_REPOSITORY=(str, ""),
    GRAPHDB_USER=(str, ""),
    GRAPHDB_PASSWORD=(str, ""),
    GRAPHDB_TIMEOUT_SECONDS=(int, 5),
    GRAPH_RAG_VARIANT=(str, "baseline"),
    GRAPH_EXPANSION_MAX_CONCEPTS=(int, 56),
    GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS=(int, 36),
    RETRIEVAL_DIVERSITY_ENABLED=(bool, True),
    RETRIEVAL_MAX_SAME_SOURCE_PATH=(int, 2),
    RETRIEVAL_SCORING_CANDIDATE_CAP=(int, 32),
    RETRIEVAL_GRAPH_PRESELECT_MULTIPLIER=(float, 2.0),
    RETRIEVAL_MMR_LAMBDA=(float, 0.92),
    RETRIEVAL_KEYWORD_TRAP_PENALTY=(float, 0.60),
    POLICY_STRICT_CLAIM_GUARD=(bool, False),
    SEMANTIC_CLUSTER_WINDOW_DAYS=(int, 30),
    SEMANTIC_CLUSTER_MIN_SIZE=(int, 2),
    SEMANTIC_CLUSTER_SIMILARITY_THRESHOLD=(float, 0.82),
    SEMANTIC_CLUSTER_MAX_EVENTS=(int, 500),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="change-me")
DEBUG = env("DJANGO_DEBUG")
SERVICE_NAME = env("SERVICE_NAME", default="napcore-helpdesk").strip() or "napcore-helpdesk"
SERVICE_VERSION = env("SERVICE_VERSION", default=REPO_VERSION).strip() or REPO_VERSION
SERVICE_BUILD_REF = env("SERVICE_BUILD_REF", default="dev").strip() or "dev"
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.postgres",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "helpdesk",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# CORS configuration: allow frontend to call backend API
# Environment variable format: comma-separated list (e.g., "http://localhost:5173,https://example.com")
# Defaults to localhost for development
_cors_origins_env = env(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173"
)
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in _cors_origins_env.split(",") if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-request-id",  # Custom header used by frontend
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="napcore_helpdesk"),
        "USER": env("POSTGRES_USER", default="napcore"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="napcore"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        # Use template1 for test databases so preinstalled extensions (e.g., pgvector)
        # are inherited without requiring superuser rights in migrations.
        "TEST": {"TEMPLATE": "template1"},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "helpdesk.authentication.JWTBearerAuthentication",
    ],
    "EXCEPTION_HANDLER": "helpdesk.api.exceptions.custom_exception_handler",
}

JWT_SECRET_KEY = env("JWT_SECRET_KEY")
JWT_ALGORITHM = env("JWT_ALGORITHM")
JWT_ISSUER = env("JWT_ISSUER").strip() or None
JWT_AUDIENCE = env("JWT_AUDIENCE").strip() or None
DEV_JWT_AUTO_ISSUE = env("DEV_JWT_AUTO_ISSUE")
DEV_JWT_DEFAULT_SUBJECT = env("DEV_JWT_DEFAULT_SUBJECT").strip() or "user-local"
DEV_JWT_DEFAULT_ROLES = [
    role.strip()
    for role in env("DEV_JWT_DEFAULT_ROLES", default="editor,reviewer,publisher").split(",")
    if role.strip()
]
DEV_JWT_TTL_MINUTES = env("DEV_JWT_TTL_MINUTES")

ALLOWED_SOURCE_REPOSITORIES = {
    value.strip()
    for value in env(
        "ALLOWED_SOURCE_REPOSITORIES",
        default="https://github.com/TransmodelEcosystem/NeTEx,https://github.com/SIRI-CEN/SIRI,https://github.com/OpRa-CEN/OpRa",
    ).split(",")
    if value.strip()
}

INDEX_SCHEDULE_REPO_URL = env("INDEX_SCHEDULE_REPO_URL").strip()
INDEX_SCHEDULE_REPO_PATH = env("INDEX_SCHEDULE_REPO_PATH").strip()
INDEX_SCHEDULE_PROFILE = env("INDEX_SCHEDULE_PROFILE", default="netex").strip() or "netex"
GITHUB_API_TOKEN = env("GITHUB_API_TOKEN", default="").strip()
GITHUB_API_VERIFY_SSL = env("GITHUB_API_VERIFY_SSL")
GITHUB_CA_BUNDLE = env("GITHUB_CA_BUNDLE", default="").strip() or None

LLM_ENABLED = env("LLM_ENABLED")
LLM_PROVIDER = env("LLM_PROVIDER").strip() or "openai-compatible"
LLM_API_BASE_URL = env("LLM_API_BASE_URL").strip() or "https://api.openai.com/v1"
# Allow reusing a GitHub token for GitHub Models when a dedicated LLM key is not set.
LLM_API_KEY = env("LLM_API_KEY", default="").strip() or GITHUB_API_TOKEN
LLM_MODEL = env("LLM_MODEL").strip() or "gpt-4o-mini"
LLM_VERIFY_SSL = env("LLM_VERIFY_SSL")
LLM_CA_BUNDLE = env("LLM_CA_BUNDLE", default="").strip() or GITHUB_CA_BUNDLE
LLM_TIMEOUT_SECONDS = env("LLM_TIMEOUT_SECONDS")
LLM_MAX_TOKENS = env("LLM_MAX_TOKENS")
LLM_TEMPERATURE = env("LLM_TEMPERATURE")
LLM_MAX_EVIDENCE_CHUNKS = env("LLM_MAX_EVIDENCE_CHUNKS")
LLM_MAX_EVIDENCE_CHARS_PER_CHUNK = env("LLM_MAX_EVIDENCE_CHARS_PER_CHUNK")
CONTROLLER_LLM_ENABLED = env("CONTROLLER_LLM_ENABLED")
CONTROLLER_LLM_PROVIDER = env("CONTROLLER_LLM_PROVIDER", default="subprocess").strip() or "subprocess"
CONTROLLER_LLM_EXECUTABLE = env("CONTROLLER_LLM_EXECUTABLE", default="").strip()
CONTROLLER_LLM_MODEL_PATH = env("CONTROLLER_LLM_MODEL_PATH", default="").strip()
CONTROLLER_LLM_DEVICE = env("CONTROLLER_LLM_DEVICE", default="none").strip() or "none"
CONTROLLER_LLM_TIMEOUT_SECONDS = env("CONTROLLER_LLM_TIMEOUT_SECONDS")
CONTROLLER_LLM_CTX_SIZE = env("CONTROLLER_LLM_CTX_SIZE")
CONTROLLER_LLM_MAX_TOKENS = env("CONTROLLER_LLM_MAX_TOKENS")
CONTROLLER_LLM_THREADS = env("CONTROLLER_LLM_THREADS")
CONTROLLER_LLM_TEMPERATURE = env("CONTROLLER_LLM_TEMPERATURE")
CONTROLLER_LLM_API_BASE_URL = env("CONTROLLER_LLM_API_BASE_URL", default="").strip() or LLM_API_BASE_URL
CONTROLLER_LLM_API_KEY = env("CONTROLLER_LLM_API_KEY", default="").strip() or LLM_API_KEY
CONTROLLER_LLM_API_MODEL = env("CONTROLLER_LLM_API_MODEL", default="").strip() or LLM_MODEL
CONTROLLER_LLM_VERIFY_SSL = env("CONTROLLER_LLM_VERIFY_SSL")
CONTROLLER_LLM_CA_BUNDLE = env("CONTROLLER_LLM_CA_BUNDLE", default="").strip()

EMBEDDING_ENABLED = env("EMBEDDING_ENABLED")
EMBEDDING_PROVIDER = env("EMBEDDING_PROVIDER").strip() or "openai-compatible"
EMBEDDING_API_BASE_URL = env("EMBEDDING_API_BASE_URL").strip() or "https://api.openai.com/v1"
EMBEDDING_API_KEY = env("EMBEDDING_API_KEY").strip()
EMBEDDING_MODEL = env("EMBEDDING_MODEL").strip() or "text-embedding-3-small"
EMBEDDING_TIMEOUT_SECONDS = env("EMBEDDING_TIMEOUT_SECONDS")
SEED_REPO_NETEX = env("SEED_REPO_NETEX").strip() or "https://github.com/TransmodelEcosystem/NeTEx"
SEED_REPO_SIRI = env("SEED_REPO_SIRI").strip() or "https://github.com/SIRI-CEN/SIRI"
SEED_REPO_OPRA = env("SEED_REPO_OPRA").strip() or "https://github.com/OpRa-CEN/OpRa"
ALLOWED_SOURCE_REPOSITORIES |= {
    SEED_REPO_NETEX,
    SEED_REPO_SIRI,
    SEED_REPO_OPRA,
}
GRAPH_RAG_ENABLED = env("GRAPH_RAG_ENABLED")
SEMANTIC_LOW_CONFIDENCE_THRESHOLD = env("SEMANTIC_LOW_CONFIDENCE_THRESHOLD")
EVIDENCE_GATE_ENABLED = env("EVIDENCE_GATE_ENABLED")
EVIDENCE_GATE_MIN_ALIGNMENT = env("EVIDENCE_GATE_MIN_ALIGNMENT")
EVIDENCE_GATE_MIN_CHUNKS = env("EVIDENCE_GATE_MIN_CHUNKS")
EVIDENCE_GATE_MIN_REPOSITORIES_MULTI_SCOPE = env("EVIDENCE_GATE_MIN_REPOSITORIES_MULTI_SCOPE")
GRAPHDB_ENABLED = env("GRAPHDB_ENABLED")
GRAPHDB_SPARQL_ENDPOINT = env("GRAPHDB_SPARQL_ENDPOINT", default="").strip()
GRAPHDB_REPOSITORY = env("GRAPHDB_REPOSITORY", default="").strip()
GRAPHDB_USER = env("GRAPHDB_USER", default="").strip()
GRAPHDB_PASSWORD = env("GRAPHDB_PASSWORD", default="").strip()
GRAPHDB_TIMEOUT_SECONDS = env("GRAPHDB_TIMEOUT_SECONDS")
GRAPH_EXPANSION_MAX_CONCEPTS = env("GRAPH_EXPANSION_MAX_CONCEPTS")
GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS = env("GRAPH_EXPANSION_MAX_CANDIDATE_CHUNKS")
RETRIEVAL_DIVERSITY_ENABLED = env("RETRIEVAL_DIVERSITY_ENABLED")
RETRIEVAL_MAX_SAME_SOURCE_PATH = env("RETRIEVAL_MAX_SAME_SOURCE_PATH")
RETRIEVAL_SCORING_CANDIDATE_CAP = env("RETRIEVAL_SCORING_CANDIDATE_CAP")
RETRIEVAL_GRAPH_PRESELECT_MULTIPLIER = env("RETRIEVAL_GRAPH_PRESELECT_MULTIPLIER")
RETRIEVAL_MMR_LAMBDA = env("RETRIEVAL_MMR_LAMBDA")
RETRIEVAL_KEYWORD_TRAP_PENALTY = env("RETRIEVAL_KEYWORD_TRAP_PENALTY")
POLICY_STRICT_CLAIM_GUARD = env("POLICY_STRICT_CLAIM_GUARD")
SEMANTIC_CLUSTER_WINDOW_DAYS = env("SEMANTIC_CLUSTER_WINDOW_DAYS")
SEMANTIC_CLUSTER_MIN_SIZE = env("SEMANTIC_CLUSTER_MIN_SIZE")
SEMANTIC_CLUSTER_SIMILARITY_THRESHOLD = env("SEMANTIC_CLUSTER_SIMILARITY_THRESHOLD")
SEMANTIC_CLUSTER_MAX_EVENTS = env("SEMANTIC_CLUSTER_MAX_EVENTS")

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")

CELERY_BEAT_SCHEDULE = {
    "helpdesk-reindex-default-repository-daily": {
        "task": "helpdesk.reindex_default_repository",
        "schedule": 60 * 60 * 24,
    }
}
