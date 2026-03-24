from django.conf import settings


BASE_URL = settings.BASE_URL

VIESTINTAPALVELU_API_URL = f"/{BASE_URL}api/v1"

TEST_USER = {"username": "test-user", "password": "supersecret"}


def get_test_access_token(client) -> str:
    resp = client.post(f"{VIESTINTAPALVELU_API_URL}/token/", data=TEST_USER).json()
    return resp.get("access")
