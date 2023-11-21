"""Utility functions for raportointipalvelu data collection"""
from typing import List

from django.db.models import QuerySet

from raportointi.constants import DATE_INPUT_FORMAT
from raportointi.models import Kyselykerta, Vastaaja, Vastaajatunnus, Kysely, Kysymysryhma


def calculate_pct(numerator: int, denominator: int) -> int:
    """Calculates percentage, returns percentage as int, e.g. 42(%)"""
    # to fix exact half rounding always up, add tiny value
    return round(numerator / denominator * 100 + 0.000001) if numerator and denominator else 0


def get_kyselykerta_answer_pct(
        kyselykerta: dict, vastaajatunnuses: List[dict], vastaajas: List[dict]) -> (int, int, int):
    """Get answer percentage for a KyselyKerta"""
    answered_count = len([1 for vastaaja in vastaajas if vastaaja["kyselykertaid"] == kyselykerta["kyselykertaid"]])
    sent_count = len([1 for vastaajatunnus in vastaajatunnuses
                      if vastaajatunnus["kyselykertaid"] == kyselykerta["kyselykertaid"]])

    return calculate_pct(answered_count, sent_count), sent_count, answered_count


def get_toimipaikka_vastaaja_sent_count(vastaajatunnuses: List[dict]) -> (int, int):
    """Get toimipaikka_sent and vastaaja_sent
    Toimipaikka_sent calculates if at least one kysely is sent out for a toimipaikka
    Vastaaja_sent calculates total of person sent out to
    """
    vastaaja_sent_count = len(vastaajatunnuses)
    sent_kyselykertaid_set = {vastaajatunnus["kyselykertaid"] for vastaajatunnus in vastaajatunnuses}

    return len(sent_kyselykertaid_set), vastaaja_sent_count


def get_toimipaikka_vastaaja_answered_count(
        kyselykertas: List[dict], vastaajatunnuses: List[dict], vastaajas: List[dict]) -> (int, int):
    """Get toimipaikka & vastaaja answered counts"""
    vastaaja_answered_count = len(vastaajas)

    toimipaikka_answered_count = 0
    for kyselykerta in kyselykertas:
        _, _, answered_count = get_kyselykerta_answer_pct(kyselykerta, vastaajatunnuses, vastaajas)
        if answered_count > 0:
            toimipaikka_answered_count += 1

    return toimipaikka_answered_count, vastaaja_answered_count


def get_toimipaikka_vastaaja_answer_pct(
        kyselykertas: List[dict], vastaajatunnuses: List[dict], vastaajas: List[dict]) -> (int, int):
    """Get answer percentage for toimipaikka & vastaaja
    Answers divided by sent
    """
    toimipaikka_answered_count, vastaaja_answered_count = get_toimipaikka_vastaaja_answered_count(
        kyselykertas, vastaajatunnuses, vastaajas)
    toimipaikka_sent_count, vastaaja_sent_count = get_toimipaikka_vastaaja_sent_count(vastaajatunnuses)

    toimipaikka_answer_pct = calculate_pct(toimipaikka_answered_count, toimipaikka_sent_count)
    vastaaja_answer_pct = calculate_pct(vastaaja_answered_count, vastaaja_sent_count)

    return toimipaikka_answer_pct, vastaaja_answer_pct


