from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

from config.beat_schedule import build_beat_schedule

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
    GITHUB_OAUTH_CLIENT_ID=(str, ""),
    GITHUB_OAUTH_CLIENT_SECRET=(str, ""),
    GITHUB_OAUTH_CALLBACK_URL=(str, ""),
    EDITOR_APP_URL=(str, ""),
    EDITOR_ADMIN_GITHUB_LOGINS=(str, ""),
    EDITOR_JWT_TTL_MINUTES=(int, 480),
    ALLOWED_SOURCE_REPOSITORIES=(
        str,
        "https://github.com/TransmodelEcosystem/NeTEx,https://github.com/TransmodelEcosystem/SIRI,https://github.com/TransmodelEcosystem/OpRa",
    ),
    SOURCE_REFRESH_ENABLED=(bool, False),
    SOURCE_REFRESH_HOUR=(int, 3),
    SOURCE_REFRESH_MINUTE=(int, 30),
    SOURCE_CHECKOUT_DIR=(str, "/app/repos"),
    GITHUB_API_TOKEN=(str, ""),
    GITHUB_API_VERIFY_SSL=(bool, True),
    GITHUB_CA_BUNDLE=(str, ""),
    TRANSMODEL_HTML_BASE_URL=(str, "https://kgpi.fgpa.um.si/napcore-helpdesk/transmodel"),
    SEARCH_TRANSLATION_ENABLED=(bool, True),
    LLM_ENABLED=(bool, False),
    LLM_PROVIDER=(str, "openai-compatible"),
    LLM_API_BASE_URL=(str, "https://api.openai.com/v1"),
    LLM_API_KEY=(str, ""),
    LLM_MODEL=(str, "gpt-4o-mini"),
    LLM_VERIFY_SSL=(bool, True),
    LLM_CA_BUNDLE=(str, ""),
    LLM_TIMEOUT_SECONDS=(int, 20),
    LLM_MAX_TOKENS=(int, 4000),
    LLM_TEMPERATURE=(float, 0.2),
    LLM_JSON_MODE=(bool, True),
    LLM_DISABLE_THINKING=(bool, True),
    LLM_STREAMING=(bool, True),
    LLM_REASONING_TOKEN_ALLOWANCE=(int, 0),
    ANTHROPIC_API_KEY=(str, ""),
    LLM_ANTHROPIC_EFFORT=(str, "low"),
    EMBEDDING_BACKEND=(str, "hash"),
    EMBEDDING_SERVICE_URL=(str, "http://embedder:8090"),
    EMBEDDING_SERVICE_TIMEOUT_SECONDS=(int, 120),
    LLM_MAX_EVIDENCE_CHUNKS=(int, 4),
    LLM_MAX_EVIDENCE_CHARS_PER_CHUNK=(int, 1200),
    CONTROLLER_LLM_ENABLED=(bool, False),
    CONTROLLER_LLM_PROVIDER=(str, "subprocess"),
    CONTROLLER_LLM_EXECUTABLE=(str, ""),
    CONTROLLER_LLM_MODEL_PATH=(str, ""),
    CONTROLLER_LLM_DEVICE=(str, "none"),
    # Routing decision with graceful fallback: a slow controller must not hold
    # the request anywhere near as long as answer generation may.
    CONTROLLER_LLM_TIMEOUT_SECONDS=(int, 5),
    # Ask the controller model whether a question that names no standard or artifact is about the
    # standards at all. Off by default; the keyword rules decide when it is off or the call fails.
    RELEVANCE_CHECK_ENABLED=(bool, False),
    RELEVANCE_CHECK_TIMEOUT_SECONDS=(int, 10),
    # Ask the controller model for the model terms a question describes in other words
    # (vocabulary_bridge). Off by default; concept matching uses label words only when off.
    VOCABULARY_BRIDGE_ENABLED=(bool, False),
    VOCABULARY_BRIDGE_TIMEOUT_SECONDS=(int, 3),
    # The classes that own a property the question names ("seat allocation" -> seatAllocationMethod
    # -> PassengerSpotAllocation), see property_terms.
    PROPERTY_TERMS_ENABLED=(bool, True),
    # Answer composition rules in the answer prompt (llm_generator.COMPOSITION_RULE).
    ANSWER_COMPOSITION_ENABLED=(bool, True),
    # Generated NeTEx fragments for "example with values" questions, validated against the XSD
    # (netex_example_generator).
    NETEX_EXAMPLE_GENERATOR_ENABLED=(bool, True),
    NETEX_VALIDATOR_URL=(str, "http://netex-validator:8091"),
    CONTROLLER_LLM_CTX_SIZE=(int, 2048),
    CONTROLLER_LLM_MAX_TOKENS=(int, 96),
    CONTROLLER_LLM_THREADS=(int, 8),
    CONTROLLER_LLM_TEMPERATURE=(float, 0.0),
    CONTROLLER_LLM_API_BASE_URL=(str, ""),
    CONTROLLER_LLM_API_KEY=(str, ""),
    CONTROLLER_LLM_API_MODEL=(str, ""),
    CONTROLLER_LLM_VERIFY_SSL=(bool, True),
    CONTROLLER_LLM_CA_BUNDLE=(str, ""),
    CONTROLLER_LLM_JSON_MODE=(str, ""),
    CONTROLLER_LLM_DISABLE_THINKING=(str, ""),
    CONTROLLER_LLM_REASONING_TOKEN_ALLOWANCE=(str, ""),
    CONTROLLER_LLM_ANTHROPIC_EFFORT=(str, ""),
    SEED_REPO_NETEX=(str, "https://github.com/TransmodelEcosystem/NeTEx"),
    SEED_REPO_SIRI=(str, "https://github.com/TransmodelEcosystem/SIRI"),
    SEED_REPO_OPRA=(str, "https://github.com/TransmodelEcosystem/OpRa"),
    SEED_REPO_MOBILITYDCAT_AP=(str, "https://github.com/mobilityDCAT-AP/mobilityDCAT-AP"),
    SEED_REPO_TNITS=(str, "https://github.com/ERTICO-TN-ITS/TN-ITS-Open"),
    GRAPH_RAG_ENABLED=(bool, True),
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
    RETRIEVAL_LEXICAL_PRESELECT_RESERVE=(int, 8),
    RETRIEVAL_LEXICAL_POOL_SIZE=(int, 8),
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

