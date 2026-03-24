import logging
import pandas as pd
import weasyprint

from datetime import date
from typing import List

from django.template.loader import render_to_string

from raportointi.constants import (
    SUMMARY_TRANSLATIONS, PDF_LOGO_PATHS, CSV_DELIMITER, PDF_INDICATOR_INFO_TRANSLATIONS, PDF_INDICATORS_NO_INDICATORS,
    PDF_NO_INDICATORS_TRANSLATIONS,
)
from raportointi.models import Summary, Kysely, Result, Organisaatio, Kyselykerta
from raportointi.utils import get_localisation_values_by_key

logger = logging.getLogger(__name__)


def create_summary_pdf(content: dict, language: str = "fi"):
    content_html = create_summary_html(content, language)
    stylesheet = weasyprint.CSS("raportointi/css/summary_pdf_style.css")
    pdf_file = weasyprint.HTML(string=content_html, base_url=".").write_pdf(stylesheets=[stylesheet])
    return pdf_file


def create_summary_html(content: dict, language: str = "fi") -> str:
    indicator_keys = [content["main_indicator_key"]] + content["secondary_indicator_keys"]
    indicator_texts = pdf_indicator_texts(indicator_keys, language)
    html_string = render_to_string(
        "summary_pdf.html", {
            "logo_src": PDF_LOGO_PATHS[language],
            "title": content["title"],
            "indicator_title": PDF_INDICATOR_INFO_TRANSLATIONS[language],
            "indicator_texts": indicator_texts,
            "koulutustoimija": content["koulutustoimija"],
            "group_info": content["group_info"],

            "title_kuvaus": SUMMARY_TRANSLATIONS["kuvaus"][language],
            "content_kuvaus": content["kuvaus"].split("\n"),

            "title_aineisto": SUMMARY_TRANSLATIONS["aineisto"][language],
            "content_aineisto": content["aineisto"].split("\n"),

            "title_vahvuudet": SUMMARY_TRANSLATIONS["vahvuudet"][language],
            "content_vahvuudet": content["vahvuudet"].split("\n"),

            "title_kohteet": SUMMARY_TRANSLATIONS["kohteet"][language],
            "content_kohteet": content["kohteet"].split("\n"),

            "title_keh_toimenpiteet": SUMMARY_TRANSLATIONS["keh_toimenpiteet"][language],
            "content_keh_toimenpiteet": content["keh_toimenpiteet"].split("\n"),

            "title_seur_toimenpiteet": SUMMARY_TRANSLATIONS["seur_toimenpiteet"][language],
            "content_seur_toimenpiteet": content["seur_toimenpiteet"].split("\n")
        },)

    return html_string


def create_summary_csv(summaries: List[dict]):
    df = pd.DataFrame(summaries)
    df = df.drop(["id", "oppilaitos", "taustatiedot"], axis=1)
    st = SUMMARY_TRANSLATIONS

    column_names = {
        "koulutustoimija_name": f"{st['koulutustoimija']['fi']} / {st['koulutustoimija']['sv']}",
        "kysely_voimassa_alkupvm": f"{st['alkupvm']['fi']} / {st['alkupvm']['sv']}",
        "group_info": f"{st['summary_title']['fi']} / {st['summary_title']['sv']}",
        "kuvaus": f"{st['kuvaus']['fi']} / {st['kuvaus']['sv']}",
        "aineisto": f"{st['aineisto']['fi']} / {st['aineisto']['sv']}",
        "vahvuudet": f"{st['vahvuudet']['fi']} / {st['vahvuudet']['sv']}",
        "kohteet": f"{st['kohteet']['fi']} / {st['kohteet']['sv']}",
        "keh_toimenpiteet": f"{st['keh_toimenpiteet']['fi']} / {st['keh_toimenpiteet']['sv']}",
        "seur_toimenpiteet": f"{st['seur_toimenpiteet']['fi']} / {st['seur_toimenpiteet']['sv']}",
    }

    df.rename(columns=column_names, inplace=True)
    csv_file = df.to_csv(sep=CSV_DELIMITER, index=False, encoding="utf-8")
    return csv_file


