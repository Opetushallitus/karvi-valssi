import os
import logging

from celery import Celery
from celery.schedules import crontab

from django.core.management import call_command

logger = logging.getLogger(__name__)


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "virkailijapalvelu.settings")

app = Celery("virkailijapalvelu", broker_connection_retry_on_startup=True)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# This is needed for Django logger to work
app.conf.worker_hijack_root_logger = False

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # calls every day at 2:00
    sender.add_periodic_task(
        crontab(hour=2, minute=0), flush_expired_tokens.s(),)

    # calls every day at 4:00
    sender.add_periodic_task(
        crontab(hour=4, minute=0), delete_outdated_kyselysends_task.s(),)

    # calls every day at 4:05
    sender.add_periodic_task(
        crontab(hour=4, minute=5), delete_all_userauthorizations_task.s(),)

    # calls every x minutes
    INTERVAL = 60  # minutes
    sender.add_periodic_task(INTERVAL * 60.0, update_varda_organisaatiot_and_toimipaikat.s())


@app.task
def flush_expired_tokens():
    call_command("flushexpiredtokens")
    logger.info("Expired JWT refresh tokens flushed.")


@app.task
def update_varda_organisaatiot_and_toimipaikat():
    from kyselyt.utils import update_organizations

    # update organisaatiot
    result = update_organizations()
    if result != "OK":
        raise Exception(result)
    logger.info("Varda organizations updated.")

    # update toimipaikat
    result = update_organizations(is_toimipaikat=True)
    if result != "OK":
        raise Exception(result)
    logger.info("Varda toimipaikat updated.")


@app.task
def delete_outdated_kyselysends_task():
    from kyselyt.utils import delete_outdated_kyselysends
    delete_count = delete_outdated_kyselysends()
    logger.info(f"Outdated KyselySends removed. (count: {delete_count})")


@app.task
def delete_all_userauthorizations_task():
    from kyselyt.utils import delete_userauths
    delete_count = delete_userauths()
    logger.info(f"UserAuthorizations removed. (count: {delete_count})")
