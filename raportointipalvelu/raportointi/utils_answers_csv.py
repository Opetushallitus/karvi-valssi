import logging
import pandas as pd
from typing import List, Tuple

from django.db.models import QuerySet

from raportointi.constants import (
    REPORT_MIN_ANSWERS, DEFAULT_REPORT_VALUE, REPORT_CSV_COLS, REPORT_CSV_COL_NAMES, REPORT_EOS_VALUE,
    REPORT_NULL_VALUE, CSV_DELIMITER)
from raportointi.models import Kysely, Kysymysryhma, Vastaaja, Vastaus, Kysymys, Kyselykerta


logger = logging.getLogger(__name__)


def create_answers_singleline_csv_by_kyselys(kyselys: QuerySet[Kysely], kysymysryhma: Kysymysryhma, language: str):
    kyselys_dict, kyselyids = create_kyselys_dict_and_kyselyids(kyselys)
    vastaajas = Vastaaja.objects.filter(kyselyid__in=kyselyids).order_by("vastaajaid")
    kysymys_texts, kysymysids = get_filtered_kysymyses(kysymysryhma.pk, language)
    lomaketyyppi = kysymysryhma.metatiedot.get("lomaketyyppi")

    if vastaajas.count() >= REPORT_MIN_ANSWERS:
        kyselykertas = Kyselykerta.objects.filter(kyselyid__in=kyselyids)
        data = create_answers_singleline_csv_data(
            vastaajas, kyselys_dict, kyselykertas, kysymysryhma, kysymysids, language)
    else:
        data = []

    report_cols = REPORT_CSV_COLS[lomaketyyppi]
    report_col_names = [REPORT_CSV_COL_NAMES[col][language] for col in report_cols]
    col_names = report_col_names + kysymys_texts
    df = pd.DataFrame(data, columns=col_names)
    csv_file = df.to_csv(sep=CSV_DELIMITER, index=False, encoding="utf-8")
    return csv_file


def create_kyselys_dict_and_kyselyids(kyselys: QuerySet[Kysely]) -> Tuple[dict, List[int]]:
    kyselyids = []
    kyselys_dict = dict()
    for kysely in kyselys:
        kyselys_dict[str(kysely.pk)] = kysely
        kyselyids.append(kysely.pk)
    return kyselys_dict, kyselyids


def create_answers_singleline_csv_data(
        vastaajas: QuerySet[Vastaaja], kyselys_dict: dict, kyselykertas: QuerySet[Kyselykerta],
        kysymysryhma: Kysymysryhma, kysymysids: List[int], language: str) -> list:
    data = []
    kysymysryhma_nimi = kysymysryhma.nimi_fi if language == "fi" else kysymysryhma.nimi_sv
    vastauses_dict = create_vastauses_dict(vastaajas)
    tehtavanimike_counts = create_tehtavanimike_counts_dict(vastaajas)
    tehtavanimike_default_count = 0
    lomaketyyppi = kysymysryhma.metatiedot.get("lomaketyyppi")
    report_cols = REPORT_CSV_COLS[lomaketyyppi]

    for vastaaja in vastaajas:
        kysely = kyselys_dict[str(vastaaja.kyselyid)]
        voimassa_alkupvm = kysely.voimassa_alkupvm
        voimassa_loppupvm = kysely.voimassa_loppupvm
        koulutustoimija_oid = kysely.koulutustoimija.oid
        kunta = kysely.koulutustoimija.kunta

        tehtavanimike, kelpoisuus, tehtavanimike_default_count = \
            get_tehtavanimike_and_kelpoisuus(vastaaja, tehtavanimike_counts, tehtavanimike_default_count)

        henk_total, henk_tn, henk_kelp = get_henkilosto_values(kyselykertas, vastaaja, report_cols)

        koul_pv, koul_tn, koul_tn_pv = get_taydennyskoulutukset(kyselykertas, vastaaja, report_cols)

        answers = [vastauses_dict.get(str(vastaaja.pk), {}).get(str(kysymysid), REPORT_NULL_VALUE)
                   for kysymysid in kysymysids]

        cols_data = []
        cols_data += [vastaaja.pk] if "vastaajaid" in report_cols else []
        cols_data += [kysymysryhma_nimi] if "lomake_nimi" in report_cols else []
        cols_data += [voimassa_alkupvm] if "alkamispaiva" in report_cols else []
        cols_data += [voimassa_loppupvm] if "paattymispaiva" in report_cols else []
        cols_data += [koulutustoimija_oid] if "organisaatio_oid" in report_cols else []
        cols_data += [kunta] if "kuntakoodi" in report_cols else []
        cols_data += [tehtavanimike] if "tehtavanimike" in report_cols else []
        cols_data += [kelpoisuus] if "kelpoisuus" in report_cols else []
        cols_data += [get_toimintamuodot(kyselykertas, vastaaja)] if "toimintamuodot" in report_cols else []
        cols_data += [henk_total] if "henkilosto_total" in report_cols else []
        cols_data += [henk_tn] if "henkilosto_tn" in report_cols else []
        cols_data += [henk_kelp] if "henkilosto_kelp" in report_cols else []
        cols_data += [get_lapset_voimassa(kyselykertas, vastaaja)] if "lapset_voimassa" in report_cols else []
        cols_data += [koul_pv] if "koulutus_pv" in report_cols else []
        cols_data += [koul_tn] if "koulutus_tn" in report_cols else []
        cols_data += [koul_tn_pv] if "koulutus_tn_pv" in report_cols else []
        data.append(cols_data + answers)

    # remove tehtavanimike data if default-count is less than min-limit
    if "tehtavanimike" in report_cols and tehtavanimike_default_count < REPORT_MIN_ANSWERS:
        tnimike_index = report_cols.index("tehtavanimike")
        for item in data:
            item[tnimike_index] = DEFAULT_REPORT_VALUE  # tehtavanimike
            item[tnimike_index + 1] = DEFAULT_REPORT_VALUE  # kelpoisuus

    return data


