import tempfile

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False
SECRET_KEY = "test-secret-key-that-is-long-enough-for-hs256"
DATABASES = {"default": env.db("TEST_DATABASE_URL", default="sqlite:///:memory:")}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
PAYMENT_GATEWAY = "fake"
MEDIA_ROOT = tempfile.mkdtemp(prefix="store-media-")
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {"anon": "1000/min", "user": "1000/min", "otp": "1000/min", "payments": "1000/min"},
}