# Editor sign-in with GitHub (services/editor_accounts.py). With a client id and secret set, the
# anonymous token above carries only the "reader" role (ask questions, give feedback) whatever
# DEV_JWT_DEFAULT_ROLES says, and editorial work needs a signed-in account with roles.
GITHUB_OAUTH_CLIENT_ID = env("GITHUB_OAUTH_CLIENT_ID").strip()
GITHUB_OAUTH_CLIENT_SECRET = env("GITHUB_OAUTH_CLIENT_SECRET").strip()
# The callback registered with the GitHub OAuth app, e.g. https://<host>/napcore-helpdesk/api/v1/auth/github/callback
GITHUB_OAUTH_CALLBACK_URL = env("GITHUB_OAUTH_CALLBACK_URL").strip()
# Where the callback returns the signed-in browser, e.g. https://<host>/napcore-helpdesk/editor
EDITOR_APP_URL = env("EDITOR_APP_URL").strip() or "http://localhost:5173/napcore-helpdesk/editor"
# GitHub logins that become admins on their first sign-in, so the first admin needs no invitation.
EDITOR_ADMIN_GITHUB_LOGINS = {
    login.strip().lower() for login in env("EDITOR_ADMIN_GITHUB_LOGINS").split(",") if login.strip()
}
EDITOR_JWT_TTL_MINUTES = env("EDITOR_JWT_TTL_MINUTES")
DEV_JWT_TTL_MINUTES = env("DEV_JWT_TTL_MINUTES")

ALLOWED_SOURCE_REPOSITORIES = {
    value.strip()
    for value in env(
        "ALLOWED_SOURCE_REPOSITORIES",
        default="https://github.com/TransmodelEcosystem/NeTEx,https://github.com/TransmodelEcosystem/SIRI,https://github.com/TransmodelEcosystem/OpRa",
    ).split(",")
    if value.strip()
}

# The user-facing "slower than usual" banner (GET /api/v1/status) appears once the host's 1-minute load average
# per CPU reaches this value. Retrieval is CPU-bound, so answers slow down from about one runnable task per CPU.
STATUS_BUSY_LOAD_PER_CPU = env.float("STATUS_BUSY_LOAD_PER_CPU", default=1.0)