def create_result_csv(results: List[dict]):
    df = pd.DataFrame(results)
    df = df.drop(["id", "taustatiedot"], axis=1)
    st = SUMMARY_TRANSLATIONS

    column_names = {
        "koulutustoimija_name": f"{st['koulutustoimija']['fi']} / {st['koulutustoimija']['sv']}",
        "kysely_voimassa_alkupvm": f"{st['alkupvm']['fi']} / {st['alkupvm']['sv']}",
        "kuvaus": f"{st['kuvaus']['fi']} / {st['kuvaus']['sv']}",
        "aineisto": f"{st['aineisto']['fi']} / {st['aineisto']['sv']}",
        "vahvuudet": f"{st['vahvuudet']['fi']} / {st['vahvuudet']['sv']}",
        "kohteet": f"{st['kohteet']['fi']} / {st['kohteet']['sv']}",
        "keh_toimenpiteet": f"{st['keh_toimenpiteet']['fi']} / {st['keh_toimenpiteet']['sv']}",
        "seur_toimenpiteet": f"{st['seur_toimenpiteet']['fi']} / {st['seur_toimenpiteet']['sv']}",
    }

    df.rename(columns=column_names, inplace=True)
    csv_file = df.to_csv(sep=CSV_DELIMITER, index=False, encoding="utf-8")
    return csv_file


def get_indicators_by_kysely(kysely: Kysely) -> (str, List[str]):
    metatiedot = kysely.kysymysryhmat.first().metatiedot
    try:
        paaindikaattori_key = metatiedot.get("paaIndikaattori").get("key", None)
    except Exception:
        paaindikaattori_key = None

    try:
        sekondaariset_ind_keys = [
            indikaattori.get("key") for indikaattori in metatiedot.get("sekondaariset_indikaattorit")]
    except Exception:
        sekondaariset_ind_keys = []

    return paaindikaattori_key, sekondaariset_ind_keys


def get_locked_summaries_by_kyselydata(kysymysryhmaid: int, kysely_voimassa_alkupvm: str,
                                       koulutustoimija: str, language: str = None) -> List[dict]:
    summary_objs = Summary.objects.filter(
        kysymysryhmaid=kysymysryhmaid,
        kysely_voimassa_alkupvm=kysely_voimassa_alkupvm,
        koulutustoimija=koulutustoimija,
        is_locked=True,
    )
    koulutustoimija_obj = Organisaatio.objects.filter(oid=koulutustoimija).first()
    koulutustoimija_name = dict(fi=koulutustoimija_obj.nimi_fi, sv=koulutustoimija_obj.nimi_sv)
    summaries = [{
        "id": obj.id,
        "oppilaitos": obj.oppilaitos,
        "koulutustoimija_name": koulutustoimija_name[language] if language else koulutustoimija_name,
        "kysely_voimassa_alkupvm": obj.kysely_voimassa_alkupvm,
        "group_info": obj.group_info,
        "kuvaus": obj.kuvaus,
        "aineisto": obj.aineisto,
        "vahvuudet": obj.vahvuudet,
        "kohteet": obj.kohteet,
        "keh_toimenpiteet": obj.keh_toimenpiteet,
        "seur_toimenpiteet": obj.seur_toimenpiteet,
        "taustatiedot": obj.taustatiedot}
        for obj in summary_objs]

    return summaries


def get_summaries_by_kysymysryhma_and_date_range(
        kysymysryhmaid: int,
        voimassa_loppupvm1: date,
        voimassa_loppupvm2: date,
        language: str,
) -> List[dict]:
    kyselykerta_objs = Kyselykerta.objects.filter(
        kyselyid__kysely__kysymysryhmaid__kysymysryhmaid=kysymysryhmaid,
        voimassa_loppupvm__range=(voimassa_loppupvm1, voimassa_loppupvm2)
    ).select_related("kyselyid__koulutustoimija")
    kyselykertas_set = {f"{obj.kyselyid.koulutustoimija.oid}-{obj.voimassa_alkupvm}" for obj in kyselykerta_objs}

    summary_objs = Summary.objects.filter(
        kysymysryhmaid=kysymysryhmaid,
        is_locked=True,
    ).order_by("kysely_voimassa_alkupvm", "group_info")
    summary_objs_filtered = [
        obj for obj in summary_objs
        if f"{obj.koulutustoimija}-{obj.kysely_voimassa_alkupvm}" in kyselykertas_set
    ]

    koulutustoimija_oids = [obj.koulutustoimija for obj in summary_objs_filtered]
    koulutustoimija_objs = Organisaatio.objects.filter(oid__in=koulutustoimija_oids)
    koulutustoimijas_dict = {obj.oid: obj for obj in koulutustoimija_objs}

    summary_dicts = []
    for obj in summary_objs_filtered:
        koulutustoimija_obj = koulutustoimijas_dict.get(obj.koulutustoimija)
        koulutustoimija_name = dict(fi=koulutustoimija_obj.nimi_fi, sv=koulutustoimija_obj.nimi_sv)

        summary_dicts.append({
            "id": obj.id,
            "oppilaitos": obj.oppilaitos,
            "koulutustoimija_name": koulutustoimija_name[language],
            "kysely_voimassa_alkupvm": obj.kysely_voimassa_alkupvm,
            "group_info": obj.group_info,
            "kuvaus": obj.kuvaus,
            "aineisto": obj.aineisto,
            "vahvuudet": obj.vahvuudet,
            "kohteet": obj.kohteet,
            "keh_toimenpiteet": obj.keh_toimenpiteet,
            "seur_toimenpiteet": obj.seur_toimenpiteet,
            "taustatiedot": obj.taustatiedot,
        })

    return summary_dicts


