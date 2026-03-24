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
    # calls every day at 3:00 (utc)
    sender.add_periodic_task(
        crontab(hour=3, minute=0), delete_outdated_tempvastauses.s(),)

    # calls every day at 2:00 (utc)
    sender.add_periodic_task(
        crontab(hour=2, minute=0), update_vastaajas_failed_taustatiedot.s(),)

    # calls every day at 3:05 (utc)
    sender.add_periodic_task(
        crontab(hour=3, minute=5), check_and_remove_duplicate_vastaajas.s(),)


@app.task
def delete_outdated_tempvastauses():
    from kyselyt.utils import delete_outdated_tempvastauses
    delete_count = delete_outdated_tempvastauses()
    logger.info(f"Outdated TempVastaus' removed. (count: {delete_count})")


@app.task
def update_vastaajas_failed_taustatiedot():
    from kyselyt.models import FailedTaustatiedot, Vastaaja
    from kyselyt.utils_auth import get_tyontekija_data

    failed_taustatiedot_objs = FailedTaustatiedot.objects.all()
    if not failed_taustatiedot_objs.exists():
        logger.info("Update Vastaajas failed taustatiedot task: No FailedTaustatiedot.")
        return None

    update_succeed_count = 0
    for obj in failed_taustatiedot_objs:
        tyontekija_data, is_tyontekija_not_found = get_tyontekija_data(obj.vastaajatunnus)
        if is_tyontekija_not_found:
            logger.warning(f"Update Vastaajas failed taustatiedot task: tyontekija not found. ({obj.vastaajatunnus})")
            FailedTaustatiedot.objects.filter(pk=obj.pk).delete()
            update_succeed_count += 1
            continue
        if tyontekija_data is None:
            logger.error("Update Vastaajas failed taustatiedot task: failed to get tyontekija_data from "
                         f"Virkailijapalvelu. ({obj.vastaajatunnus})")
            continue

        vastaaja = Vastaaja.objects.filter(vastaajatunnus=obj.vastaajatunnus).first()
        if not vastaaja:
            logger.error("Update Vastaajas failed taustatiedot task: failed to get Vastaaja object. "
                         f"({obj.vastaajatunnus})")
            continue

        # update taustatiedot to Vastaaja
        Vastaaja.objects.filter(pk=vastaaja.pk).update(
            tehtavanimikkeet=tyontekija_data["tehtavanimikkeet"],
            tutkinnot=tyontekija_data["tutkinnot"])

        FailedTaustatiedot.objects.filter(pk=obj.pk).delete()
        update_succeed_count += 1

    logger.info(f"Update Vastaajas failed taustatiedot succeeded. (count {update_succeed_count})")


@app.task
def check_and_remove_duplicate_vastaajas():
    from datetime import datetime
    from django.db import transaction
    from django.db.models import Count
    from django.utils.timezone import make_aware
    from kyselyt.models import Vastaaja, Vastaajatunnus, Vastaus

    logger.info("Checking duplicate Vastaajas.")

    created_after_time = make_aware(datetime(2025, 8, 1, 0, 0, 0))
    duplicate_vastaajas = (
        Vastaaja.objects
        .filter(luotuaika__gt=created_after_time)
        .values("vastaajatunnus")
        .annotate(tunnus_count=Count("vastaajatunnus"))
        .filter(tunnus_count__gt=1)
    )
    duplicate_tunnuses = [v["vastaajatunnus"] for v in duplicate_vastaajas]

    # split query into chunks
    CHUNK_SIZE = 100
    vastaajatunnuses = []
    for i in range(0, len(duplicate_tunnuses), CHUNK_SIZE):
        tunnuses_chunk = duplicate_tunnuses[i:i + CHUNK_SIZE]
        # filter kohteiden_lkm=1
        vastaajatunnuses_chunk = Vastaajatunnus.objects.filter(tunnus__in=tunnuses_chunk, kohteiden_lkm=1)
        vastaajatunnuses.extend(vastaajatunnuses_chunk)

    # log results
    if vastaajatunnuses:
        logger.warning(f"Duplicate Vastaajas found. count={len(vastaajatunnuses)}")
    else:
        logger.info("No duplicate Vastaajas found.")

    # Remove duplicates
    for vt in vastaajatunnuses:
        tunnus = vt.tunnus
        vastaajaids = list(
            Vastaaja.objects
            .filter(vastaajatunnus=tunnus)
            .order_by("vastaajaid")
            .values_list("vastaajaid", flat=True)
        )

        # Skip if only one record (this never should happen)
        if len(vastaajaids) <= 1:
            continue

        with transaction.atomic():
            # Keep first Vastaaja and delete others
            vastaajaids_to_delete = vastaajaids[1:]

            # Delete related Vastaus rows first
            Vastaus.objects.filter(vastaajaid__in=vastaajaids_to_delete).delete()

            # Delete duplicate Vastaaja rows
            Vastaaja.objects.filter(vastaajaid__in=vastaajaids_to_delete).delete()

        logger.info(f"Duplicate Vastaajas removed. tunnus={tunnus}")
