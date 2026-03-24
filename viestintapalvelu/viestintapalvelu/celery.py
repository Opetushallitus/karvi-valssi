import logging
import os

from celery import Celery
from celery.schedules import crontab
from datetime import timedelta, datetime
from time import sleep

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

    # calls every day at 2:15
    sender.add_periodic_task(
        crontab(hour=2, minute=15), remove_email_data_from_old_messages.s(),)

    # calls every day at 4:00
    sender.add_periodic_task(
        crontab(hour=4, minute=0), check_failed_messages.s(24),)

    # calls every day at 4:30
    sender.add_periodic_task(
        crontab(hour=4, minute=30), re_queue_messagequeue_messages.s(),)

    # calls every x minutes
    INTERVAL = 10  # minutes
    sender.add_periodic_task(INTERVAL * 60.0, update_message_statuses.s(INTERVAL))
    sender.add_periodic_task(INTERVAL * 60.0, check_failed_messages.s(1))
    sender.add_periodic_task(INTERVAL * 60.0, retry_failed_messages.s(INTERVAL))


@app.task
def update_message_statuses(interval=3):
    from kyselyt.models import Message
    from kyselyt.constants import EMAIL_STATUS_SENT
    from kyselyt.utils import get_email_status

    task_start_time = datetime.now()

    messages = Message.objects.filter(msg_status=EMAIL_STATUS_SENT, email_service_msg_id_str__isnull=False)
    messages_dict = {message.pk: message for message in messages}

    objs_to_update = []
    for msg in messages:
        # check task runtime and break loop before next task starts to avoid simultaneous tasks
        if task_start_time + timedelta(minutes=interval - 1) < datetime.now():
            break

        new_status, email_service_status_code = get_email_status(msg.email_service_msg_id_str)
        if new_status is not None and (
            new_status != msg.msg_status or
            email_service_status_code != msg.email_service_status_code
        ):
            obj_to_update = messages_dict[msg.pk]
            obj_to_update.msg_status = new_status
            obj_to_update.email_service_status_code = email_service_status_code
            objs_to_update.append(obj_to_update)

    update_count = Message.objects.bulk_update(objs_to_update, ["msg_status", "email_service_status_code"])

    if messages.exists():
        logger.info(f"Message statuses ('{EMAIL_STATUS_SENT}') checked and updated. (updated: {update_count})")

        # Check Messages that have been in SENT status for more than 2 hours
        CREATED_LIMIT = 2  # hours
        messages_sent_overtime = Message.objects.filter(
            msg_status=EMAIL_STATUS_SENT,
            created__lt=timezone.now() - timedelta(hours=CREATED_LIMIT))
        if messages_sent_overtime.exists():
            logger.error("There are Messages in SENT status for over 2 hours.")


@app.task
def check_failed_messages(hours_delta: int = 168):  # default delta = 1 week
    from django.conf import settings
    from kyselyt.models import Message
    from kyselyt.constants import EMAIL_STATUS_FAILED
    from kyselyt.utils import get_email_status

    messages_kwargs = dict()
    if hours_delta:
        messages_kwargs["created__gt"] = timezone.now() - timedelta(hours=hours_delta)

    # Filter out old messages where email addresses have already been removed
    messages = Message.objects.filter(
        msg_status=EMAIL_STATUS_FAILED,
        email_service_msg_id_str__isnull=False,
        **messages_kwargs
    ).exclude(email="")
    messages_dict = {message.pk: message for message in messages}

    logger.info(f"Checking failed messages. (hours_delta={hours_delta}) (count: {messages.count()})")

    objs_to_update = []
    for msg in messages:
        # skip '.invalid'-ending addresses (disabled in production)
        if not settings.PRODUCTION_ENV and msg.email.endswith(".invalid"):
            continue
        new_status, email_service_status_code = get_email_status(msg.email_service_msg_id_str)
        if new_status is not None and new_status != msg.msg_status:
            obj_to_update = messages_dict[msg.pk]
            obj_to_update.msg_status = new_status
            obj_to_update.email_service_status_code = email_service_status_code
            objs_to_update.append(obj_to_update)

    update_count = Message.objects.bulk_update(objs_to_update, ["msg_status", "email_service_status_code"])

    if messages.exists():
        logger.info(f"Message statuses ('{EMAIL_STATUS_FAILED}') checked and updated. (updated: {update_count})")


@app.task
def retry_failed_messages(interval=3):
    from kyselyt.constants import FAILED_TASKS_RETRY_MAX_COUNT, EMAIL_STATUS_SENT, DEFAULT_SLEEP
    from kyselyt.models import FailedTask, Message
    from kyselyt.utils import send_email_vastaajatunnus

    task_start_time = datetime.now()

    failed_messages = FailedTask.objects.all()
    retry_succeed_count = 0
    retry_failed_count = 0
    for task in failed_messages:
        # check task runtime and break loop before next task starts to avoid simultaneous tasks
        if task_start_time + timedelta(minutes=interval - 1) < datetime.now():
            break
        result, email_service_msg_id_str = send_email_vastaajatunnus(
            task.email, task.vastaajatunnus, task.message, task.template, task.pdfs_encoded)
        if result == "OK" and email_service_msg_id_str:
            logger.info(f"Retrying failed-message succeeded. (msg_id: {task.msg_id})")
            retry_succeed_count += 1
            Message.objects.filter(pk=task.msg_id).update(
                email_service_msg_id_str=email_service_msg_id_str, msg_status=EMAIL_STATUS_SENT)
            FailedTask.objects.filter(pk=task.pk).delete()
            retry_failed_count = 0
        else:
            logger.warning(f"Retrying failed-message failed. (msg_id: {task.msg_id})")
            retry_failed_count += 1
            if retry_failed_count >= FAILED_TASKS_RETRY_MAX_COUNT:
                logger.error(
                    f"Retrying failed-messages max failed sequential count exceeded ({FAILED_TASKS_RETRY_MAX_COUNT}).")
                break
        sleep(DEFAULT_SLEEP)

    if retry_succeed_count == 0 and retry_failed_count > 0:
        logger.error("Retrying failed-messages failed. 0 succeed retries.")


@app.task
def re_queue_messagequeue_messages():
    """
    There shouldn't be any Messages to re-queue if everything works as planned.
    This task is runned as backup if celery-queue fails.
    """
    from kyselyt.models import MessageQueue
    from kyselyt.tasks import send_email_by_message_queue_task

    queue_messages = MessageQueue.objects.all()
    for queue_obj in queue_messages:
        send_email_by_message_queue_task.delay(queue_obj.msg_id)

    if queue_messages.exists():
        logger.error(f"Messages re-queued to celery-queue. (count {queue_messages.count()})")


@app.task
def remove_email_data_from_old_messages():
    from kyselyt.utils import empty_email_fields_from_old_messages

    update_count = empty_email_fields_from_old_messages()
    logger.info(f"Email addresses removed from old Messages. (count: {update_count})")
