from django.conf import settings
from rest_framework import status


VALSSI_VERSION = "1.1.3"

VASTAAJATUNNUS_MAX_LENGTH = 10

OPINTOPOLKU_HEADERS = {'Caller-Id': 'csc.valssi', 'CSRF': 'csc.valssi', 'Cookie': 'CSRF=csc.valssi'}

SUCCESS_STATUSES = (status.HTTP_200_OK, status.HTTP_201_CREATED)

PDF_CONTENT_TYPE = "application/pdf"

# Time after sending email when marked as "delivered"
MINUTES_TO_DELIVERED = 120

FAILED_TASKS_RETRY_MAX_COUNT = 3

# Email message statuses
EMAIL_STATUS_SENT = "sent"
EMAIL_STATUS_DELIVERED = "delivered"
EMAIL_STATUS_FAILED = "failed"

KYSELY_LINK_BASE = settings.VASTAAJA_UI_URL + "?vastaajatunnus={}"

# Email template codes
FIRST_MSG_TEMPLATE_NO = 1
SECOND_MSG_TEMPLATE_NO = 2
ANSWER_PDF_TEMPLATE_NO = 3

# Email template subjects
FIRST_MSG_TEMPLATE_SUBJECT = "Linkki arviointilomakkeeseen / Länk till utvärderingsblanketten"
SECOND_MSG_TEMPLATE_SUBJECT = "Muistutus arviointilomakkeeseen vastaamisesta / Påminnelse om att besvara utvärderingsblanketten"
ANSWER_PDF_TEMPLATE_SUBJECT = "Vastauksesi arviointilomakkeeseen / Dina svar på utvärderingsblanketten"

# Email template messages
FIRST_MSG_TEMPLATE_LINES = [
    "Täytä arviointilomake linkistä / Fyll i utvärderingsblanketten via länken:"]
SECOND_MSG_TEMPLATE_LINES = [
    "Et ole vielä täyttänyt arviointilomaketta. Täytä arviointilomake linkistä / "
    "Du har ännu inte besvarat utvärderingsblanketten. Fyll i utvärderingsblanketten via länken:"]
ANSWER_PDF_TEMPLATE_LINES = [
    "Kiitos lomakkeeseen vastaamisesta! Kirjaamasi vastaukset löytyvät viestin liitteestä PDF-tiedostona. / "
    "Tack för att du svarat på blanketten! Dina svar finns i PDF-bilagan till meddelandet."]

# Email template texts and link
PRIVACY_STATEMENT_TEXT = "Tietosuojaseloste / Sekretesspolicy:"
PRIVACY_STATEMENT_LINK = "https://wiki.eduuni.fi/x/kR05E"

# loop configs
MAX_NO_OF_LOOPS = 4
LOOP_SLEEPS = [3, 6, 10, 0]  # length need to be same as MAX_NO_OF_LOOPS (last item 0)