SOURCE_REFRESH_ENABLED = env("SOURCE_REFRESH_ENABLED")
SOURCE_REFRESH_HOUR = env("SOURCE_REFRESH_HOUR")
SOURCE_REFRESH_MINUTE = env("SOURCE_REFRESH_MINUTE")
SOURCE_CHECKOUT_DIR = env("SOURCE_CHECKOUT_DIR").strip() or "/app/repos"
GITHUB_API_TOKEN = env("GITHUB_API_TOKEN", default="").strip()
GITHUB_API_VERIFY_SSL = env("GITHUB_API_VERIFY_SSL")
GITHUB_CA_BUNDLE = env("GITHUB_CA_BUNDLE", default="").strip() or None

LLM_ENABLED = env("LLM_ENABLED")
LLM_PROVIDER = env("LLM_PROVIDER").strip() or "openai-compatible"
LLM_API_BASE_URL = env("LLM_API_BASE_URL").strip() or "https://api.openai.com/v1"
# Allow reusing a GitHub token for GitHub Models when a dedicated LLM key is not set.
LLM_API_KEY = env("LLM_API_KEY", default="").strip() or GITHUB_API_TOKEN
LLM_MODEL = env("LLM_MODEL").strip() or "gpt-4o-mini"
# The model that names a short question's language (llm_generator._classify_question_language_with_llm).
# Haiku 5.5 calls short Slovenian questions Croatian ("Kako SIRI opisuje zamude?", 5 of 5 runs); Sonnet 5.5
# names them right (2026-11-05). Empty: Sonnet 5.5 with the Anthropic provider, otherwise LLM_MODEL.
LANGUAGE_CLASSIFIER_MODEL = env("LANGUAGE_CLASSIFIER_MODEL", default="").strip() or (
    "claude-sonnet-5-5" if LLM_PROVIDER == "anthropic" else LLM_MODEL
)
LLM_VERIFY_SSL = env("LLM_VERIFY_SSL")
LLM_CA_BUNDLE = env("LLM_CA_BUNDLE", default="").strip() or GITHUB_CA_BUNDLE
LLM_TIMEOUT_SECONDS = env("LLM_TIMEOUT_SECONDS")
LLM_MAX_TOKENS = env("LLM_MAX_TOKENS")
LLM_TEMPERATURE = env("LLM_TEMPERATURE")
# Optional request fields, for gateways that reject them (helpdesk/services/llm_options.py). A managed
# model-as-a-service endpoint may accept only plain non-streaming chat calls: then set JSON_MODE,
# DISABLE_THINKING and STREAMING to False, and give the model's reasoning a token allowance.
LLM_JSON_MODE = env("LLM_JSON_MODE")
LLM_DISABLE_THINKING = env("LLM_DISABLE_THINKING")
LLM_STREAMING = env("LLM_STREAMING")
LLM_REASONING_TOKEN_ALLOWANCE = env("LLM_REASONING_TOKEN_ALLOWANCE")
# LLM_PROVIDER / CONTROLLER_LLM_PROVIDER = "anthropic": Claude through the official SDK
# (helpdesk/services/anthropic_chat.py). LLM_MODEL / CONTROLLER_LLM_API_MODEL then name a Claude model
# (e.g. claude-opus-5-5); base URL and VERIFY_SSL settings are not used. Effort (low|medium|high|xhigh|max)
# sets how much the model thinks before answering; thinking tokens count towards max_tokens.
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY").strip()
_ANTHROPIC_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
LLM_ANTHROPIC_EFFORT = env("LLM_ANTHROPIC_EFFORT").strip().lower() or "low"
if LLM_ANTHROPIC_EFFORT not in _ANTHROPIC_EFFORTS:
    raise ImproperlyConfigured(f"LLM_ANTHROPIC_EFFORT must be one of {sorted(_ANTHROPIC_EFFORTS)}.")
# "hash" (default) or "semantic". Semantic needs the embedding service (compose profile
# "semantic") and every chunk re-embedded with it: hash and semantic vectors cannot be mixed.
EMBEDDING_BACKEND = env("EMBEDDING_BACKEND").strip().lower()
if EMBEDDING_BACKEND not in {"hash", "semantic"}:
    raise ImproperlyConfigured("EMBEDDING_BACKEND must be 'hash' or 'semantic'.")
