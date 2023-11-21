from django.conf import settings


BASE_URL = settings.BASE_URL

RAPORTOINTIPALVELU_API_URL = f"/{BASE_URL}api/v1"

TEST_USER = {"username": "test-user", "password": "supersecret"}

TEST_DATABASES = ["default", "valssi", "vastauspalvelu", "virkailijapalvelu"]
