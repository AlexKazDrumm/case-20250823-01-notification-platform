import os
from pathlib import Path
from dotenv import load_dotenv
from os import getenv

load_dotenv()

CELERY_EAGER = getenv("CELERY_EAGER", "0") in ("1", "true", "True")
CACHEOPS_ENABLED = getenv("CACHEOPS_ENABLED", "0") in ("1", "true", "True")

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure")
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")
TIME_ZONE = os.getenv("DJANGO_TIMEZONE", "UTC")
USE_TZ = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "strawberry.django",
    "drf_spectacular",
    "cacheops",
    "rest_framework.authtoken",
    "django_prometheus",
    "accounts",
    "notifications",
    "dashboard",
]

if CACHEOPS_ENABLED:
    INSTALLED_APPS += ["cacheops"]
    CACHEOPS = {"*.*": {"ops": "all", "timeout": 60*15}}
    CACHEOPS_REDIS = os.getenv("CACHEOPS_REDIS", "redis://localhost:6379/3")

if CELERY_EAGER:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "app.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "notification_hub"),
        "USER": os.getenv("POSTGRES_USER", "notification_hub"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "notification_hub"),
        "HOST": os.getenv("POSTGRES_HOST", ""),
        "PORT": int(os.getenv("POSTGRES_PORT", "5432")),
    }
}
if not DATABASES["default"]["HOST"]:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_PASSWORD_VALIDATORS = []

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": os.getenv("THROTTLE_USER_RATE", "60/min"),
        "anon": os.getenv("THROTTLE_ANON_RATE", "10/min"),
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Notification Hub Notifications API",
    "VERSION": "1.0.0",
}

# Email
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("SMTP_HOST", "")
EMAIL_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_HOST_USER = os.getenv("SMTP_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("SMTP_USE_TLS", "1") == "1"
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_FROM", "no-reply@example.com")

# Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
CELERY_TASK_DEFAULT_QUEUE = os.getenv("CELERY_TASK_DEFAULT_QUEUE", "default")
CELERY_TASK_TIME_LIMIT = 60
CELERY_TASK_SOFT_TIME_LIMIT = 50

# Cacheops
CACHEOPS_REDIS = os.getenv("CACHEOPS_REDIS", "redis://localhost:6379/3")
CACHEOPS = {
    "auth.*": {"ops": "all", "timeout": 60*60},
    "notifications.*": {"ops": "all", "timeout": 60*5},
}

DEFAULT_CHANNELS_ORDER = [c.strip() for c in os.getenv("DEFAULT_CHANNELS_ORDER", "telegram,email,sms").split(",") if c.strip()]

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# SMS
SMS_PROVIDER = os.getenv("SMS_PROVIDER", "mock")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")

# Custom user
AUTH_USER_MODEL = "accounts.User"

# Prometheus metrics
PROMETHEUS_EXPORT_MIGRATIONS = False

# OpenTelemetry (optional)
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "notification_hub-notifications")
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")

# Celery queues and routes
from kombu import Queue
CELERY_TASK_QUEUES = (
    Queue("default"),
    Queue("email"),
    Queue("sms"),
    Queue("telegram"),
)
CELERY_TASK_ROUTES = { 
    "notifications.tasks.send_via_channel": {"queue": "default"},  # dynamic per arg
}

# Idempotency / dedupe
IDEMPOTENCY_WINDOW_SEC = int(os.getenv("IDEMPOTENCY_WINDOW_SEC", "3600"))

# AWS
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_SES_SENDER = os.getenv("AWS_SES_SENDER", DEFAULT_FROM_EMAIL)
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "django")  # django | ses

# Second pass fallback
SECOND_PASS_ENABLED = os.getenv("SECOND_PASS_ENABLED", "1") == "1"
