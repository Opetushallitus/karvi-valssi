import logging
import os

from celery import Celery
from celery.schedules import crontab
from datetime import timedelta, datetime

from django.utils import timezone


logger = logging.getLogger(__name__)


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viestintapalvelu.settings")

app = Celery("viestintapalvelu", broker_connection_retry_on_startup=True)

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
    # calls once a week (monday 4:10)
    sender.add_periodic_task(
        crontab(day_of_week=1, hour=4, minute=10), check_failed_messages.s(),)

    # calls every day at 4:00
    sender.add_periodic_task(
        crontab(hour=4, minute=0), check_failed_messages.s(24),)

    # calls every x minutes
    INTERVAL = 10  # minutes
    sender.add_periodic_task(INTERVAL * 60.0, update_message_statuses.s())
    sender.add_periodic_task(INTERVAL * 60.0, check_failed_messages.s(1))
    sender.add_periodic_task(INTERVAL * 60.0, retry_failed_tasks.s(INTERVAL))


@app.task
def update_message_statuses():
    from kyselyt.models import Message
    from kyselyt.constants import MINUTES_TO_DELIVERED, EMAIL_STATUS_SENT, EMAIL_STATUS_DELIVERED

    messages = Message.objects.filter(msg_status=EMAIL_STATUS_SENT)
    messages_dict = {message.pk: message for message in messages}

    objs_to_update = []
    for msg in messages:
        # TODO check bounces and do status changes (ticket VAL-418)
        if msg.created + timedelta(minutes=MINUTES_TO_DELIVERED) < timezone.now():
            obj_to_update = messages_dict[msg.pk]
            obj_to_update.msg_status = EMAIL_STATUS_DELIVERED
            objs_to_update.append(obj_to_update)

    update_count = Message.objects.bulk_update(objs_to_update, ["msg_status"])

    if messages.exists():
        logger.info(f"Message statuses ('{EMAIL_STATUS_SENT}') checked and updated. (updated: {update_count})")


@app.task
def check_failed_messages(hours_delta: int = None):
    from django.conf import settings
    from kyselyt.models import Message
    from kyselyt.constants import EMAIL_STATUS_FAILED
    from kyselyt.utils import get_email_status

    messages_kwargs = dict()
    if hours_delta:
        messages_kwargs["created__gt"] = timezone.now() - timedelta(hours=hours_delta)
    messages = Message.objects.filter(
        msg_status=EMAIL_STATUS_FAILED, email_service_msg_id__gt=0, **messages_kwargs)
    messages_dict = {message.pk: message for message in messages}

    objs_to_update = []
    for msg in messages:
        # skip '.invalid'-ending addresses (disabled in production)
        if not settings.PRODUCTION_ENV and msg.email.endswith(".invalid"):
            continue
        new_status = get_email_status(msg.email_service_msg_id)
        if new_status is not None and new_status != msg.msg_status:
            obj_to_update = messages_dict[msg.pk]
            obj_to_update.msg_status = new_status
            objs_to_update.append(obj_to_update)

    update_count = Message.objects.bulk_update(objs_to_update, ["msg_status"])

    if messages.exists():
        logger.info(f"Message statuses ('{EMAIL_STATUS_FAILED}') checked and updated. (updated: {update_count})")


@app.task
def retry_failed_tasks(interval=3):
    from kyselyt.constants import FAILED_TASKS_RETRY_MAX_COUNT, EMAIL_STATUS_SENT
    from kyselyt.models import FailedTask, Message
    from kyselyt.utils import send_email_vastaajatunnus

    task_start_time = datetime.now()

    failed_tasks = FailedTask.objects.all()
    retry_succeed_count = 0
    retry_failed_count = 0
    for task in failed_tasks:
        # check task runtime and break loop before next task starts to avoid simultaneous tasks
        if task_start_time + timedelta(minutes=interval - 1) < datetime.now():
            break
        result, email_service_msg_id = send_email_vastaajatunnus(
            task.email, task.vastaajatunnus, task.message, task.template, task.pdfs_encoded)
        if result == "OK":
            logger.info(f"Retrying failed-task succeeded. (msg_id: {task.msg_id})")
            retry_succeed_count += 1
            Message.objects.filter(pk=task.msg_id).update(
                email_service_msg_id=email_service_msg_id, msg_status=EMAIL_STATUS_SENT)
            FailedTask.objects.filter(pk=task.pk).delete()
        else:
            logger.warning(f"Retrying failed-task failed. (msg_id: {task.msg_id})")
            retry_failed_count += 1
            if retry_failed_count >= FAILED_TASKS_RETRY_MAX_COUNT:
                logger.error(f"Retrying failed-tasks max failed count exceeded ({FAILED_TASKS_RETRY_MAX_COUNT}).")
                break

    if retry_succeed_count == 0 and retry_failed_count > 0:
        logger.error("Retrying failed-tasks failed. 0 succeed retries.")
