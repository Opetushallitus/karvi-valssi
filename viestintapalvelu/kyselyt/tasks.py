from celery import shared_task

from kyselyt.constants import EMAIL_STATUS_FAILED, EMAIL_STATUS_SENT
from kyselyt.models import Message, FailedTask, MessageQueue
from kyselyt.utils import send_email_vastaajatunnus


@shared_task(bind=True, rate_limit="10/m")
def send_email_by_message_queue_task(self, msg_id):
    message_queue_obj = MessageQueue.objects.filter(msg_id=msg_id).first()

    # Skip if message not in queue
    if not message_queue_obj:
        return None

    message_obj = Message.objects.filter(pk=msg_id).first()

    # Skip if Message doesnt exist or message already sent
    if not message_obj or message_obj.email_service_msg_id_str:
        # Remove from MessageQueue
        MessageQueue.objects.filter(msg_id=msg_id).delete()
        return None

    # Send email
    result, email_service_msg_id_str = send_email_vastaajatunnus(
        message_queue_obj.email,
        message_queue_obj.vastaajatunnus,
        message_queue_obj.message,
        message_queue_obj.template,
        message_queue_obj.pdfs_encoded)

    if result == "OK" and email_service_msg_id_str:
        # Email sent successfully
        Message.objects.filter(pk=msg_id).update(
            email_service_msg_id_str=email_service_msg_id_str,
            msg_status=EMAIL_STATUS_SENT)
    else:
        # Email sending failed, add it to FailedTask
        Message.objects.filter(pk=msg_id).update(msg_status=EMAIL_STATUS_FAILED)
        if not FailedTask.objects.filter(msg_id=msg_id).first():
            FailedTask.objects.create(
                msg_id=message_queue_obj.msg_id,
                email=message_queue_obj.email,
                vastaajatunnus=message_queue_obj.vastaajatunnus,
                message=message_queue_obj.message,
                template=message_queue_obj.template,
                pdfs_encoded=message_queue_obj.pdfs_encoded)

    # Remove from MessageQueue
    MessageQueue.objects.filter(msg_id=msg_id).delete()
