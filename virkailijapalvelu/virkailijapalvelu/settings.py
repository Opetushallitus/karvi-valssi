import hashlib
import os
import sys

from datetime import timedelta
from logging.handlers import SysLogHandler
from pathlib import Path

from virkailijapalvelu.filters import DisableLoggingInTestingFilter


# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent

BASE_URL = os.getenv("BASE_URL", "virkailijapalvelu/")


TESTING = (sys.argv[1:2] == ["test"]) or (os.getenv("TESTING", "false").lower() in ("true", "1"))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-hd_@wk1r$!e7hr#h$fhb(lt1_l2)8e&z%9=(9k&$5bg0=p9jm#")

PRODUCTION_ENV = os.getenv("PRODUCTION_ENV", "false").lower() in ("true", "1")
QA_ENV = os.getenv("QA_ENV", "false").lower() in ("true", "1")
TEST_ENV = os.getenv("TEST_ENV", "false").lower() in ("true", "1")

ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

# SECURITY WARNING: do not run with debug turned on in production!
DEBUG = not (PRODUCTION_ENV or QA_ENV)

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",") if os.getenv("ALLOWED_HOSTS") else []

APPEND_SLASH = False

if TESTING:
    VIESTINTAPALVELU_URL = "http://viestintapalvelu-test-url"
else:
    VIESTINTAPALVELU_URL = os.getenv("VIESTINTAPALVELU_URL", "http://127.0.0.1:5000")
VIESTINTAPALVELU_AUTH_USER = os.getenv("VIESTINTAPALVELU_AUTH_USER", "virkailijapalvelu-auth")
VIESTINTAPALVELU_AUTH_PW = os.getenv("VIESTINTAPALVELU_AUTH_PW", "localhero")

VIESTINTAPALVELU_TIMEOUT = 3  # seconds

# token obtain ratelimits
TOKEN_RATELIMIT_PER_MINUTE = int(os.getenv("TOKEN_RATELIMIT_PER_MINUTE", 10))
TOKEN_RATELIMIT_PER_HOUR = int(os.getenv("TOKEN_RATELIMIT_PER_HOUR", 50))

# jwt tokens lifetimes
JWT_ACCESS_TOKEN_LIFETIME_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 5))
JWT_REFRESH_TOKEN_LIFETIME_HOURS = int(os.getenv("JWT_REFRESH_TOKEN_LIFETIME_HOURS", 10))


# Application definition

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

ROOT_URLCONF = "virkailijapalvelu.urls"

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

WSGI_APPLICATION = "virkailijapalvelu.wsgi.application"

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
    "AUTH_COOKIE_SAMESITE": "Lax" if (PRODUCTION_ENV or QA_ENV) else "None",
}


# Access-Control-Allow-Origin
# https://github.com/ottoyiu/django-cors-headers/
if not QA_ENV and not PRODUCTION_ENV:
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS").split(",") \
        if os.getenv("CORS_ALLOWED_ORIGINS") else ["http://localhost:3000", "https://localhost:3000"]
    CORS_EXPOSE_HEADERS = [
        "X-Virkailijapalvelu-Access-Token",
        "X-Virkailijapalvelu-Refresh-Token",
        "Impersonate-Organization",
        "Impersonate-User"]


# Cross Site Request Forgery protection (CSRF/XSRF)
CSRF_FORCE_ENABLED = PRODUCTION_ENV or QA_ENV
CSRF_COOKIE_NAME = "virkailijapalvelu_csrftoken"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS").split(",") if os.getenv("CSRF_TRUSTED_ORIGINS") else []


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

def get_test_db_name():
    md5 = hashlib.md5()
    md5.update(os.getenv("CI_JOB_ID", "no-tag").encode("utf-8"))
    return md5.hexdigest()