def create_tehtavanimike_counts_dict(vastaajas: QuerySet[Vastaaja]) -> dict:
    tehtavanimike_counts = dict()
    for vastaaja in vastaajas:
        if vastaaja.tehtavanimikkeet:
            tehtavanimike = vastaaja.tehtavanimikkeet[0]  # only first is counted
            koodi_kelpoisuus = f"{tehtavanimike['tehtavanimike_koodi']}-{tehtavanimike['kelpoisuus_kytkin']}"
        else:
            koodi_kelpoisuus = "None"
        tehtavanimike_counts.setdefault(koodi_kelpoisuus, 0)
        tehtavanimike_counts[koodi_kelpoisuus] += 1
    return tehtavanimike_counts


def get_filtered_kysymyses(kysymysryhmaid: int, language: str) -> Tuple[List[str], List[int]]:
    kysymyses = Kysymys.objects.filter(kysymysryhmaid=kysymysryhmaid).order_by("jarjestys", "matriisi_jarjestys")
    kysymys_texts = []
    kysymysids = []
    for kysymys in kysymyses:
        # filter out statictext-parts and matrix_roots
        if kysymys.metatiedot.get("type") == "statictext":
            continue
        if kysymys.vastaustyyppi == "matrix_root":
            continue
        if language == "fi":
            kysymys_texts.append(kysymys.kysymys_fi)
        else:
            kysymys_texts.append(kysymys.kysymys_sv)
        kysymysids.append(kysymys.pk)
    return kysymys_texts, kysymysids


def create_vastauses_dict(vastaajas: QuerySet[Vastaaja]) -> dict:
    vastauses = Vastaus.objects.filter(vastaajaid__in=vastaajas).select_related("vastaajaid")
    vastauses_dict = dict()
    for vastaus in vastauses:
        if vastaus.string is not None:
            answer = vastaus.string
        elif vastaus.numerovalinta is not None:
            answer = vastaus.numerovalinta
        elif vastaus.en_osaa_sanoa is not None:
            answer = REPORT_EOS_VALUE
        else:
            answer = REPORT_NULL_VALUE
        vastaajaid = str(vastaus.vastaajaid.pk)
        vastauses_dict.setdefault(vastaajaid, dict())
        vastauses_dict[vastaajaid][str(vastaus.kysymysid)] = answer
    return vastauses_dict


