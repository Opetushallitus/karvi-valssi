import logging
import os

from celery import Celery
from celery.schedules import crontab


logger = logging.getLogger(__name__)


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vastauspalvelu.settings")

app = Celery("vastauspalvelu", broker_connection_retry_on_startup=True)

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
    # calls every day at 3:00
    sender.add_periodic_task(
        crontab(hour=3, minute=0), delete_outdated_tempvastauses.s(),)


@app.task
def delete_outdated_tempvastauses():
    from kyselyt.utils import delete_outdated_tempvastauses
    delete_count = delete_outdated_tempvastauses()
    logger.info(f"Outdated TempVastaus' removed. (count: {delete_count})")
