from django.conf import settings
from raportointi.models import Kysymysryhma, ReportingTemplate


def create_reporting_template(kysymysryhma_id: int):
    if settings.PRODUCTION_ENV:
        print("NOT ALLOWED IN PRODUCTION.")
        return 0

    kysymysryhma = Kysymysryhma.objects.filter(pk=kysymysryhma_id).first()
    if not kysymysryhma:
        print("Kysymysryhma not found.")
        return 0

    ReportingTemplate.objects.create(
        kysymysryhmaid=kysymysryhma_id,
        title_fi="", title_sv="", description_fi="", description_sv="")
    print("ReportingTemplate created.")
