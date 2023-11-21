import random
from typing import List

from django.conf import settings
from django.db import transaction
from django.db.models.query import QuerySet

from kyselyt.models import Vastaajatunnus, Vastaaja, Vastaus, Kysymys
from kyselyt.constants import NUMEROVALINTA_TYPES_AND_LIMITS

LOREMS = [
    ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce laoreet rhoncus cursus. Donec pretium, justo non suscipit rutrum, lacus urna feugiat felis, nec sagittis dui turpis euismod dui. Donec nec faucibus lacus. Sed ac eros a neque venenatis aliquam. Aliquam erat volutpat. Proin mauris justo, porttitor sit amet tincidunt ut, euismod vitae mauris. Maecenas lacinia neque id quam ornare, et aliquam diam porttitor. In hac habitasse platea dictumst. In risus justo, laoreet eget accumsan et, vestibulum quis quam. Ut gravida hendrerit ante, et laoreet eros faucibus quis. Vestibulum sollicitudin iaculis nibh, vel bibendum ipsum lacinia sit amet. Proin tristique vulputate elit, vehicula posuere eros condimentum dapibus. Suspendisse ultrices ipsum in eros semper sollicitudin. " * 20).split(" "),
    ("Etiam tincidunt sapien placerat dignissim eleifend. Nullam dictum sapien in enim aliquet, nec bibendum elit fermentum. Duis porttitor tellus at ante condimentum pellentesque. Etiam justo arcu, tempus gravida felis ac, hendrerit ultrices nulla. Donec ac posuere turpis. Vivamus hendrerit vel ligula ac porta. Sed hendrerit eros lacus. Nulla faucibus nunc ut risus dictum laoreet. Phasellus ultrices, velit id volutpat cursus, ligula nisl porttitor nisi, eu sodales orci neque sit amet nunc. Donec sem velit, tincidunt in sollicitudin quis, pellentesque ut arcu. " * 20).split(" "),
    ("Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Aliquam sapien tellus, rhoncus pharetra sapien et, rhoncus ultrices ipsum. Suspendisse faucibus sem in arcu gravida, vitae suscipit sapien dapibus. Sed eu sem volutpat, aliquam nisi vel, vestibulum nunc. Phasellus sit amet quam ipsum. Duis bibendum venenatis nibh vitae lacinia. Nulla luctus ante erat, eu sodales elit pellentesque vitae. Nulla vitae cursus erat, nec pulvinar nibh. Aliquam leo odio, ultrices sed auctor nec, congue vitae arcu. Aliquam pulvinar diam at risus semper auctor. Sed ut dui id sem fermentum lacinia. In nec augue a nisi interdum pellentesque. Integer blandit posuere consequat. Duis imperdiet metus vestibulum odio maximus dignissim. " * 20).split(" "),
    ("Morbi non luctus metus. Aliquam velit erat, finibus at turpis id, varius accumsan velit. Duis lacinia, est vitae elementum venenatis, magna ligula sagittis nibh, sit amet fringilla ligula urna sed eros. Donec tellus mi, dapibus vitae nunc et, posuere luctus quam. Mauris eleifend porttitor orci, at finibus dolor sollicitudin eget. Mauris sed quam metus. Mauris purus est, mollis sit amet felis nec, maximus dapibus dolor. In vel lorem fermentum mi placerat consectetur et ut libero. Maecenas sit amet dui tincidunt ipsum malesuada porttitor. Nulla maximus porta tortor sed congue. Aenean a ipsum malesuada, condimentum ipsum a, varius lacus. Etiam luctus dui id pharetra eleifend. " * 20).split(" "),
    ("Integer nisl purus, ornare vel ipsum quis, scelerisque egestas odio. Curabitur scelerisque egestas vulputate. Nulla quis erat elit. Proin sodales nisl purus, in vestibulum sem convallis vel. Etiam in enim mattis, gravida dui in, suscipit odio. Pellentesque vestibulum, turpis id ullamcorper vehicula, felis ligula pharetra nisi, sit amet volutpat velit erat ut elit. In fringilla nulla ut enim eleifend pulvinar. Curabitur condimentum nisi at est sagittis accumsan. In vestibulum pulvinar feugiat. Aenean tincidunt lorem urna, a aliquam augue vestibulum non. Nullam ut ante quam. " * 20).split(" ")]

ANSWER_PERCENTAGE = 0.85
TYONTEKIJA_DATA = [
    dict(tehtavanimike_koodi="64212", tutkinnot=["003", "613101"]),
    dict(tehtavanimike_koodi="81787", tutkinnot=["003"]),
    dict(tehtavanimike_koodi="84724", tutkinnot=["003", "371101"])]
KELPOISUUS_TRUE_PERCENTAGE = 0.9
EOS_TRUE_PERCENTAGE = 0.1


