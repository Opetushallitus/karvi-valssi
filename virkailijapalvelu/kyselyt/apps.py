import urllib3

from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_migrate

from kyselyt.migrations.production.setup import create_indicators, create_scales, create_malfunction_messages

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # disable requests_pkcs12 warnings


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


def run_post_migration_tasks(sender, **kwargs):
    for migration_plan_tuple in kwargs["plan"]:
        if (migration_plan_tuple[0].app_label == "kyselyt" and
                not migration_plan_tuple[1] and
                migration_plan_tuple[0].name == "0014_alter_indikaattori_key" and
                not settings.TESTING):
            create_indicators()

        if (migration_plan_tuple[0].app_label == "kyselyt" and
                not migration_plan_tuple[1] and
                migration_plan_tuple[0].name == "0019_malfunctionmessage_service" and
                not settings.TESTING):
            create_malfunction_messages()

        if (migration_plan_tuple[0].app_label == "kyselyt" and
                not migration_plan_tuple[1] and
                migration_plan_tuple[0].name == "0020_scale_eos_allowed_scale_is_visible" and
                not settings.TESTING):
            create_scales()

    # if plan-list is empty, migrations are done previously
    # this is used to update initialization values
    if not kwargs["plan"] and not settings.TESTING:
        create_indicators()
        create_malfunction_messages()
        create_scales()


class KyselytConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "kyselyt"

    def ready(self):
        post_migrate.connect(run_post_migration_tasks, sender=self)
