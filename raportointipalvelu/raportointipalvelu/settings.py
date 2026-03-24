import hashlib
import os
import sys

from datetime import timedelta
from pathlib import Path
from corsheaders.defaults import default_headers

from raportointipalvelu.filters import DisableLoggingInTestingFilter, AddProgramnameFilter


# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent

BASE_URL = os.getenv("BASE_URL", "raportointipalvelu/")


TESTING = (sys.argv[1:2] == ["test"]) or (os.getenv("TESTING", "false").lower() in ("true", "1"))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-8oxgjab5l*2z7kg@cza7f9equ*(evczhi_xie(8180v$b510#b")

PRODUCTION_ENV = os.getenv("PRODUCTION_ENV", "false").lower() in ("true", "1")
QA_ENV = os.getenv("QA_ENV", "false").lower() in ("true", "1")
TEST_ENV = os.getenv("TEST_ENV", "false").lower() in ("true", "1")
LOCAL_ENV = os.getenv("LOCAL_ENV", "false").lower() in ("true", "1")

ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

# SECURITY WARNING: do not run with debug turned on in production!
DEBUG = not (PRODUCTION_ENV or QA_ENV)

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",") if os.getenv("ALLOWED_HOSTS") else []

APPEND_SLASH = False

# token obtain ratelimits
RATELIMIT_PER_MINUTE = int(os.getenv("RATELIMIT_PER_MINUTE", 10))
RATELIMIT_PER_HOUR = int(os.getenv("RATELIMIT_PER_HOUR", 50))

# jwt tokens lifetimes
JWT_ACCESS_TOKEN_LIFETIME_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 5))
JWT_REFRESH_TOKEN_LIFETIME_HOURS = int(os.getenv("JWT_REFRESH_TOKEN_LIFETIME_HOURS", 10))


# Application definition

INSTALLED_APPS = [
    "raportointi.apps.RaportointiConfig",
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
    "django_cas_ng",
    "rest_framework_simplejwt.token_blacklist",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "token_resolved.middleware.AddTokenHeaderMiddleware",
]

ROOT_URLCONF = "raportointipalvelu.urls"

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

WSGI_APPLICATION = "raportointipalvelu.wsgi.application"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=JWT_ACCESS_TOKEN_LIFETIME_MINUTES),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=JWT_REFRESH_TOKEN_LIFETIME_HOURS),

    # jwt cookie
    "AUTH_COOKIE_DOMAIN": None,
    "AUTH_COOKIE_SECURE": PRODUCTION_ENV or QA_ENV or TEST_ENV,
    "AUTH_COOKIE_HTTP_ONLY": False,
    "AUTH_COOKIE_PATH": "/",
    "AUTH_COOKIE_SAMESITE": "Lax" if (PRODUCTION_ENV or QA_ENV or LOCAL_ENV) else "None",
}

# Access-Control-Allow-Origin
# https://github.com/ottoyiu/django-cors-headers/
if not QA_ENV and not PRODUCTION_ENV:
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS").split(",") \
        if os.getenv("CORS_ALLOWED_ORIGINS") else ["http://localhost:3000", "https://localhost:3000"]
    CORS_ALLOW_HEADERS = [
        *default_headers,
        "X-Raportointipalvelu-Access-Token",
        "X-Raportointipalvelu-Refresh-Token",
        "Impersonate-Organization",
        "Impersonate-User"]
    CORS_EXPOSE_HEADERS = [
        *default_headers,
        "X-Raportointipalvelu-Access-Token",
        "X-Raportointipalvelu-Refresh-Token",
        "Impersonate-Organization",
        "Impersonate-User"]


# Cross Site Request Forgery protection (CSRF/XSRF)
CSRF_FORCE_ENABLED = PRODUCTION_ENV or QA_ENV
CSRF_COOKIE_NAME = "raportointipalvelu_csrftoken"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS").split(",") if os.getenv("CSRF_TRUSTED_ORIGINS") else []


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

def get_test_db_name():
    md5 = hashlib.md5()
    md5.update(os.getenv("CI_JOB_ID", "no-tag").encode("utf-8"))
    return "aa_rap_" + md5.hexdigest()[:8]


