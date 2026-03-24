import logging
import pandas as pd

from collections import defaultdict
from typing import List, Tuple, Set

from django.db.models import QuerySet

from raportointi.constants import (
    REPORT_MIN_ANSWERS, REPORT_VALUE_DEFAULT, REPORT_CSV_COLS, REPORT_CSV_COL_NAMES, REPORT_CSV_COLS_SIIRTO,
    REPORT_EOS_VALUE_BY_SCALE, REPORT_EOS_VALUE_DEFAULT, REPORT_VALUE_NULL, REPORT_VALUE_HIDDEN,
    CSV_DELIMITER, LOMAKE_USAGE_EXPORT_COLS, LOMAKE_USAGE_EXPORT_COL_TRANSLATIONS, REPORT_VALUE_TRUE,
    REPORT_VALUE_FALSE, DATE_INPUT_FORMAT,
)
from raportointi.indicators import INDICATORS_SHORT_DICT
from raportointi.models import (
    Kysely, Kysymysryhma, Vastaaja, Vastaus, Kysymys, Kyselykerta, Organisaatio, KysymysJatkokysymys, AluejakoAlue,
    Result, Vastaajatunnus,
)
from raportointi.utils_report import get_report_language_codes


logger = logging.getLogger(__name__)


def create_answers_singleline_csv_by_kyselys(
    kyselys: QuerySet[Kysely],
    kysymysryhma: Kysymysryhma,
    language: str,
    is_siirto: bool = False,
    hide_text_type_answers: bool = False,
    hide_hidden_report_questions: bool = True,
):
    kyselys_dict, kyselyids = create_kyselys_dict_and_kyselyids(kyselys)
    vastaajas = Vastaaja.objects.filter(kyselyid__in=kyselyids).order_by("vastaajaid")
    kysymys_texts, kysymysids, kysymyses, hidden_kysymysids = get_filtered_kysymyses(kysymysryhma.pk, language)
    lomaketyyppi = kysymysryhma.metatiedot.get("lomaketyyppi")

    report_cols = REPORT_CSV_COLS[lomaketyyppi]
    if is_siirto:
        report_cols = REPORT_CSV_COLS_SIIRTO[lomaketyyppi]

    if not vastaajas.exists():
        data = []
    elif is_siirto or vastaajas.count() >= REPORT_MIN_ANSWERS:
        kyselykertas = Kyselykerta.objects.filter(kyselyid__in=kyselyids)
        data = create_answers_singleline_csv_data(
            vastaajas, kyselys_dict, kyselykertas, kysymysryhma, kysymysids, kysymyses, hidden_kysymysids,
            language, report_cols, is_siirto, hide_text_type_answers, hide_hidden_report_questions,
        )
    else:
        data = []

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
    vastaajas: QuerySet[Vastaaja],
    kyselys_dict: dict,
    kyselykertas: QuerySet[Kyselykerta],
    kysymysryhma: Kysymysryhma,
    kysymysids: List[int],
    kysymyses: List[Kysymys],
    hidden_kysymysids: List[int],
    language: str,
    report_cols: List[str],
    is_siirto: bool,
    hide_text_type_answers: bool,
    hide_hidden_report_questions: bool,
) -> list:
    data = []
    kysymysryhma_nimi = kysymysryhma.nimi_fi if language == "fi" else kysymysryhma.nimi_sv
    indicators = get_indicators_combined(kysymysryhma)
    vastauses_dict = create_vastauses_dict(vastaajas, kysymyses, hide_text_type_answers)
    toimintakieli_counts = create_toimintakieli_counts_dict(vastaajas, kyselys_dict)
    toimintakieli_default_count = 0
    tehtavanimike_counts = create_tehtavanimike_counts_dict(vastaajas)
    tehtavanimike_default_count = 0
    tutkinto_counts = create_tutkinto_counts_dict(vastaajas)
    aluejako_names = create_aluejako_names_dict()

    for vastaaja in vastaajas:
        kysely = kyselys_dict[str(vastaaja.kyselyid)]
        voimassa_alkupvm = kysely.voimassa_alkupvm
        voimassa_loppupvm = kysely.voimassa_loppupvm
        koulutustoimija_name = kysely.koulutustoimija.nimi_fi if language == "fi" else kysely.koulutustoimija.nimi_sv
        koulutustoimija_oid = kysely.koulutustoimija.oid
        kunta = kysely.koulutustoimija.kunta
        yritysmuoto = get_yritysmuoto(kysely.koulutustoimija)
        toimintakieli, toimintakieli_default_count = get_toimintakieli(
            vastaaja, kyselys_dict, toimintakieli_counts, toimintakieli_default_count, is_siirto)

        tehtavanimike, kelpoisuus, tehtavanimike_default_count = \
            get_tehtavanimike_and_kelpoisuus(vastaaja, tehtavanimike_counts, tehtavanimike_default_count, is_siirto)
        tutkinto = get_tutkinto(vastaaja, tutkinto_counts, is_siirto)

        henk_total, henk_tn, henk_kelp = get_henkilosto_values(kyselykertas, vastaaja, report_cols)

        koul_pv, koul_tn, koul_tn_pv = get_taydennyskoulutukset(kyselykertas, vastaaja, report_cols)

        toimipaikka = get_oppilaitos_data(kysely)
        aluejako_name = get_aluejako_name(kysely, aluejako_names, language)

        answers = []
        for kysymysid in kysymysids:
            # Set answers 'HIDDEN' of hidden questions if needed
            if hide_hidden_report_questions and kysymysid in hidden_kysymysids:
                answers.append(REPORT_VALUE_HIDDEN)
            else:
                answers.append(vastauses_dict.get(str(vastaaja.pk), {}).get(str(kysymysid), REPORT_VALUE_NULL))

        cols_data = []
        cols_data += [vastaaja.pk] if "vastaajaid" in report_cols else []
        cols_data += [kysymysryhma_nimi] if "lomake_nimi" in report_cols else []
        cols_data += [indicators] if "indikaattori" in report_cols else []
        cols_data += [voimassa_alkupvm] if "alkamispaiva" in report_cols else []
        cols_data += [voimassa_loppupvm] if "paattymispaiva" in report_cols else []

        cols_data += [koulutustoimija_name] if "organisaatio_nimi" in report_cols else []
        cols_data += [koulutustoimija_oid] if "organisaatio_oid" in report_cols else []
        cols_data += [kunta] if "kuntakoodi" in report_cols else []
        cols_data += [yritysmuoto] if "yritysmuoto" in report_cols else []

        cols_data += [get_toimintamuodot(kyselykertas, vastaaja)] if "toimintamuodot" in report_cols else []
        cols_data += [henk_total] if "henkilosto_total" in report_cols else []
        cols_data += [henk_tn] if "henkilosto_tn" in report_cols else []
        cols_data += [henk_kelp] if "henkilosto_kelp" in report_cols else []
        cols_data += [get_lapset_voimassa(kyselykertas, vastaaja)] if "lapset_voimassa" in report_cols else []
        cols_data += [get_tuen_tiedot(kyselykertas, vastaaja)] if "tuen_tiedot" in report_cols else []

        cols_data += [koul_pv] if "koulutus_pv" in report_cols else []
        cols_data += [koul_tn] if "koulutus_tn" in report_cols else []
        cols_data += [koul_tn_pv] if "koulutus_tn_pv" in report_cols else []

        cols_data += [aluejako_name] if "aluejako" in report_cols else []
        cols_data += [toimipaikka["oid"]] if "toimipaikka_oid" in report_cols else []
        cols_data += [toimipaikka["nimi"]] if "toimipaikka_nimi" in report_cols else []
        cols_data += [toimipaikka["postinumero"]] if "toimipaikka_postinumero" in report_cols else []
        cols_data += [toimipaikka["jarjestamismuoto"]] if "toimipaikka_jarjmuoto" in report_cols else []
        cols_data += [toimipaikka["toimintamuoto"]] if "toimipaikka_toimmuoto" in report_cols else []
        cols_data += [toimintakieli] if "toimintakieli" in report_cols else []

        cols_data += [tehtavanimike] if "tehtavanimike" in report_cols else []
        cols_data += [kelpoisuus] if "kelpoisuus" in report_cols else []
        cols_data += [tutkinto] if "tutkinto" in report_cols else []

        data.append(cols_data + answers)

    # remove tehtavanimike data if there is default-count and it is less than min-limit
    if not is_siirto and "tehtavanimike" in report_cols and 0 < tehtavanimike_default_count < REPORT_MIN_ANSWERS:
        tnimike_index = report_cols.index("tehtavanimike")
        for item in data:
            item[tnimike_index] = REPORT_VALUE_DEFAULT  # tehtavanimike
            item[tnimike_index + 1] = REPORT_VALUE_DEFAULT  # kelpoisuus

    # remove toimintakieli data if there is default-count and it is less than min-limit
    if not is_siirto and "toimintakieli" in report_cols and 0 < toimintakieli_default_count < REPORT_MIN_ANSWERS:
        toimintakieli_index = report_cols.index("toimintakieli")
        for item in data:
            item[toimintakieli_index] = REPORT_VALUE_DEFAULT

    return data


