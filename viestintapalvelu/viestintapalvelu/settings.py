import hashlib
import os
import sys

from pathlib import Path
from datetime import timedelta
from logging.handlers import SysLogHandler

from viestintapalvelu.filters import DisableLoggingInTestingFilter


# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent

BASE_URL = os.getenv("BASE_URL", "viestintapalvelu/")


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-ia1ex-id^$az(zdke^a+$a7#l+7tw+q1gpgw&zk9o9gkvz*3+$")

PRODUCTION_ENV = os.getenv("PRODUCTION_ENV", "false").lower() in ("true", "1")
QA_ENV = os.getenv("QA_ENV", "false").lower() in ("true", "1")

ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

# SECURITY WARNING: do not run with debug turned on in production!
DEBUG = not (PRODUCTION_ENV or QA_ENV)


ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",") if os.getenv("ALLOWED_HOSTS") else []

APPEND_SLASH = False

# token obtain ratelimits
TOKEN_RATELIMIT_PER_MINUTE = int(os.getenv("TOKEN_RATELIMIT_PER_MINUTE", 10))
TOKEN_RATELIMIT_PER_HOUR = int(os.getenv("TOKEN_RATELIMIT_PER_HOUR", 50))


# Application definition

INSTALLED_APPS = [
    "kyselyt.apps.KyselytConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_celery_results",
    "django_celery_beat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "token_resolved.middleware.AddTokenHeaderMiddleware",
]

ROOT_URLCONF = "viestintapalvelu.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "viestintapalvelu.wsgi.application"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
}


# Cross Site Request Forgery protection (CSRF/XSRF)
CSRF_FORCE_ENABLED = PRODUCTION_ENV or QA_ENV
CSRF_COOKIE_NAME = "viestintapalvelu_csrftoken"
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS").split(",") if os.getenv("CSRF_TRUSTED_ORIGINS") else []


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

def get_test_db_name():
    md5 = hashlib.md5()
    md5.update(os.getenv("CI_JOB_ID", "no-tag").encode("utf-8"))
    return md5.hexdigest()


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "valssi_db"),
        "USER": os.getenv("POSTGRES_USER", "valssi_admin"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "localhero"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "TEST": {
            "NAME": get_test_db_name(),
        },
    }
}

TESTING = sys.argv[1:2] == ["test"]


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Django logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "testing": {
            "()": DisableLoggingInTestingFilter
        },
    },
    "formatters": {
        "verbose": {
            "format": "{asctime} viestintapalvelu [{levelname}] {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d_%H-%M-%S",
        },
        "simple": {
            "format": "[{asctime}] [{levelname}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "filters": ["testing"]
        },
        "syslog": {
            "level": "INFO",
            "class": "logging.handlers.SysLogHandler",
            "facility": SysLogHandler.LOG_LOCAL1,
            "address": ["127.0.0.1", 1514],
            "formatter": "verbose"
        },
    },
    "root": {
        "handlers": ["syslog", "console"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "": {
            "handlers": ["syslog", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["syslog", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery.beat": {
            "handlers": ["syslog", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["syslog", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "level": "INFO",
            "handlers": ["syslog", "console"],
            "propagate": False,
        },
        "django.security": {
            "level": "INFO",
            "handlers": ["syslog"],
            "propagate": False,
        },
        "django.server": {
            "level": "INFO",
            "handlers": ["syslog", "console"],
            "propagate": False,
        },
        "viestintapalvelu.celery": {
            "handlers": ["syslog", "console"],
            "level": "INFO",
            "propagate": False,
        }
    }
}


# Celery Configuration Options
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "virtual_host")
BROKER_ADDRESS = os.getenv("RABBITMQ_HOST", "localhost") + ":5672/" + RABBITMQ_VHOST
BROKER_USERNAME = os.getenv("BROKER_USERNAME", None)
BROKER_PASSWORD = os.getenv("BROKER_PASSWORD", None)
CELERY_BROKER_URL = f"amqp://{BROKER_USERNAME}:{BROKER_PASSWORD}@{BROKER_ADDRESS}" if (
    BROKER_USERNAME and BROKER_PASSWORD) else f"amqp://{BROKER_ADDRESS}"
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_DEFAULT_QUEUE = f"viestintapalvelu_queue_{ENVIRONMENT}"
if TESTING:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True


# Email settings
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "no-reply@karvi.fi")


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = f"/{BASE_URL}static/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Opintopolku
OPINTOPOLKU_URL = os.getenv("OPINTOPOLKU_URL", "https://virkailija.testiopintopolku.fi")
OPINTOPOLKU_USERNAME = os.getenv("OPINTOPOLKU_USERNAME", "username")
OPINTOPOLKU_PASSWORD = os.getenv("OPINTOPOLKU_PASSWORD", "password")

EMAIL_SERVICE = "ryhmasahkoposti-service"
EMAIL_SERVICE_URL = f"{OPINTOPOLKU_URL}/{EMAIL_SERVICE}/"
EMAIL_SERVICE_TIMEOUT = 3  # seconds


VASTAAJA_UI_URL = os.getenv("VASTAAJA_UI_URL", "http://localhost:3000/vastaaja-ui/")

# Django-session
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "viestintapalvelu_sessionid"
SESSION_COOKIE_AGE = 36000  # 10 hours
SESSION_COOKIE_PATH = "/viestintapalvelu"