DATABASE_ROUTERS = ("kyselyt.dbrouters.VirkailijapalveluRouter",)
DATABASE_APPS_MAPPING = {
    "admin": "default",
    "auth": "default",
    "contenttypes": "default",
    "django_cas_ng": "default",
    "django_celery_beat": "default",
    "django_celery_results": "default",
    "sessions": "default",
    "token_blacklist": "default",
    "kyselyt": "valssi", }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {
            "options": "-c search_path=virkailijapalvelu"
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
    },
    "formatters": {
        "verbose": {
            "format": "{asctime} virkailijapalvelu [{levelname}] {message}",
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
        "virkailijapalvelu.celery": {
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
CELERY_TASK_DEFAULT_QUEUE = f"virkailijapalvelu_queue_{ENVIRONMENT}"
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


# CAS-authentication (Valssi autentikointipalvelu)
CAS_SERVER_URL = os.getenv("CAS_SERVER_URL", "https://valssi-qa.rahtiapp.fi") + "/cas/"
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

OPINTOPOLKU_URL = os.getenv("OPINTOPOLKU_URL", "https://virkailija.testiopintopolku.fi")

OPINTOPOLKU_USERNAME = os.getenv("OPINTOPOLKU_USERNAME", "username")
OPINTOPOLKU_PASSWORD = os.getenv("OPINTOPOLKU_PASSWORD", "password")

KAYTTOOIKEUS_SERVICE = "kayttooikeus-service"
KAYTTOOIKEUS_SERVICE_URL = f"{OPINTOPOLKU_URL}/{KAYTTOOIKEUS_SERVICE}/"
KAYTTOOIKEUS_SERVICE_TIMEOUT = 3  # seconds

LOCALISATION_SERVICE = "lokalisointi"
LOCALISATION_SERVICE_URL = f"{OPINTOPOLKU_URL}/{LOCALISATION_SERVICE}/cxf/rest/v1/"
LOCALISATION_SERVICE_TIMEOUT = 3  # seconds
LOCALISATION_ENDPOINT = LOCALISATION_SERVICE_URL + "localisation"


# Arvo settings
ARVO_URL = os.getenv("ARVO_URL", "http://localhost:5000")
ARVO_API_USERNAME = os.getenv("ARVO_API_USERNAME", "virkailija")
ARVO_API_PASSWORD = os.getenv("ARVO_API_PASSWORD", "localhero")
ARVO_VASTAAJATUNNUS_ENDPOINT = ARVO_URL + "/api/yleinen/v1/vastaajatunnus/"
ARVO_TIMEOUT = int(os.getenv("ARVO_TIMEOUT", 3))  # seconds
ARVO_ORGANISAATIOT_UPDATE_ENDPOINT = ARVO_URL + "/api/yleinen/v1/paivita-organisaatiot"


# Varda settings
VARDA_URL = os.getenv("VARDA_URL", "http://localhost")
VARDA_USERNAME = os.getenv("VARDA_USERNAME", "username")
VARDA_PASSWORD = os.getenv("VARDA_PASSWORD", "password")
VARDA_APIKEY_ENDPOINT = VARDA_URL + "/api/user/apikey/"
VARDA_ORGANISAATIOT_ENDPOINT = VARDA_URL + "/api/reporting/v1/valssi/organisaatiot/"
VARDA_TAUSTATIEDOT_ENDPOINT = VARDA_URL + "/api/reporting/v1/valssi/organisaatiot/{}/taustatiedot/"
VARDA_TOIMIPAIKAT_ENDPOINT = VARDA_URL + "/api/reporting/v1/valssi/toimipaikat/"
VARDA_TYONTEKIJAT_ENDPOINT = VARDA_URL + "/api/reporting/v1/valssi/toimipaikat/{}/tyontekijat/"
VARDA_ORG_COUNT_PER_REQUEST = 200
VARDA_TYONTEKIJA_COUNT_PER_REQUEST = 100
VARDA_TIMEOUT = 5  # seconds
VARDA_TEST_CERT_FILE = "./kyselyt/migrations/testing/dummy-test-cert-for-tests-only.pfx"  # dummy, only for tests
VARDA_CERT_FILE = VARDA_TEST_CERT_FILE if TESTING else os.getenv("VARDA_CERT_FILE", "/tmp/varda_cert.pfx")
VARDA_CERT_PASSWORD = os.getenv("VARDA_CERT_PASSWORD", "password")

# write Varda certificate using Base64 encoded env
VARDA_CERT_BASE64_ENCODED = os.getenv("VARDA_CERT_BASE64_ENCODED", None)
if not TESTING and VARDA_CERT_BASE64_ENCODED:
    import base64
    cert_file = open(VARDA_CERT_FILE, "wb")
    cert_file.write(base64.b64decode(VARDA_CERT_BASE64_ENCODED))
    cert_file.close()

# Django-session
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "virkailijapalvelu_sessionid"
SESSION_COOKIE_AGE = 36000  # 10 hours
SESSION_COOKIE_PATH = "/virkailijapalvelu"