def get_indicators_combined(kysymysryhma: Kysymysryhma, language: str = "fi") -> str:
    indicators_str = ""

    # initialize with main indicator
    main_indicator = kysymysryhma.metatiedot.get("paaIndikaattori")
    if main_indicator:
        indicator_key = main_indicator["key"]
        indicator_short = INDICATORS_SHORT_DICT[indicator_key][language]
        indicators_str = indicator_short

    # append with secondary indicators
    for indicator in kysymysryhma.metatiedot.get("sekondaariset_indikaattorit", []):
        indicator_key = indicator["key"]
        indicator_short = INDICATORS_SHORT_DICT[indicator_key][language]
        indicators_str += f", {indicator_short}"

    return indicators_str


def create_toimintakieli_counts_dict(vastaajas: QuerySet[Vastaaja], kyselys_dict: dict) -> dict:
    toimintakieli_counts = dict()
    for vastaaja in vastaajas:
        toimintakieli_codes = get_toimintakieli_combined(vastaaja, kyselys_dict)
        toimintakieli_counts.setdefault(toimintakieli_codes, 0)
        toimintakieli_counts[toimintakieli_codes] += 1
    return toimintakieli_counts


def create_tehtavanimike_counts_dict(vastaajas: QuerySet[Vastaaja]) -> dict:
    tehtavanimike_counts = dict()
    for vastaaja in vastaajas:
        koodi_kelpoisuus = get_koodi_kelpoisuus(vastaaja)
        tehtavanimike_counts.setdefault(koodi_kelpoisuus, 0)
        tehtavanimike_counts[koodi_kelpoisuus] += 1
    return tehtavanimike_counts


