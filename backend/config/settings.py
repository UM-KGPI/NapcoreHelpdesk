from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DJANGO_DEBUG=(bool, True),
    # Keep SQLite fallback for local tests; production/staging should set this to False.
    DJANGO_USE_SQLITE=(bool, True),
    JWT_SECRET_KEY=(str, "change-me-jwt-secret-key-at-least-32-bytes"),
    JWT_ALGORITHM=(str, "HS256"),
    JWT_ISSUER=(str, ""),
    JWT_AUDIENCE=(str, ""),
    DEV_JWT_AUTO_ISSUE=(bool, True),
    DEV_JWT_DEFAULT_SUBJECT=(str, "user-local"),
    DEV_JWT_DEFAULT_ROLES=(str, "editor,reviewer,publisher"),
    DEV_JWT_TTL_MINUTES=(int, 480),
    ALLOWED_SOURCE_REPOSITORIES=(str, "https://github.com/NeTEx-CEN/NeTEx"),
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
    LLM_MAX_TOKENS=(int, 500),
    LLM_TEMPERATURE=(float, 0.2),
    EMBEDDING_ENABLED=(bool, False),
    EMBEDDING_PROVIDER=(str, "openai-compatible"),
    EMBEDDING_API_BASE_URL=(str, "https://api.openai.com/v1"),
    EMBEDDING_API_KEY=(str, ""),
    EMBEDDING_MODEL=(str, "text-embedding-3-small"),
    EMBEDDING_TIMEOUT_SECONDS=(int, 30),
    GRAPH_RAG_ENABLED=(bool, False),
    GRAPH_RAG_VARIANT=(str, "baseline"),
    NEO4J_ENABLED=(bool, False),
    NEO4J_URI=(str, ""),
    NEO4J_USER=(str, "neo4j"),
    NEO4J_PASSWORD=(str, ""),
    NEO4J_DATABASE=(str, "neo4j"),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="change-me")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.postgres",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "helpdesk",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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

if env("DJANGO_USE_SQLITE"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
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
    for value in env("ALLOWED_SOURCE_REPOSITORIES", default="https://github.com/NeTEx-CEN/NeTEx").split(",")
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

EMBEDDING_ENABLED = env("EMBEDDING_ENABLED")
EMBEDDING_PROVIDER = env("EMBEDDING_PROVIDER").strip() or "openai-compatible"
EMBEDDING_API_BASE_URL = env("EMBEDDING_API_BASE_URL").strip() or "https://api.openai.com/v1"
EMBEDDING_API_KEY = env("EMBEDDING_API_KEY").strip()
EMBEDDING_MODEL = env("EMBEDDING_MODEL").strip() or "text-embedding-3-small"
EMBEDDING_TIMEOUT_SECONDS = env("EMBEDDING_TIMEOUT_SECONDS")
GRAPH_RAG_ENABLED = env("GRAPH_RAG_ENABLED")
NEO4J_ENABLED = env("NEO4J_ENABLED")
NEO4J_URI = env("NEO4J_URI", default="").strip()
NEO4J_USER = env("NEO4J_USER", default="neo4j").strip() or "neo4j"
NEO4J_PASSWORD = env("NEO4J_PASSWORD", default="").strip()
NEO4J_DATABASE = env("NEO4J_DATABASE", default="neo4j").strip() or "neo4j"

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")

CELERY_BEAT_SCHEDULE = {
    "helpdesk-reindex-default-repository-daily": {
        "task": "helpdesk.reindex_default_repository",
        "schedule": 60 * 60 * 24,
    }
}
