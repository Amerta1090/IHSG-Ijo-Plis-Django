import dj_database_url  # noqa: F405

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

DATABASE_URL = os.environ.get("DATABASE_URL")  # noqa: F405

if DATABASE_URL:
    DATABASES["default"] = dj_database_url.parse(  # noqa: F405
        DATABASE_URL, conn_max_age=600, ssl_require=True
    )

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