def create_tutkinto_counts_dict(vastaajas: QuerySet[Vastaaja]) -> dict:
    tutkinto_counts = dict()
    for vastaaja in vastaajas:
        if vastaaja.tutkinnot:
            tutkinto_codes = ",".join(sorted(list(vastaaja.tutkinnot)))
        else:
            tutkinto_codes = REPORT_VALUE_NULL
        tutkinto_counts.setdefault(tutkinto_codes, 0)
        tutkinto_counts[tutkinto_codes] += 1
    return tutkinto_counts


def create_aluejako_names_dict() -> dict:
    aluejako_objs = AluejakoAlue.objects.all()
    aluejako_names = {
        f"{alue.id}": dict(fi=alue.name_fi, sv=alue.name_sv)
        for alue in aluejako_objs}
    return aluejako_names


def get_filtered_kysymyses(kysymysryhmaid: int, language: str):
    kysymyses, kysymys_jatkokysymyses_dict = get_kysymyses_and_jatkokysymyses(kysymysryhmaid)

    kysymys_texts = []
    kysymysids = []
    filtered_kysymyses = []
    hidden_kysymysids = []
    for kysymys in kysymyses:
        # add id into hidden_kysymysids list if question is hidden
        if kysymys.metatiedot and kysymys.metatiedot.get("is_hidden_on_report", False):
            hidden_kysymysids.append(kysymys.pk)
        elif kysymys.matriisi_kysymysid and kysymys.matriisi_kysymysid in hidden_kysymysids:
            hidden_kysymysids.append(kysymys.pk)

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
        filtered_kysymyses.append(kysymys)

        # add jatkokysymyses related to this kysymys
        kysymys_texts_append, kysymysids_append, filtered_kysymyses_append, hidden_kysymysids = \
            collect_jatkokysymyses_by_kysymys(kysymys, kysymys_jatkokysymyses_dict, hidden_kysymysids, language)
        kysymys_texts += kysymys_texts_append
        kysymysids += kysymysids_append
        filtered_kysymyses += filtered_kysymyses_append

    return kysymys_texts, kysymysids, filtered_kysymyses, hidden_kysymysids


