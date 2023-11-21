from celery import shared_task

from kyselyt.constants import EMAIL_STATUS_FAILED, EMAIL_STATUS_SENT
from kyselyt.models import Message, FailedTask
from kyselyt.utils import send_email_vastaajatunnus


@shared_task(bind=True)
def send_email_to_answer_task(self, email, vastaajatunnus, message, template, msg_id, pdfs_encoded):
    message_obj = Message.objects.filter(pk=msg_id).first()
    if not message_obj or message_obj.email_service_msg_id == 0:
        result, email_service_msg_id = send_email_vastaajatunnus(email, vastaajatunnus, message, template, pdfs_encoded)
        if result == "OK":
            # email sent successfully
            Message.objects.filter(pk=msg_id).update(
                email_service_msg_id=email_service_msg_id, msg_status=EMAIL_STATUS_SENT)
        else:
            # email sending failed, add it to FailedTask
            Message.objects.filter(pk=msg_id).update(msg_status=EMAIL_STATUS_FAILED)
            if not FailedTask.objects.filter(msg_id=msg_id).first():
                FailedTask.objects.create(
                    email=email, vastaajatunnus=vastaajatunnus, message=message,
                    template=template, msg_id=msg_id, pdfs_encoded=pdfs_encoded)