def get_locked_results_by_koulutustoimija(koulutustoimija: str) -> List[dict]:
    result_objs = Result.objects.filter(koulutustoimija=koulutustoimija, is_locked=True)
    koulutustoimija_obj = Organisaatio.objects.filter(oid=koulutustoimija).first()
    koulutustoimija_name = dict(fi=koulutustoimija_obj.nimi_fi, sv=koulutustoimija_obj.nimi_sv)
    results = [{
        "id": obj.id,
        "kysymysryhmaid": obj.kysymysryhmaid,
        "koulutustoimija": obj.koulutustoimija,
        "koulutustoimija_name": koulutustoimija_name,
        "kysely_voimassa_alkupvm": obj.kysely_voimassa_alkupvm,
        "kuvaus": obj.kuvaus,
        "aineisto": obj.aineisto,
        "vahvuudet": obj.vahvuudet,
        "kohteet": obj.kohteet,
        "keh_toimenpiteet": obj.keh_toimenpiteet,
        "seur_toimenpiteet": obj.seur_toimenpiteet,
        "taustatiedot": obj.taustatiedot}
        for obj in result_objs]
    return results


def get_results_by_kysymysryhma_and_date_range(
        kysymysryhmaid: int,
        voimassa_loppupvm1: date,
        voimassa_loppupvm2: date,
        language: str,
) -> List[dict]:
    kyselykerta_objs = Kyselykerta.objects.filter(
        kyselyid__kysely__kysymysryhmaid__kysymysryhmaid=kysymysryhmaid,
        voimassa_loppupvm__range=(voimassa_loppupvm1, voimassa_loppupvm2)
    ).select_related("kyselyid__koulutustoimija")
    kyselykertas_set = {f"{obj.kyselyid.koulutustoimija.oid}-{obj.voimassa_alkupvm}" for obj in kyselykerta_objs}

    result_objs = Result.objects.filter(
        kysymysryhmaid=kysymysryhmaid,
        is_locked=True,
    ).order_by("kysely_voimassa_alkupvm")
    result_objs_filtered = [
        obj for obj in result_objs
        if f"{obj.koulutustoimija}-{obj.kysely_voimassa_alkupvm}" in kyselykertas_set
    ]

    koulutustoimija_oids = [obj.koulutustoimija for obj in result_objs_filtered]
    koulutustoimija_objs = Organisaatio.objects.filter(oid__in=koulutustoimija_oids)
    koulutustoimijas_dict = {obj.oid: obj for obj in koulutustoimija_objs}

    result_dicts = []
    for obj in result_objs_filtered:
        koulutustoimija_obj = koulutustoimijas_dict.get(obj.koulutustoimija)
        koulutustoimija_name = dict(fi=koulutustoimija_obj.nimi_fi, sv=koulutustoimija_obj.nimi_sv)

        result_dicts.append({
            "id": obj.id,
            "koulutustoimija_name": koulutustoimija_name[language],
            "kysely_voimassa_alkupvm": obj.kysely_voimassa_alkupvm,
            "kuvaus": obj.kuvaus,
            "aineisto": obj.aineisto,
            "vahvuudet": obj.vahvuudet,
            "kohteet": obj.kohteet,
            "keh_toimenpiteet": obj.keh_toimenpiteet,
            "seur_toimenpiteet": obj.seur_toimenpiteet,
            "taustatiedot": obj.taustatiedot,
        })

    return result_dicts


def pdf_indicator_texts(indicator_keys: List[str], language: str) -> List[str]:
    texts = []
    for indicator_key in indicator_keys:
        # "No indicators" on pdf with specific indicators
        if indicator_key in PDF_INDICATORS_NO_INDICATORS:
            return [PDF_NO_INDICATORS_TRANSLATIONS[language]]

        if not indicator_key:
            continue
        localisation_key = f"indik.desc_{indicator_key}"
        indicator_text = get_localisation_values_by_key(localisation_key)[language]
        texts += [indicator_text]

    return texts