def get_kysymyses_and_jatkokysymyses(kysymysryhmaid: int):
    kysymyses = Kysymys.objects.filter(
        kysymysryhmaid=kysymysryhmaid, jatkokysymys=False) \
        .order_by("jarjestys", "matriisi_jarjestys")

    jatkokysymyses = Kysymys.objects.filter(
        kysymysryhmaid=kysymysryhmaid, jatkokysymys=True).order_by("kysymysid")
    kysymys_jatkokysymyses_dict = defaultdict(list)
    if jatkokysymyses.exists():
        jatkokysymys_ids = [jatkokysymys.kysymysid for jatkokysymys in jatkokysymyses]
        kysymys_jatkokysymyses = KysymysJatkokysymys.objects.filter(
            jatkokysymysid__in=jatkokysymys_ids) \
            .select_related("kysymysid", "jatkokysymysid")
        for kysymys_jatkokysymys in kysymys_jatkokysymyses:
            kysymys_jatkokysymyses_dict[str(kysymys_jatkokysymys.kysymysid.pk)].append(kysymys_jatkokysymys)

    return kysymyses, kysymys_jatkokysymyses_dict


def collect_jatkokysymyses_by_kysymys(
        kysymys: Kysymys, kysymys_jatkokysymyses_dict: defaultdict[list], hidden_kysymysids: List[int], language: str):
    kysymys_texts = []
    kysymysids = []
    filtered_kysymyses = []

    kysymys_jatkokysymyses = kysymys_jatkokysymyses_dict.get(str(kysymys.kysymysid), [])
    if not kysymys_jatkokysymyses:
        return kysymys_texts, kysymysids, filtered_kysymyses, hidden_kysymysids

    for choice in kysymys.metatiedot.get("vastausvaihtoehdot", []):
        for kysymys_jatkokysymys in kysymys_jatkokysymyses:
            if (kysymys_jatkokysymys.kysymysid.pk == kysymys.pk and
                    kysymys_jatkokysymys.vastaus == str(choice["id"])):
                kysymys_texts.append(choice["title"][language])
                kysymysids.append(kysymys_jatkokysymys.jatkokysymysid.pk)
                filtered_kysymyses.append(kysymys_jatkokysymys)
                if kysymys.pk in hidden_kysymysids:
                    hidden_kysymysids.append(kysymys_jatkokysymys.jatkokysymysid.pk)

    return kysymys_texts, kysymysids, filtered_kysymyses, hidden_kysymysids


def create_vastauses_dict(vastaajas: QuerySet[Vastaaja], kysymyses: List[Kysymys],
                          hide_text_type_answers: bool) -> dict:
    vastauses = Vastaus.objects.filter(vastaajaid__in=vastaajas) \
        .select_related("vastaajaid").order_by("vastaajaid", "string", "numerovalinta")
    kysymyses_dict = {str(k.kysymysid): k for k in kysymyses}
    vastauses_dict = dict()
    for vastaus in vastauses:
        if vastaus.string is not None:
            if hide_text_type_answers:
                answer = REPORT_VALUE_HIDDEN
            else:
                answer = vastaus.string
        elif vastaus.numerovalinta is not None:
            answer = vastaus.numerovalinta
        elif vastaus.en_osaa_sanoa is not None:
            answer = get_eos_value(vastaus, kysymyses_dict)
        else:
            answer = REPORT_VALUE_NULL
        vastaajaid = str(vastaus.vastaajaid.pk)
        vastauses_dict.setdefault(vastaajaid, dict())
        if str(vastaus.kysymysid) in vastauses_dict[vastaajaid]:
            vastauses_dict[vastaajaid][str(vastaus.kysymysid)] += f",{answer}"
        else:
            vastauses_dict[vastaajaid][str(vastaus.kysymysid)] = str(answer)
    return vastauses_dict