def get_toimipaikka_extra_data(
        kyselykertas: List[dict], vastaajatunnuses: List[dict], vastaajas: List[dict]) -> ([list], [str]):
    """Get extra data for toimipaikka
    Check if toimipaikka has sent out at all
    Check which toimipaikka's have less than 50% answering percentage, sorted with the lowest % first
    """
    toimipaikka_answer_percentage_lt_50 = []
    toimipaikka_kysely_not_sent = []

    for kyselykerta in kyselykertas:
        toimipaikka_name_fi = kyselykerta["oppilaitos"]["nimi_fi"]
        toimipaikka_name_sv = kyselykerta["oppilaitos"]["nimi_sv"]
        answer_pct, sent_count, _ = get_kyselykerta_answer_pct(kyselykerta, vastaajatunnuses, vastaajas)

        if sent_count == 0:
            toimipaikka_kysely_not_sent.append(
                {"nimi_fi": toimipaikka_name_fi, "nimi_sv": toimipaikka_name_sv})
        elif answer_pct < 50:
            toimipaikka_answer_percentage_lt_50.append(
                {"nimi_fi": toimipaikka_name_fi, "nimi_sv": toimipaikka_name_sv, "answer_pct": answer_pct})

    toimipaikka_answer_percentage_lt_50_sorted = sorted(
        toimipaikka_answer_percentage_lt_50, key=lambda item: item["answer_pct"])

    return toimipaikka_answer_percentage_lt_50_sorted, toimipaikka_kysely_not_sent


def get_latest_answer_date(vastaajas: List[dict]) -> str:
    """Get the latest answer date of all Kysely's"""
    latest_answer_date = None
    if vastaajas:
        latest_answer_date = vastaajas[0]["luotuaika"]

    for vastaaja in vastaajas[1:]:
        if vastaaja["luotuaika"] > latest_answer_date:
            latest_answer_date = vastaaja["luotuaika"]

    if latest_answer_date is not None:
        latest_answer_date = latest_answer_date.strftime(DATE_INPUT_FORMAT)

    return latest_answer_date


def get_data_dicts_by_kyselys(kyselys: QuerySet[Kysely]) -> (dict, dict, dict, dict, dict):
    kysely_dicts = []
    kyselyids = []
    kysymysryhmaids = set()
    for kysely in kyselys:
        kysely_dicts.append(dict(
            kyselyid=kysely.pk,
            kysymysryhmaid=kysely.metatiedot["valssi_kysymysryhma"],
            nimi_fi=kysely.nimi_fi,
            nimi_sv=kysely.nimi_sv,
            voimassa_alkupvm=kysely.voimassa_alkupvm,
            voimassa_loppupvm=kysely.voimassa_loppupvm,
            koulutustoimija=kysely.koulutustoimija,
            oppilaitos=kysely.oppilaitos))
        kyselyids.append(kysely.pk)
        kysymysryhmaids.add(kysely.metatiedot["valssi_kysymysryhma"])

    kysymysryhmas = Kysymysryhma.objects.filter(kysymysryhmaid__in=kysymysryhmaids)
    kysymysryhma_dicts = dict()
    for kysymysryhma in kysymysryhmas:
        kysymysryhma_dicts[kysymysryhma.pk] = dict(
            kysymysryhmaid=kysymysryhma.pk,
            nimi_fi=kysymysryhma.nimi_fi,
            nimi_sv=kysymysryhma.nimi_sv,
            muutettuaika=kysymysryhma.muutettuaika,
            lomaketyyppi=kysymysryhma.metatiedot.get("lomaketyyppi", ""),
            main_indicator=kysymysryhma.metatiedot.get("paaIndikaattori", {}),
            secondary_indicators=kysymysryhma.metatiedot.get("sekondaariset_indikaattorit", []))

    kyselykertas = Kyselykerta.objects.filter(kyselyid__in=kyselyids) \
        .select_related("kyselyid__oppilaitos", "kyselyid__koulutustoimija")
    kyselykerta_dicts = []
    kyselykertaids = []
    for kyselykerta in kyselykertas:
        oppilaitos = dict(oid=kyselykerta.kyselyid.oppilaitos.oid,
                          nimi_fi=kyselykerta.kyselyid.oppilaitos.nimi_fi,
                          nimi_sv=kyselykerta.kyselyid.oppilaitos.nimi_sv) \
            if kyselykerta.kyselyid.oppilaitos else dict(oid=None, nimi_fi=None, nimi_sv=None)
        kyselykerta_dicts.append(dict(
            kyselykertaid=kyselykerta.pk,
            kyselyid=kyselykerta.kyselyid.kyselyid,
            oppilaitos=oppilaitos,
            koulutustoimija=dict(oid=kyselykerta.kyselyid.koulutustoimija.oid,
                                 nimi_fi=kyselykerta.kyselyid.koulutustoimija.nimi_fi,
                                 nimi_sv=kyselykerta.kyselyid.koulutustoimija.nimi_sv)
        ))
        kyselykertaids.append(kyselykerta.pk)

    vastaajatunnuses = Vastaajatunnus.objects.filter(kyselykertaid__in=kyselykertaids).select_related("kyselykertaid")
    vastaajatunnus_dicts = []
    for vastaajatunnus in vastaajatunnuses:
        vastaajatunnus_dicts.append(dict(
            vastaajatunnusid=vastaajatunnus.pk,
            kyselykertaid=vastaajatunnus.kyselykertaid.kyselykertaid))

    vastaajas = Vastaaja.objects.filter(kyselykertaid__in=kyselykertaids)
    vastaaja_dicts = []
    for vastaaja in vastaajas:
        vastaaja_dicts.append(dict(
            vastaajaid=vastaaja.pk,
            kyselykertaid=vastaaja.kyselykertaid,
            luotuaika=vastaaja.luotuaika))

    return kysely_dicts, kysymysryhma_dicts, kyselykerta_dicts, vastaajatunnus_dicts, vastaaja_dicts


