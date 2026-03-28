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
    ALLOWED_SOURCE_REPOSITORIES=(str, "https://github.com/NeTEx-CEN/NeTEx"),
    INDEX_SCHEDULE_REPO_URL=(str, ""),
    INDEX_SCHEDULE_REPO_PATH=(str, ""),
    INDEX_SCHEDULE_PROFILE=(str, "netex"),
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

ALLOWED_SOURCE_REPOSITORIES = {
    value.strip()
    for value in env("ALLOWED_SOURCE_REPOSITORIES", default="https://github.com/NeTEx-CEN/NeTEx").split(",")
    if value.strip()
}

INDEX_SCHEDULE_REPO_URL = env("INDEX_SCHEDULE_REPO_URL").strip()
INDEX_SCHEDULE_REPO_PATH = env("INDEX_SCHEDULE_REPO_PATH").strip()
INDEX_SCHEDULE_PROFILE = env("INDEX_SCHEDULE_PROFILE", default="netex").strip() or "netex"

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")

CELERY_BEAT_SCHEDULE = {
    "helpdesk-reindex-default-repository-daily": {
        "task": "helpdesk.reindex_default_repository",
        "schedule": 60 * 60 * 24,
    }
}