def get_tehtavanimike_and_kelpoisuus(
        vastaaja: Vastaaja, tehtavanimike_counts: dict, tehtavanimike_default_count: int,
        is_siirto: bool) -> (str, str, int):
    koodi_kelpoisuus = get_koodi_kelpoisuus(vastaaja)

    if is_siirto or tehtavanimike_counts[koodi_kelpoisuus] >= REPORT_MIN_ANSWERS:
        if vastaaja.tehtavanimikkeet:
            tehtavanimike = ",".join([tnimike["tehtavanimike_koodi"] for tnimike in vastaaja.tehtavanimikkeet])
            kelpoisuus = ",".join([str(tnimike["kelpoisuus_kytkin"]) for tnimike in vastaaja.tehtavanimikkeet])
        else:
            tehtavanimike = REPORT_VALUE_NULL
            kelpoisuus = REPORT_VALUE_NULL
    else:
        tehtavanimike = REPORT_VALUE_DEFAULT
        kelpoisuus = REPORT_VALUE_DEFAULT
        tehtavanimike_default_count += 1

    return tehtavanimike, kelpoisuus.upper(), tehtavanimike_default_count


def get_tutkinto(vastaaja: Vastaaja, tutkinto_counts: dict, is_siirto: bool):
    if vastaaja.tutkinnot:
        tutkinto_codes = ",".join(sorted(list(vastaaja.tutkinnot)))
    else:
        tutkinto_codes = REPORT_VALUE_NULL

    if is_siirto or tutkinto_counts[tutkinto_codes] >= REPORT_MIN_ANSWERS:
        return tutkinto_codes
    return REPORT_VALUE_DEFAULT


def get_toimintamuodot(kyselykertas: QuerySet[Kyselykerta], vastaaja: Vastaaja) -> str:
    try:
        kyselykerta = Kyselykerta.objects.none()
        for kk in kyselykertas:
            if kk.kyselyid.pk == vastaaja.kyselyid:
                kyselykerta = kk
                break
        return str(kyselykerta.metatiedot["rakennetekijalomake_data"]["toimipaikat"]["toimintamuodot"])
    except Exception as e:
        logger.warning(f"Error getting toimintamuodot value. Error: {e}")
    return REPORT_VALUE_NULL


def get_toimintakieli(vastaaja, kyselys_dict, toimintakieli_counts,
                      toimintakieli_default_count: int, is_siirto: bool) -> (str, int):
    toimintakieli_combined = get_toimintakieli_combined(vastaaja, kyselys_dict)
    if is_siirto or toimintakieli_counts[toimintakieli_combined] >= REPORT_MIN_ANSWERS:
        return toimintakieli_combined, toimintakieli_default_count
    toimintakieli_default_count += 1
    return REPORT_VALUE_DEFAULT, toimintakieli_default_count


def get_toimintakieli_combined(vastaaja: Vastaaja, kyselys_dict: dict) -> str:
    kysely = kyselys_dict.get(str(vastaaja.kyselyid))
    if kysely and kysely.oppilaitos:
        language_codes = kysely.oppilaitos.metatiedot.get("toimintakieli_koodi", [])
        report_language_codes = get_report_language_codes(language_codes)
        return ",".join(sorted(list(report_language_codes)))
    return REPORT_VALUE_NULL


def get_lapset_voimassa(kyselykertas: QuerySet[Kyselykerta], vastaaja: Vastaaja) -> str:
    try:
        kyselykerta = Kyselykerta.objects.none()
        for kk in kyselykertas:
            if kk.kyselyid.pk == vastaaja.kyselyid:
                kyselykerta = kk
                break
        return str(kyselykerta.metatiedot["rakennetekijalomake_data"]["lapset_voimassa"])
    except Exception as e:
        logger.warning(f"Error getting lapset_voimassa value. Error: {e}")
    return REPORT_VALUE_NULL


def get_tuen_tiedot(kyselykertas: QuerySet[Kyselykerta], vastaaja: Vastaaja) -> str:
    try:
        kyselykerta = Kyselykerta.objects.none()
        for kk in kyselykertas:
            if kk.kyselyid.pk == vastaaja.kyselyid:
                kyselykerta = kk
                break
        return str(kyselykerta.metatiedot["rakennetekijalomake_data"]["tuen_tiedot"])
    except Exception as e:
        logger.warning(f"Error getting tuen_tiedot value. Error: {e}")
    return REPORT_VALUE_NULL