def get_organisaatio_in_use_counts(kyselys: List[dict]) -> (int, int):
    koulutustoimija_set = set()
    oppilaitos_set = set()
    for kysely in kyselys:
        if kysely["koulutustoimija"] not in koulutustoimija_set:
            koulutustoimija_set.add(kysely["koulutustoimija"])
        if kysely["oppilaitos"] and kysely["oppilaitos"] not in oppilaitos_set:
            oppilaitos_set.add(kysely["oppilaitos"])

    return len(koulutustoimija_set), len(oppilaitos_set)


def get_organisaatio_sent_counts(vastaajatunnuses: List[dict], kyselykertas: List[dict]) -> (int, int):
    koulutustoimija_set = set()
    oppilaitos_set = set()
    for kyselykerta in kyselykertas:
        for vastaajatunnus in vastaajatunnuses:
            if kyselykerta["kyselykertaid"] == vastaajatunnus["kyselykertaid"]:
                koulutustoimija_set.add(kyselykerta["koulutustoimija"]["oid"])
                oppilaitos_set.add(kyselykerta["oppilaitos"]["oid"])
                break

    return len(koulutustoimija_set), len(oppilaitos_set)


def get_earliest_starting_date(kyselys: List[dict]) -> str:
    earliest_starting_date = kyselys[0]["voimassa_alkupvm"]
    for kysely in kyselys[1:]:
        if kysely["voimassa_alkupvm"] < earliest_starting_date:
            earliest_starting_date = kysely["voimassa_alkupvm"]

    return earliest_starting_date


def get_latest_ending_date(kyselys: List[dict]) -> str:
    latest_ending_date = kyselys[0]["voimassa_loppupvm"]
    for kysely in kyselys[1:]:
        if kysely["voimassa_loppupvm"] > latest_ending_date:
            latest_ending_date = kysely["voimassa_loppupvm"]

    return latest_ending_date


def get_koulutustoimija_names(kyselys: List[dict]) -> dict:
    koulutustoimija_names_fi = sorted(list({str(kysely["koulutustoimija"].nimi_fi) for kysely in kyselys}))
    koulutustoimija_names_sv = sorted(list({str(kysely["koulutustoimija"].nimi_sv) for kysely in kyselys}))
    return dict(koulutustoimija_names=dict(fi=koulutustoimija_names_fi,
                                           sv=koulutustoimija_names_sv))
