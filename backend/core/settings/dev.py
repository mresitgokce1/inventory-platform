from .base import *

# Development settings
DEBUG = True

# Allow testserver for testing
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
