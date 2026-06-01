from .base import *  # noqa: F403

DEBUG = False

ALLOWED_HOSTS = os.environ.get(  # noqa: F405
    "ALLOWED_HOSTS", "localhost"
).split(",")

MIDDLEWARE.insert(  # noqa: F405
    1, "whitenoise.middleware.WhiteNoiseMiddleware"
)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Supabase PostgreSQL — overrides base.py DATABASES
SUPABASE_URL = os.environ.get("SUPABASE_URL")  # noqa: F405
SUPABASE_DB_PASSWORD = os.environ.get("SUPABASE_DB_PASSWORD")  # noqa: F405

if SUPABASE_URL and SUPABASE_DB_PASSWORD:
    DATABASES = {  # noqa: F405
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("SUPABASE_DB_NAME", "postgres"),  # noqa: F405
            "USER": os.environ.get("SUPABASE_DB_USER", "postgres"),  # noqa: F405
            "PASSWORD": SUPABASE_DB_PASSWORD,
            "HOST": SUPABASE_URL,
            "PORT": os.environ.get("SUPABASE_DB_PORT", "5432"),  # noqa: F405
            "OPTIONS": {"sslmode": "require"},
        }
    }

SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True") == "True"  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = os.environ.get(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS", "https://*.example.com"
).split(",")
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",  # noqa: F405
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
}
