import logging

from celery import shared_task

from kyselyt.constants import OPETUSHALLITUS_OID, ALLOWED_TOIMINTAMUOTO_CODES
from kyselyt.models import Organisaatio


logger = logging.getLogger(__name__)


@shared_task(bind=True)
def anonymize_organizations_with_unallowed_toimintamuoto(self):
    anonymized_update_count = 0

    toimipaikkas = Organisaatio.objects.exclude(parent_oid__oid=OPETUSHALLITUS_OID)
    for toimipaikka in toimipaikkas:
        metatiedot = toimipaikka.metatiedot
        if "toimintamuoto_koodi" in metatiedot and \
                metatiedot["toimintamuoto_koodi"].lower() not in ALLOWED_TOIMINTAMUOTO_CODES:
            anonymized_name = f"anonymized-{toimipaikka.oid[-8:]}"
            Organisaatio.objects.filter(oid=toimipaikka.oid).update(
                nimi_fi=anonymized_name,
                nimi_sv=anonymized_name,
                nimi_en=anonymized_name,
            )
            anonymized_update_count += 1

    logger.info(f"Toimipaikkas anonymized. count={anonymized_update_count}")
