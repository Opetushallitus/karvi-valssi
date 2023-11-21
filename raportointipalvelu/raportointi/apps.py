from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in, user_logged_out


def login_handler(sender, user, request, **kwargs):
    if request.method == "GET":
        request.session["user"] = user.username


def logout_handler(sender, user, request, **kwargs):
    if "user" in request.session:
        request.session.pop("user")

    if "refresh_token" in request.session:
        request.session.pop("refresh_token")


# Catch signals
user_logged_in.connect(login_handler)
user_logged_out.connect(logout_handler)


class RaportointiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "raportointi"