def get_henkilosto_values(kyselykertas: QuerySet[Kyselykerta], vastaaja: Vastaaja,
                          report_cols: List[str]) -> (str, str, str):
    if not set(["henkilosto_total", "henkilosto_tn", "henkilosto_kelp"]).intersection(set(report_cols)):
        return REPORT_VALUE_NULL, REPORT_VALUE_NULL, REPORT_VALUE_NULL

    try:
        kyselykerta = Kyselykerta.objects.none()
        for kk in kyselykertas:
            if kk.kyselyid.pk == vastaaja.kyselyid:
                kyselykerta = kk
                break
        tyontekija_data = kyselykerta.metatiedot["rakennetekijalomake_data"]["tyontekijat"]
        henkilosto_total = str(tyontekija_data["total"])
        henkilosto_tehtavanimikkeet = str(tyontekija_data["tehtavanimikkeet"])
        henkilosto_kelpoiset = str(tyontekija_data["tehtavanimikkeet_kelpoiset"])
        return henkilosto_total, henkilosto_tehtavanimikkeet, henkilosto_kelpoiset
    except Exception as e:
        logger.warning(f"Error getting henkilosto values. Error: {e}")
    return REPORT_VALUE_NULL, REPORT_VALUE_NULL, REPORT_VALUE_NULL


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

        if "taydennyskoulutukset" not in kyselykerta.metatiedot:
            return "", "", ""

        koulutus_data = kyselykerta.metatiedot["taydennyskoulutukset"]
        koulutus_pv = koulutus_data["koulutuspaivat"]
        koulutus_tehtavanimikkeet = str(koulutus_data["tehtavanimikkeet"])
        koulutus_tehtavanimikkeet_pv = str(koulutus_data["tehtavanimikkeet_koulutuspaivat"])
        return koulutus_pv, koulutus_tehtavanimikkeet, koulutus_tehtavanimikkeet_pv
    except Exception as e:
        logger.error(f"Error getting taydennyskoulutukset values. Error: {e}")
    return "", "", ""


def get_yritysmuoto(koulutustoimija: Organisaatio):
    if koulutustoimija.metatiedot:
        return koulutustoimija.metatiedot.get("yritysmuoto", REPORT_VALUE_NULL)
    return REPORT_VALUE_NULL


def get_aluejako_name(kysely: Kysely, aluejako_names: dict, language: str) -> str:
    if kysely.oppilaitos:
        aluejako_id = kysely.oppilaitos.metatiedot.get("aluejako", 0)
        if aluejako_id and str(aluejako_id) in aluejako_names:
            return aluejako_names[str(aluejako_id)][language]

    return REPORT_VALUE_NULL


def get_oppilaitos_data(kysely: Kysely):
    toimipaikka = dict(
        oid=REPORT_VALUE_NULL,
        nimi=REPORT_VALUE_NULL,
        postinumero=REPORT_VALUE_NULL,
        jarjestamismuoto=REPORT_VALUE_NULL,
        toimintamuoto=REPORT_VALUE_NULL)
    if kysely.oppilaitos:
        if kysely.oppilaitos.postinumero:
            censored_postinumero = kysely.oppilaitos.postinumero[:3] + "XX"
            toimipaikka["postinumero"] = censored_postinumero

        toimipaikka["oid"] = kysely.oppilaitos.oid
        toimipaikka["nimi"] = kysely.oppilaitos.nimi_fi
        toimipaikka["jarjestamismuoto"] = kysely.oppilaitos.metatiedot.get("jarjestamismuoto_koodit", REPORT_VALUE_NULL)
        toimipaikka["toimintamuoto"] = kysely.oppilaitos.metatiedot.get("toimintamuoto_koodi", REPORT_VALUE_NULL)

    return toimipaikka


def get_koodi_kelpoisuus(vastaaja: Vastaaja) -> str:
    if vastaaja.tehtavanimikkeet:
        tehtavanimike_pairs = []
        for tnimike in vastaaja.tehtavanimikkeet:
            tehtavanimike_pairs.append(
                f"{tnimike['tehtavanimike_koodi']}-{tnimike['kelpoisuus_kytkin']}")
        return "-".join(sorted(list(tehtavanimike_pairs)))
    return REPORT_VALUE_NULL


def get_eos_value(vastaus: Vastaus, kysymyses: dict, language: str = "fi"):
    kysymys = kysymyses.get(str(vastaus.kysymysid))
    if kysymys:
        eos_value = REPORT_EOS_VALUE_BY_SCALE.get(kysymys.vastaustyyppi)
        if eos_value:
            return eos_value[language]
    return REPORT_EOS_VALUE_DEFAULT[language]


