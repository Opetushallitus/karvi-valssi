
import html5validate
import responses
import weasyprint

from django.test import TestCase

from kyselyt.migrations.testing.setup import add_test_data_for_html_test, \
    add_testing_responses_virkailijapalvelu_scales
from kyselyt.models import Kyselykerta, Vastaaja
from kyselyt.utils_pdf import create_content_html, update_global_scales


class PdfCreationTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        add_test_data_for_html_test()

    def test_pdf_creation(self):
        pdf_file = None
        try:
            pdf_file = weasyprint.HTML(string="<html>something</html>").write_pdf()
        except Exception:
            pass
        self.assertIsNotNone(pdf_file)

    @responses.activate
    def test_get_pdf_html_creation_validity(self):
        add_testing_responses_virkailijapalvelu_scales(responses)
        scale_count = len(update_global_scales())
        self.assertTrue(scale_count > 0)

        kyselykerta = Kyselykerta.objects.get(nimi="html_test_kyselykerta")
        vastaaja = Vastaaja.objects.get(kyselykertaid=kyselykerta.kyselykertaid)
        html_str = create_content_html(vastaaja, "fi")
        html5validate.validate(html_str)
