from celery import shared_task

from kyselyt.models import VastausSend
from kyselyt.utils_pdf import post_answer_pdf_to_viestintapalvelu


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 5, "countdown": 60})
def send_answer_pdf_task(self, vastaussend_id):
    vastaussend = VastausSend.objects.get(pk=vastaussend_id)
    result = post_answer_pdf_to_viestintapalvelu(
        vastaussend.email, vastaussend.vastaajaid.vastaajaid, vastaussend.language)
    if result != "OK":
        raise Exception(result)

    # remove VastausSend object when email sent successfully
    VastausSend.objects.filter(pk=vastaussend_id).delete()
