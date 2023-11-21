import logging
import weasyprint
import pandas as pd

from typing import List

from django.template.loader import render_to_string

from raportointi.constants import (
    SUMMARY_TRANSLATIONS, PDF_LOGO_PATHS, CSV_DELIMITER, MAIN_INDICATOR_TITLE, SECONDARY_INDICATORS_TITLE)
from raportointi.models import Summary, Kysely, Result, Organisaatio
from raportointi.utils import get_localisation_values_by_key

logger = logging.getLogger(__name__)


def create_summary_pdf(content: dict, language: str = "fi"):
    content_html = create_summary_html(content, language)
    stylesheet = weasyprint.CSS("raportointi/css/summary_pdf_style.css")
    pdf_file = weasyprint.HTML(string=content_html, base_url=".").write_pdf(stylesheets=[stylesheet])
    return pdf_file


def create_summary_html(content: dict, language: str = "fi") -> str:
    main_indicator_str, secondary_indicators_str = get_indicators_strs_by_keys(
        main_indicator_key=content["main_indicator_key"],
        secondary_indicator_keys=content["secondary_indicator_keys"],
        language=language)
    html_string = render_to_string(
        "summary_pdf.html", {
            "logo_src": PDF_LOGO_PATHS[language],
            "title": content["title"],
            "main_indicator_title": MAIN_INDICATOR_TITLE[language],
            "main_indicator": main_indicator_str,
            "secondary_indicators_title": SECONDARY_INDICATORS_TITLE[language],
            "secondary_indicators": secondary_indicators_str,
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

    column_names = \
        {
            "group_info": f"{st['summary_title']['fi']} / {st['summary_title']['sv']}",
            "kuvaus": f"{st['kuvaus']['fi']} / {st['kuvaus']['sv']}",
            "aineisto": f"{st['aineisto']['fi']} / {st['aineisto']['sv']}",
            "vahvuudet": f"{st['vahvuudet']['fi']} / {st['vahvuudet']['sv']}",
            "kohteet": f"{st['kohteet']['fi']} / {st['kohteet']['sv']}",
            "keh_toimenpiteet": f"{st['keh_toimenpiteet']['fi']} / {st['keh_toimenpiteet']['sv']}",
            "seur_toimenpiteet": f"{st['seur_toimenpiteet']['fi']} / {st['seur_toimenpiteet']['sv']}"
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
                                       koulutustoimija: str) -> List[dict]:
    summary_objs = Summary.objects.filter(
        kysymysryhmaid=kysymysryhmaid,
        kysely_voimassa_alkupvm=kysely_voimassa_alkupvm,
        koulutustoimija=koulutustoimija,
        is_locked=True)
    koulutustoimija_obj = Organisaatio.objects.filter(oid=koulutustoimija).first()
    koulutustoimija_name = dict(fi=koulutustoimija_obj.nimi_fi, sv=koulutustoimija_obj.nimi_sv)
    summaries = [{
        "id": obj.id,
        "oppilaitos": obj.oppilaitos,
        "koulutustoimija_name": koulutustoimija_name,
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


def get_indicators_strs_by_keys(main_indicator_key: str, secondary_indicator_keys: List[str] = [],
                                language: str = "fi") -> (str, str):
    main_indicator_str = get_localisation_values_by_key(main_indicator_key)[language]
    secondary_indicator_strs = [get_localisation_values_by_key(key)[language] for key in secondary_indicator_keys]

    return main_indicator_str, ", ".join(secondary_indicator_strs)