EMBEDDING_SERVICE_URL = env("EMBEDDING_SERVICE_URL").strip()
EMBEDDING_SERVICE_TIMEOUT_SECONDS = env("EMBEDDING_SERVICE_TIMEOUT_SECONDS")
LLM_MAX_EVIDENCE_CHUNKS = env("LLM_MAX_EVIDENCE_CHUNKS")
LLM_MAX_EVIDENCE_CHARS_PER_CHUNK = env("LLM_MAX_EVIDENCE_CHARS_PER_CHUNK")
CONTROLLER_LLM_ENABLED = env("CONTROLLER_LLM_ENABLED")
CONTROLLER_LLM_PROVIDER = env("CONTROLLER_LLM_PROVIDER", default="subprocess").strip() or "subprocess"
CONTROLLER_LLM_EXECUTABLE = env("CONTROLLER_LLM_EXECUTABLE", default="").strip()
CONTROLLER_LLM_MODEL_PATH = env("CONTROLLER_LLM_MODEL_PATH", default="").strip()
CONTROLLER_LLM_DEVICE = env("CONTROLLER_LLM_DEVICE", default="none").strip() or "none"
CONTROLLER_LLM_TIMEOUT_SECONDS = env("CONTROLLER_LLM_TIMEOUT_SECONDS")
RELEVANCE_CHECK_ENABLED = env("RELEVANCE_CHECK_ENABLED")
RELEVANCE_CHECK_TIMEOUT_SECONDS = env("RELEVANCE_CHECK_TIMEOUT_SECONDS")
VOCABULARY_BRIDGE_ENABLED = env("VOCABULARY_BRIDGE_ENABLED")
VOCABULARY_BRIDGE_TIMEOUT_SECONDS = env("VOCABULARY_BRIDGE_TIMEOUT_SECONDS")
PROPERTY_TERMS_ENABLED = env("PROPERTY_TERMS_ENABLED")
ANSWER_COMPOSITION_ENABLED = env("ANSWER_COMPOSITION_ENABLED")
NETEX_EXAMPLE_GENERATOR_ENABLED = env("NETEX_EXAMPLE_GENERATOR_ENABLED")
NETEX_VALIDATOR_URL = env("NETEX_VALIDATOR_URL").strip()
CONTROLLER_LLM_CTX_SIZE = env("CONTROLLER_LLM_CTX_SIZE")
CONTROLLER_LLM_MAX_TOKENS = env("CONTROLLER_LLM_MAX_TOKENS")
CONTROLLER_LLM_THREADS = env("CONTROLLER_LLM_THREADS")
CONTROLLER_LLM_TEMPERATURE = env("CONTROLLER_LLM_TEMPERATURE")
CONTROLLER_LLM_API_BASE_URL = env("CONTROLLER_LLM_API_BASE_URL", default="").strip() or LLM_API_BASE_URL
CONTROLLER_LLM_API_KEY = env("CONTROLLER_LLM_API_KEY", default="").strip() or LLM_API_KEY
CONTROLLER_LLM_API_MODEL = env("CONTROLLER_LLM_API_MODEL", default="").strip() or LLM_MODEL
CONTROLLER_LLM_VERIFY_SSL = env("CONTROLLER_LLM_VERIFY_SSL")
CONTROLLER_LLM_CA_BUNDLE = env("CONTROLLER_LLM_CA_BUNDLE", default="").strip()


def _bool_or(value: str, fallback: bool) -> bool:
    value = value.strip().lower()
    if not value:
        return fallback
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"Expected a boolean, got {value!r}.")


# Unset: the same as the LLM_* setting, like the controller's base URL, key and model above.
CONTROLLER_LLM_JSON_MODE = _bool_or(env("CONTROLLER_LLM_JSON_MODE"), LLM_JSON_MODE)
CONTROLLER_LLM_DISABLE_THINKING = _bool_or(env("CONTROLLER_LLM_DISABLE_THINKING"), LLM_DISABLE_THINKING)
CONTROLLER_LLM_REASONING_TOKEN_ALLOWANCE = int(
    env("CONTROLLER_LLM_REASONING_TOKEN_ALLOWANCE").strip() or LLM_REASONING_TOKEN_ALLOWANCE
)
CONTROLLER_LLM_ANTHROPIC_EFFORT = env("CONTROLLER_LLM_ANTHROPIC_EFFORT").strip().lower() or LLM_ANTHROPIC_EFFORT
if CONTROLLER_LLM_ANTHROPIC_EFFORT not in _ANTHROPIC_EFFORTS:
    raise ImproperlyConfigured(f"CONTROLLER_LLM_ANTHROPIC_EFFORT must be one of {sorted(_ANTHROPIC_EFFORTS)}.")