DATABASE_ROUTERS = ("raportointi.dbrouters.RaportointipalveluRouter",)

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
    },
    "vastauspalvelu": {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {
            "options": "-c search_path=vastauspalvelu"
        },
        "NAME": os.getenv("VASTAUSPALVELU_POSTGRES_DB", os.getenv("POSTGRES_DB_VALSSI", "valssi_db")),
        "USER": os.getenv("VASTAUSPALVELU_POSTGRES_USER", os.getenv("POSTGRES_USER_VALSSI", "valssi_admin")),
        "PASSWORD": os.getenv("VASTAUSPALVELU_POSTGRES_PASSWORD", os.getenv("POSTGRES_PASSWORD_VALSSI", "localhero")),
        "HOST": os.getenv("VASTAUSPALVELU_POSTGRES_HOST", os.getenv("POSTGRES_HOST_VALSSI", "127.0.0.1")),
        "PORT": os.getenv("VASTAUSPALVELU_POSTGRES_PORT", os.getenv("POSTGRES_PORT_VALSSI", "5432")),
        "TEST": {
            "NAME": get_test_db_name(),
            "DEPENDENCIES": [],
        },
    },
    "virkailijapalvelu": {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {
            "options": "-c search_path=virkailijapalvelu"
        },
        "NAME": os.getenv("VIRKAILIJAPALVELU_POSTGRES_DB", os.getenv("POSTGRES_DB_VALSSI", "valssi_db")),
        "USER": os.getenv("VIRKAILIJAPALVELU_POSTGRES_USER", os.getenv("POSTGRES_USER_VALSSI", "valssi_admin")),
        "PASSWORD": os.getenv("VIRKAILIJAPALVELU_POSTGRES_PASSWORD", os.getenv("POSTGRES_PASSWORD_VALSSI", "localhero")),
        "HOST": os.getenv("VIRKAILIJAPALVELU_POSTGRES_HOST", os.getenv("POSTGRES_HOST_VALSSI", "127.0.0.1")),
        "PORT": os.getenv("VIRKAILIJAPALVELU_POSTGRES_PORT", os.getenv("POSTGRES_PORT_VALSSI", "5432")),
        "TEST": {
            "NAME": get_test_db_name(),
            "DEPENDENCIES": [],
        },
    },
}

if TESTING:
    DATABASES["vastauspalvelu"]["OPTIONS"]["options"] += ",public"
    DATABASES["virkailijapalvelu"]["OPTIONS"]["options"] += ",public"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "django_cas_ng.backends.CASBackend",
)

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
        "add_programname": {
            "()": AddProgramnameFilter
        },
    },
    "formatters": {
        "simple": {
            "format": "{asctime} {levelname} {programname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "filters": ["testing", "add_programname"]
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery.beat": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "django.security": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "django.server": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "raportointipalvelu.celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "fontTools": {
            "handlers": ["console"],
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
CELERY_TASK_DEFAULT_QUEUE = f"raportointipalvelu_queue_{ENVIRONMENT}"
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

# Permissions levels & Organisations
OPINTOPOLKU_URL = os.getenv("OPINTOPOLKU_URL", "https://virkailija.testiopintopolku.fi")

OPINTOPOLKU_USERNAME = os.getenv("OPINTOPOLKU_USERNAME", "username")
OPINTOPOLKU_PASSWORD = os.getenv("OPINTOPOLKU_PASSWORD", "password")

KAYTTOOIKEUS_SERVICE = "kayttooikeus-service"
KAYTTOOIKEUS_SERVICE_URL = f"{OPINTOPOLKU_URL}/{KAYTTOOIKEUS_SERVICE}/"
KAYTTOOIKEUS_SERVICE_TIMEOUT = 3  # seconds

# CAS-authentication (Valssi autentikointipalvelu)
CAS_SERVER_URL = os.getenv("CAS_SERVER_URL", "https://valssi-test-1.2.rahtiapp.fi") + "/cas/"
CAS_CREATE_USER = True
CAS_LOGIN_MSG = None
CAS_LOGGED_MSG = None
CAS_VERSION = 3
CAS_RETRY_LOGIN = False
if PRODUCTION_ENV or QA_ENV:
    CAS_FORCE_SSL_SERVICE_URL = True
    CAS_IGNORE_REFERER = True
    CAS_REDIRECT_URL = "/virkailija-ui/"
CAS_CHECK_NEXT = not DEBUG

# Django-session
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "raportointipalvelu_sessionid"
SESSION_COOKIE_AGE = 36000  # 10 hours
SESSION_COOKIE_PATH = "/raportointipalvelu"
