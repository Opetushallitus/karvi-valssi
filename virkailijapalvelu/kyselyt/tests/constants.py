from django.conf import settings


BASE_URL = settings.BASE_URL

VIRKAILIJAPALVELU_API_URL = f"/{BASE_URL}api/v1"

TEST_USER = {"username": "test-user", "password": "supersecret"}
TEST_SERVICE_USER = {"username": "test-service-user", "password": "supersecret"}


def get_test_access_token(client, service_user=False) -> str:
    user = TEST_SERVICE_USER if service_user else TEST_USER
    resp = client.post(f"{VIRKAILIJAPALVELU_API_URL}/token/", data=user).json()
    return resp.get("access")


def get_test_refresh_token(client) -> str:
    resp = client.post(f"{VIRKAILIJAPALVELU_API_URL}/token/", data=TEST_USER).json()
    return resp.get("refresh")