def create_vastaajat_vastaukset(kyselykerta_ids: List[int], answer_pct: float = ANSWER_PERCENTAGE):
    if settings.PRODUCTION_ENV:
        print("NOT ALLOWED IN PRODUCTION.")
        return 0

    if not isinstance(kyselykerta_ids, list):
        print("Validation error: kyselykerta_ids is not list")
        return 0

    created_vastaaja_count = 0
    skipped_count = 0
    vastaajatunnukset = Vastaajatunnus.objects.filter(kyselykertaid__in=kyselykerta_ids) \
        .exclude(lukittu=True) \
        .select_related("kyselykertaid", "kyselykertaid__kyselyid") \
        .prefetch_related("kyselykertaid__kyselyid__kysely__kysymysryhmaid")

    if not vastaajatunnukset.exists():
        print("Vastaajatunnukset not found.")
        return 0

    # check every Vastaajatunnus is related to same Kysymysryhma
    if len(set([vastaajatunnus.kyselykertaid.kyselyid.kysely.first().kysymysryhmaid.pk
                for vastaajatunnus in vastaajatunnukset])) != 1:
        print("Vastaajatunnukset have to be related to same Kysymysryhma.")
        return 0

    kysymysryhma = vastaajatunnukset.first().kyselykertaid.kyselyid.kysely.first().kysymysryhmaid
    kysymykset = Kysymys.objects.filter(kysymysryhmaid=kysymysryhma) \
        .exclude(vastaustyyppi="matrix_root")

    for vastaajatunnus in vastaajatunnukset:
        # randomly skip Vastaajatunnus
        if not random_bool(answer_pct):
            skipped_count += 1
            continue

        print(f"Creating answers for {vastaajatunnus.tunnus}")

        with transaction.atomic(using="valssi"):
            create_vastaaja_vastaukset_by_vastaajatunnus(vastaajatunnus, kysymykset)
        created_vastaaja_count += 1

    print(f"Vastaajas created: {created_vastaaja_count}. Skipped: {skipped_count}")


def create_vastaaja_vastaukset_by_vastaajatunnus(vastaajatunnus: Vastaajatunnus,
                                                 kysymykset: QuerySet[Kysymys]):
    if settings.PRODUCTION_ENV:
        print("NOT ALLOWED IN PRODUCTION.")
        return 0

    tehtavanimikkeet, tutkinnot = random_tehtavanimikkeet_tutkinnot()
    vastaaja = Vastaaja.objects.create(
        kyselykertaid=vastaajatunnus.kyselykertaid.pk,
        kyselyid=vastaajatunnus.kyselykertaid.kyselyid.pk,
        vastaajatunnus=vastaajatunnus.tunnus,
        tehtavanimikkeet=tehtavanimikkeet,
        tutkinnot=tutkinnot)

    for kysymys in kysymykset:
        # skip intertitle questions
        if kysymys.metatiedot.get("type", "") == "statictext":
            continue
        create_vastaus(kysymys=kysymys, vastaaja=vastaaja)

    # lock Vastaajatunnus
    vastaajatunnus.lukittu = True
    vastaajatunnus.save()


def create_vastaus(kysymys: Kysymys, vastaaja: Vastaaja):
    vastaus_kwargs = dict(kysymysid=kysymys.pk, vastaajaid=vastaaja)
    vastaustyyppi = kysymys.vastaustyyppi
    metatiedot = kysymys.metatiedot
    # numeric
    if vastaustyyppi == "string" and metatiedot.get("numeric", False):
        Vastaus.objects.create(string=random.randint(1, 100), **vastaus_kwargs)

    # multiline
    elif vastaustyyppi == "string" and metatiedot.get("multiline", False):
        vastaus_str = f"{random_lorem(12, 20)}\n\n{random_lorem(12, 20)}"
        Vastaus.objects.create(string=vastaus_str, **vastaus_kwargs)

    # textfield
    elif vastaustyyppi == "string":
        Vastaus.objects.create(string=random_lorem(8, 12), **vastaus_kwargs)

    # multichoice
    elif vastaustyyppi == "monivalinta":
        create_monivalinta_vastaus(metatiedot, vastaus_kwargs)

    # matrix
    elif kysymys.matriisi_kysymysid and kysymys.matriisi_jarjestys > 0:
        if kysymys.eos_vastaus_sallittu and random_bool(EOS_TRUE_PERCENTAGE):
            Vastaus.objects.create(en_osaa_sanoa=True, **vastaus_kwargs)
        else:
            numerovalinta = random_numerovalinta_by_vastaustyyppi(vastaustyyppi)
            Vastaus.objects.create(numerovalinta=numerovalinta, **vastaus_kwargs)


def create_monivalinta_vastaus(metatiedot: dict, vastaus_kwargs: dict):
    choice_count = len(metatiedot.get("vastausvaihtoehdot", []))

    # multichoice (1-choice)
    if metatiedot.get("type", "") == "radiobutton":
        Vastaus.objects.create(numerovalinta=random.randint(1, choice_count), **vastaus_kwargs)

    # multichoice (n-choice)
    elif metatiedot.get("type", "") == "checkbox":
        # create random count of answers
        answers = sorted(random.sample(list(range(1, choice_count + 1)), choice_count))
        for answer in answers:
            Vastaus.objects.create(numerovalinta=answer, **vastaus_kwargs)


def random_tehtavanimikkeet_tutkinnot():
    tyontekija_data = random.choice(TYONTEKIJA_DATA)
    tehtavanimikkeet = [dict(kelpoisuus_kytkin=random_bool(KELPOISUUS_TRUE_PERCENTAGE),
                             tehtavanimike_koodi=tyontekija_data["tehtavanimike_koodi"])]
    return tehtavanimikkeet, tyontekija_data["tutkinnot"]


def random_numerovalinta_by_vastaustyyppi(vastaustyyppi: str):
    for nv_type in NUMEROVALINTA_TYPES_AND_LIMITS:
        if vastaustyyppi == nv_type["vastaustyyppi"]:
            return random.randint(nv_type["lower"], nv_type["upper"])
    return 1


def random_bool(true_pct: float = 0.5):
    return random.uniform(0, 1) < true_pct


def random_lorem(min_words: int = 4, max_words: int = 12):
    lorem_rnd = random.choice(LOREMS)
    word_count = random.randint(min_words, max_words)
    return " ".join(lorem_rnd[:word_count])