def create_lomake_usage_csv_by_kyselys(kyselys: QuerySet[Kysely], date1: str, date2: str, language: str):
    data = create_lomake_usage_csv_data(kyselys, date1, date2, language)
    col_names = [LOMAKE_USAGE_EXPORT_COL_TRANSLATIONS[col][language] for col in LOMAKE_USAGE_EXPORT_COLS]
    df = pd.DataFrame(data, columns=col_names)
    csv_file = df.to_csv(sep=CSV_DELIMITER, index=False, encoding="utf-8")
    return csv_file


def create_lomake_usage_csv_data(kyselys: QuerySet[Kysely], date1: str, date2: str, language: str) -> list:
    data = []

    kyselykierros_result_str_set = create_kyselykierros_result_str_set(kyselys)
    kysely_ids_sent_set = set(Vastaajatunnus.objects.values_list("kyselykertaid__kyselyid", flat=True))

    kyselykierros_already = set()
    for kysely in kyselys:
        kysymysryhma = kysely.kysymysryhmat.first()

        kysymysryhmaid = kysymysryhma.kysymysryhmaid
        koulutustoimija_oid = kysely.koulutustoimija.oid
        voimassa_alkupvm = kysely.voimassa_alkupvm
        kyselykierros_str = f"{kysymysryhmaid}-{koulutustoimija_oid}-{voimassa_alkupvm}"

        # Skip if kyselykierros already added
        if kyselykierros_str in kyselykierros_already:
            continue

        kysymysryhma_name = kysymysryhma.nimi_fi if language == "fi" else kysymysryhma.nimi_sv
        yritysmuoto = get_yritysmuoto(kysely.koulutustoimija)
        koulutustoimija_name = kysely.koulutustoimija.nimi_fi if language == "fi" else kysely.koulutustoimija.nimi_sv
        kuntakoodi = kysely.koulutustoimija.kunta
        voimassa_loppupvm = kysely.voimassa_loppupvm

        is_results_done = REPORT_VALUE_TRUE if kyselykierros_str in kyselykierros_result_str_set else REPORT_VALUE_FALSE

        is_lomake_sent = REPORT_VALUE_TRUE if kysely.kyselyid in kysely_ids_sent_set else REPORT_VALUE_FALSE

        cols_data = []
        cols_data += [date1] if "voimassa_pvm1" in LOMAKE_USAGE_EXPORT_COLS else []
        cols_data += [date2] if "voimassa_pvm2" in LOMAKE_USAGE_EXPORT_COLS else []
        cols_data += [kysymysryhma_name] if "lomake_nimi" in LOMAKE_USAGE_EXPORT_COLS else []
        cols_data += [yritysmuoto] if "yritysmuoto" in LOMAKE_USAGE_EXPORT_COLS else []
        cols_data += [koulutustoimija_name] if "koulutustoimija_name" in LOMAKE_USAGE_EXPORT_COLS else []
        cols_data += [kuntakoodi] if "kuntakoodi" in LOMAKE_USAGE_EXPORT_COLS else []
        cols_data += [voimassa_loppupvm] if "voimassa_loppupvm" in LOMAKE_USAGE_EXPORT_COLS else []
        cols_data += [is_results_done] if "is_results_done" in LOMAKE_USAGE_EXPORT_COLS else []
        cols_data += [is_lomake_sent] if "is_lomake_sent" in LOMAKE_USAGE_EXPORT_COLS else []

        data.append(cols_data)
        kyselykierros_already.add(kyselykierros_str)

    return data


def create_kyselykierros_result_str_set(kyselys: QuerySet[Kysely]) -> Set[str]:
    # Use oids to narrow Result queryset
    koulutustoimija_oids = {kysely.koulutustoimija.oid for kysely in kyselys}
    results = (
        Result.objects.filter(is_locked=True, koulutustoimija__in=koulutustoimija_oids)
        .values("kysymysryhmaid", "koulutustoimija", "kysely_voimassa_alkupvm")
    )

    return {
        f"{result['kysymysryhmaid']}-{result['koulutustoimija']}-"
        f"{result['kysely_voimassa_alkupvm'].strftime(DATE_INPUT_FORMAT)}"
        for result in results
    }
