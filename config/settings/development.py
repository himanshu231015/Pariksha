from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Optional PostgreSQL configuration if specified in .env
if os.getenv("USE_POSTGRES", "False").lower() in ("true", "1", "yes"):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "pariksha_db"),
        "USER": os.getenv("DB_USER", "pariksha_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }

# Development email backend: prints emails to console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
