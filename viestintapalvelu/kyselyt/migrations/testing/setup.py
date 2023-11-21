from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import status

from kyselyt.models import Message


def add_test_messages():
    Message.objects.create(email="a001@a.aa", msg_status="", template=1)


def add_test_user():
    User.objects.create_user("test-user", "", "supersecret")


def load_testing_data():
    add_test_user()
    add_test_messages()


def add_testing_responses_email_service(responses_obj):
    responses_obj.add(
        responses_obj.POST, f"{settings.EMAIL_SERVICE_URL}email",
        json={"id": 1}, status=status.HTTP_200_OK)


def add_testing_responses_service_ticket(responses_obj):
    responses_obj.add(
        responses_obj.POST, f"{settings.OPINTOPOLKU_URL}/cas/v1/tickets",
        headers={"Location": "http://ok"}, status=status.HTTP_201_CREATED)

    responses_obj.add(
        responses_obj.POST, "http://ok", json={}, status=status.HTTP_200_OK)


def add_testing_responses_service_ticket_fail_500(responses_obj):
    responses_obj.add(
        responses_obj.POST, f"{settings.OPINTOPOLKU_URL}/cas/v1/tickets",
        headers={"Location": "http://fail"}, status=status.HTTP_201_CREATED)

    responses_obj.add(
        responses_obj.POST, "http://fail", json={}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