SEED_REPO_NETEX = env("SEED_REPO_NETEX").strip() or "https://github.com/TransmodelEcosystem/NeTEx"
SEED_REPO_SIRI = env("SEED_REPO_SIRI").strip() or "https://github.com/TransmodelEcosystem/SIRI"
SEED_REPO_OPRA = env("SEED_REPO_OPRA").strip() or "https://github.com/TransmodelEcosystem/OpRa"
# NAPCORE's metadata profile (CC BY 4.0): its text is indexed and its ontology loaded into GraphDB.
SEED_REPO_MOBILITYDCAT_AP = (
    env("SEED_REPO_MOBILITYDCAT_AP").strip() or "https://github.com/mobilityDCAT-AP/mobilityDCAT-AP"
)
# TN-ITS (CEN/TS 17268, DATEX II Part 14): road attribute updates; schemas, code lists and examples.
SEED_REPO_TNITS = env("SEED_REPO_TNITS").strip() or "https://github.com/ERTICO-TN-ITS/TN-ITS-Open"
ALLOWED_SOURCE_REPOSITORIES |= {
    SEED_REPO_NETEX,
    SEED_REPO_SIRI,
    SEED_REPO_OPRA,
    SEED_REPO_MOBILITYDCAT_AP,
    SEED_REPO_TNITS,
}
# Published Enterprise Architect HTML export of the Transmodel model (issue #151). Transmodel definitions
# in answers link to the class page there by EA GUID; empty keeps the link to transmodel.ttl.
TRANSMODEL_HTML_BASE_URL = env("TRANSMODEL_HTML_BASE_URL").strip().rstrip("/")
# Search a non-English question also in English (llm_generator.english_search_query); off: question only.
SEARCH_TRANSLATION_ENABLED = env("SEARCH_TRANSLATION_ENABLED")
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
RETRIEVAL_LEXICAL_PRESELECT_RESERVE = env("RETRIEVAL_LEXICAL_PRESELECT_RESERVE")
# Text-search matches added to the vector-ranked candidate pool when vectors are semantic
# (retrieval_gateway._lexical_recall_candidates); 0 turns it off.
RETRIEVAL_LEXICAL_POOL_SIZE = env("RETRIEVAL_LEXICAL_POOL_SIZE")
RETRIEVAL_MMR_LAMBDA = env("RETRIEVAL_MMR_LAMBDA")
RETRIEVAL_KEYWORD_TRAP_PENALTY = env("RETRIEVAL_KEYWORD_TRAP_PENALTY")
POLICY_STRICT_CLAIM_GUARD = env("POLICY_STRICT_CLAIM_GUARD")
SEMANTIC_CLUSTER_WINDOW_DAYS = env("SEMANTIC_CLUSTER_WINDOW_DAYS")
SEMANTIC_CLUSTER_MIN_SIZE = env("SEMANTIC_CLUSTER_MIN_SIZE")
SEMANTIC_CLUSTER_SIMILARITY_THRESHOLD = env("SEMANTIC_CLUSTER_SIMILARITY_THRESHOLD")
SEMANTIC_CLUSTER_MAX_EVENTS = env("SEMANTIC_CLUSTER_MAX_EVENTS")

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")

# With DEBUG off, Django sends request errors (500s) only to mail_admins, which is not configured, so
# their tracebacks went nowhere. Print them to stderr, where `docker compose logs backend` shows them.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False}},
}

# The daily source refresh runs at SOURCE_REFRESH_HOUR:SOURCE_REFRESH_MINUTE UTC, only when enabled.
CELERY_BEAT_SCHEDULE = build_beat_schedule(
    refresh_enabled=SOURCE_REFRESH_ENABLED,
    hour=SOURCE_REFRESH_HOUR,
    minute=SOURCE_REFRESH_MINUTE,
)
