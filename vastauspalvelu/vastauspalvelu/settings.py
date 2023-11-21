import hashlib
import os
import sys

from logging.handlers import SysLogHandler
from pathlib import Path

from vastauspalvelu.filters import DisableLoggingInTestingFilter


# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent

BASE_URL = os.getenv("BASE_URL", "vastauspalvelu/")


TESTING = (sys.argv[1:2] == ["test"]) or (os.getenv("TESTING", "false").lower() in ("true", "1"))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-&znem2pl0v4^_wdi+y$q5vg$p^1y6(s29z3z3c6(hi7nilk14x")

PRODUCTION_ENV = os.getenv("PRODUCTION_ENV", "false").lower() in ("true", "1")
QA_ENV = os.getenv("QA_ENV", "false").lower() in ("true", "1")

ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

# SECURITY WARNING: do not run with debug turned on in production!
DEBUG = not (PRODUCTION_ENV or QA_ENV)


ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",") if os.getenv("ALLOWED_HOSTS") else []

APPEND_SLASH = False


if TESTING:
    VIRKAILIJAPALVELU_URL = "http://virkailijapalvelu-test-url"
    VIESTINTAPALVELU_URL = "http://viestintapalvelu-test-url"
else:
    VIRKAILIJAPALVELU_URL = os.getenv("VIRKAILIJAPALVELU_URL", "http://localhost:3000/virkailijapalvelu")
    VIESTINTAPALVELU_URL = os.getenv("VIESTINTAPALVELU_URL", "http://localhost:3000/viestintapalvelu")
VIRKAILIJAPALVELU_AUTH_USER = os.getenv("VIRKAILIJAPALVELU_AUTH_USER", "vastauspalvelu-auth")
VIRKAILIJAPALVELU_AUTH_PW = os.getenv("VIRKAILIJAPALVELU_AUTH_PW", "localhero")
VIESTINTAPALVELU_AUTH_USER = os.getenv("VIESTINTAPALVELU_AUTH_USER", "vastauspalvelu-auth")
VIESTINTAPALVELU_AUTH_PW = os.getenv("VIESTINTAPALVELU_AUTH_PW", "localhero")

VIRKAILIJAPALVELU_TIMEOUT = 3  # seconds
VIESTINTAPALVELU_TIMEOUT = 3  # seconds


# ratelimits
RATELIMIT_PER_MINUTE = int(os.getenv("RATELIMIT_PER_MINUTE", 20))
RATELIMIT_PER_HOUR = int(os.getenv("RATELIMIT_PER_HOUR", 50))
RATELIMIT_USE_CACHE = "redis"
RATELIMIT_FAIL_OPEN = True
REDIS_URL = os.getenv("REDIS_URL", "localhost")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_AUTH = f":{REDIS_PASSWORD}@" if REDIS_PASSWORD else ""


# Application definition

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "redis": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_AUTH}{REDIS_URL}:6379/0",
    }
}

INSTALLED_APPS = [
    "kyselyt.apps.KyselytConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "django_celery_results",
    "django_celery_beat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "token_resolved.middleware.AddTokenHeaderMiddleware",
]

ROOT_URLCONF = "vastauspalvelu.urls"

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

WSGI_APPLICATION = "vastauspalvelu.wsgi.application"

# Access-Control-Allow-Origin
# https://github.com/ottoyiu/django-cors-headers/
if not QA_ENV and not PRODUCTION_ENV:
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS").split(",") \
        if os.getenv("CORS_ALLOWED_ORIGINS") else ["http://localhost:3000", "https://localhost:3000"]


# Cross Site Request Forgery protection (CSRF/XSRF)
CSRF_FORCE_ENABLED = PRODUCTION_ENV or QA_ENV
CSRF_COOKIE_NAME = "vastauspalvelu_csrftoken"
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS").split(",") if os.getenv("CSRF_TRUSTED_ORIGINS") else []


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

def get_test_db_name():
    md5 = hashlib.md5()
    md5.update(os.getenv("CI_JOB_ID", "no-tag").encode("utf-8"))
    return md5.hexdigest()


DATABASE_ROUTERS = ("kyselyt.dbrouters.VastauspalveluRouter",)
DATABASE_APPS_MAPPING = {
    "admin": "default",
    "auth": "default",
    "contenttypes": "default",
    "django_celery_results": "default",
    "sessions": "default",
    "kyselyt": "valssi", }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {
            "options": "-c search_path=vastauspalvelu"
        },
        "NAME": os.getenv("POSTGRES_DB", "valssi_db"),
        "USER": os.getenv("POSTGRES_USER", "valssi_admin"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "localhero"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "TEST": {
            "NAME": get_test_db_name(),
        },
    },
    "valssi": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB_VALSSI", os.getenv("POSTGRES_DB", "valssi_db")),
        "USER": os.getenv("POSTGRES_USER_VALSSI", os.getenv("POSTGRES_USER", "valssi_admin")),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD_VALSSI", os.getenv("POSTGRES_PASSWORD", "localhero")),
        "HOST": os.getenv("POSTGRES_HOST_VALSSI", os.getenv("POSTGRES_HOST", "127.0.0.1")),
        "PORT": os.getenv("POSTGRES_PORT_VALSSI", os.getenv("POSTGRES_PORT", "5432")),
        "TEST": {
            "NAME": get_test_db_name(),
            "DEPENDENCIES": [],
        },
    }
}

if TESTING:
    DATABASES["default"]["OPTIONS"]["options"] += ",public"


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
            "format": "{asctime} vastauspalvelu [{levelname}] {message}",
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
        "vastauspalvelu.celery": {
            "handlers": ["syslog", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "fontTools": {
            "handlers": ["syslog", "console"],
            "level": "ERROR",
            "propagate": False,
        },
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
CELERY_TASK_DEFAULT_QUEUE = f"vastauspalvelu_queue_{ENVIRONMENT}"
if TESTING:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True


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


OPINTOPOLKU_URL = os.getenv("OPINTOPOLKU_URL", "https://virkailija.testiopintopolku.fi")

LOCALISATION_SERVICE = "lokalisointi"
LOCALISATION_SERVICE_URL = f"{OPINTOPOLKU_URL}/{LOCALISATION_SERVICE}/cxf/rest/v1/"
LOCALISATION_SERVICE_TIMEOUT = 3  # seconds
LOCALISATION_ENDPOINT = LOCALISATION_SERVICE_URL + "localisation"

# Django-session
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "vastauspalvelu_sessionid"
SESSION_COOKIE_AGE = 36000  # 10 hours
SESSION_COOKIE_PATH = "/vastauspalvelu"