def get_tehtavanimike_and_kelpoisuus(
        vastaaja: Vastaaja, tehtavanimike_counts: dict, tehtavanimike_default_count: int) -> (str, str, int):
    if vastaaja.tehtavanimikkeet:
        tnimike = vastaaja.tehtavanimikkeet[0]  # only first is counted
        koodi_kelpoisuus = f"{tnimike['tehtavanimike_koodi']}-{tnimike['kelpoisuus_kytkin']}"
    else:
        tnimike = {"tehtavanimike_koodi": REPORT_NULL_VALUE, "kelpoisuus_kytkin": REPORT_NULL_VALUE}
        koodi_kelpoisuus = "None"

    if tehtavanimike_counts[koodi_kelpoisuus] >= REPORT_MIN_ANSWERS:
        tehtavanimike = tnimike["tehtavanimike_koodi"]
        kelpoisuus = str(tnimike["kelpoisuus_kytkin"])
    else:
        tehtavanimike = DEFAULT_REPORT_VALUE
        kelpoisuus = DEFAULT_REPORT_VALUE
        tehtavanimike_default_count += 1

    return tehtavanimike, kelpoisuus, tehtavanimike_default_count


def get_toimintamuodot(kyselykertas: QuerySet[Kyselykerta], vastaaja: Vastaaja) -> str:
    try:
        kyselykerta = Kyselykerta.objects.none()
        for kk in kyselykertas:
            if kk.kyselyid.pk == vastaaja.kyselyid:
                kyselykerta = kk
                break
        return str(kyselykerta.metatiedot["rakennetekijalomake_data"]["toimipaikat"]["toimintamuodot"])
    except Exception as e:
        logger.error(f"Error getting toimintamuodot value. Error: {e}")
    return ""


def get_lapset_voimassa(kyselykertas: QuerySet[Kyselykerta], vastaaja: Vastaaja) -> int:
    try:
        kyselykerta = Kyselykerta.objects.none()
        for kk in kyselykertas:
            if kk.kyselyid.pk == vastaaja.kyselyid:
                kyselykerta = kk
                break
        return str(kyselykerta.metatiedot["rakennetekijalomake_data"]["lapset_voimassa"])
    except Exception as e:
        logger.error(f"Error getting lapset_voimassa value. Error: {e}")
    return 0


def get_henkilosto_values(kyselykertas: QuerySet[Kyselykerta], vastaaja: Vastaaja,
                          report_cols: List[str]) -> (int, str, str):
    if not set(["henkilosto_total", "henkilosto_tn", "henkilosto_kelp"]).intersection(set(report_cols)):
        return 0, "", ""

    try:
        kyselykerta = Kyselykerta.objects.none()
        for kk in kyselykertas:
            if kk.kyselyid.pk == vastaaja.kyselyid:
                kyselykerta = kk
                break
        tyontekija_data = kyselykerta.metatiedot["rakennetekijalomake_data"]["tyontekijat"]
        henkilosto_total = tyontekija_data["total"]
        henkilosto_tehtavanimikkeet = str(tyontekija_data["tehtavanimikkeet"])
        henkilosto_kelpoiset = str(tyontekija_data["tehtavanimikkeet_kelpoiset"])
        return henkilosto_total, henkilosto_tehtavanimikkeet, henkilosto_kelpoiset
    except Exception as e:
        logger.error(f"Error getting henkilosto values. Error: {e}")
    return 0, "", ""


def get_taydennyskoulutukset(kyselykertas: QuerySet[Kyselykerta], vastaaja: Vastaaja,
                             report_cols: List[str]) -> (str, str, str):
    if not set(["koulutus_pv", "koulutus_tn", "koulutus_tn_pv"]).intersection(set(report_cols)):
        return "", "", ""

    try:
        kyselykerta = Kyselykerta.objects.none()
        for kk in kyselykertas:
            if kk.kyselyid.pk == vastaaja.kyselyid:
                kyselykerta = kk
                break
        koulutus_data = kyselykerta.metatiedot["taydennyskoulutukset"]
        koulutus_pv = koulutus_data["koulutuspaivat"]
        koulutus_tehtavanimikkeet = str(koulutus_data["tehtavanimikkeet"])
        koulutus_tehtavanimikkeet_pv = str(koulutus_data["tehtavanimikkeet_koulutuspaivat"])
        return koulutus_pv, koulutus_tehtavanimikkeet, koulutus_tehtavanimikkeet_pv
    except Exception as e:
        logger.error(f"Error getting taydennyskoulutukset values. Error: {e}")
    return "", "", ""
