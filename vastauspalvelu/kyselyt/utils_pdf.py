import logging
import weasyprint

from collections import defaultdict
from time import sleep
from typing import List

from django.conf import settings
from django.db.models import QuerySet
from django.template.loader import render_to_string
from rest_framework import status

from kyselyt.constants import (
    PDF_FILENAME_SUFFIX, VIESTINTAPALVELU_SETTINGS, SUCCESS_STATUSES, PDF_INDICATOR_INFO_TRANSLATIONS,
    EOS_TRANSLATIONS, PDF_LOGO_PATHS, MAX_NO_OF_LOOPS, DATE_INPUT_FORMAT, PDF_INDICATORS_NO_INDICATORS,
    PDF_NO_INDICATORS_TRANSLATIONS, PDF_TRANSLATION_MISSING_TEXT, EOS_TRANSLATION_DEFAULT,
)
from kyselyt.models import Kyselykerta, Vastaaja, Vastaus, Kysymysryhma, Kysymys, Kysely, KysymysJatkokysymys
from kyselyt.tokens import TOKENS
from kyselyt.utils import get_localisation_values_by_key, request_service
from kyselyt.utils_auth import get_access_token_for_palvelu, get_scales


logger = logging.getLogger(__name__)

SCALES = dict()  # temporary store for scales


def post_answer_pdf_to_viestintapalvelu(email: str, vastaajaid: int, language: str):
    token = get_access_token_for_palvelu(VIESTINTAPALVELU_SETTINGS)
    if not token:
        log_msg = "Vastauspalvelu not able to get viestintapalvelu access token."
        logger.warning(log_msg)
        return log_msg

    # update SCALES
    scales = update_global_scales()
    if scales is None:
        log_msg = "Vastauspalvelu not able to get scales from Virkailijapalvelu."
        logger.error(log_msg)
        return log_msg

    # create pdf document
    pdf_file = create_answer_pdf(vastaajaid, language)

    # email attachment filename
    vastaaja = Vastaaja.objects.get(vastaajaid=vastaajaid)
    filename = vastaaja.vastaajatunnus + PDF_FILENAME_SUFFIX[language]

    kysely = Kysely.objects.get(pk=vastaaja.kyselyid)
    end_date = kysely.voimassa_loppupvm.strftime(DATE_INPUT_FORMAT)

    # send pdf to viestintapalvelu
    for i in range(MAX_NO_OF_LOOPS):
        resp = request_service(
            "Viestintapalvelu", "post",
            f"{settings.VIESTINTAPALVELU_URL}/api/v1/pdfsend/", token,
            data=dict(filename=filename, email=email, end_date=end_date),
            files=dict(pdf_file=pdf_file))

        if resp is None:
            pass
        elif resp.status_code in SUCCESS_STATUSES:
            return "OK"
        elif resp.status_code == status.HTTP_401_UNAUTHORIZED:
            logger.info("Viestintapalvelu read: 401 Unauthorized.")
            TOKENS["viestintapalvelu"] = None
            logger.info("Viestintapalvelu expired access token removed.")
            token = get_access_token_for_palvelu(VIESTINTAPALVELU_SETTINGS)  # update token
        else:
            logger.error(f"Viestintapalvelu read error, http status code: {resp.status_code}. Error: {resp.text}")
        sleep(2)

    log_msg = f"Viestintapalvelu pdf send max retries ({MAX_NO_OF_LOOPS}) exceeded."
    logger.error(log_msg)
    return log_msg


def create_answer_pdf(vastaajaid: int, language: str):
    vastaaja = Vastaaja.objects.get(vastaajaid=vastaajaid)
    content_html = create_content_html(vastaaja, language)
    stylesheet = weasyprint.CSS("kyselyt/css/kysely_pdf_style.css")
    pdf_file = weasyprint.HTML(string=content_html, base_url=".").write_pdf(stylesheets=[stylesheet])
    return pdf_file


def create_content_html(vastaaja: Vastaaja, language: str) -> str:
    kysely = get_kysely_by_kyselykertaid(vastaaja.kyselykertaid)
    vastaukset = Vastaus.objects.filter(vastaajaid=vastaaja)

    kysymysryhma = kysely["kysymysryhmat"][0] if kysely["kysymysryhmat"] else None
    indicator_texts = pdf_indicator_texts(kysymysryhma, language) if kysymysryhma else []
    kysymys_list = pdf_html_kysymysryhma_kysymykset(
        kysymysryhma, language, vastaukset) if kysymysryhma else None
    kysymysryhma_name = kysymysryhma["nimi"].get(language, PDF_TRANSLATION_MISSING_TEXT) if kysymysryhma else ""

    html_string = render_to_string(
        "kysely_pdf.html", {
            "logo_src": PDF_LOGO_PATHS[language],
            "kysymysryhma_name": kysymysryhma_name,
            "indicator_title": PDF_INDICATOR_INFO_TRANSLATIONS[language],
            "indicator_texts": indicator_texts})
    if kysymys_list:
        html_string = html_string.replace("(((KYSYMYS_CONTENT)))", "".join(kysymys_list))

    return html_string


def pdf_html_kysymysryhma_kysymykset(
        kysymysryhma: List[dict], language: str, vastaukset: QuerySet = None
) -> List[str]:
    html_list = []
    for kysymys in kysymysryhma["kysymykset"]:
        # skip question if hidden=True or jatkokysymys=True
        if kysymys["metatiedot"].get("hidden", False) or kysymys["jatkokysymys"]:
            continue

        vastaustyyppi = kysymys["vastaustyyppi"]
        kysymys_type = kysymys["metatiedot"].get("type", "")
        vastaus = vastaukset.filter(kysymysid=kysymys["kysymysid"]) if vastaukset else None

        # intertitle (väliotsikko)
        if kysymys_type == "statictext":
            html_list += pdf_html_intertitle(kysymys, language)

        # question (not matrix subquestion)
        elif not kysymys["matriisi_jarjestys"]:
            html_list += pdf_html_question_and_description(kysymys, language)

        # textfields (tekstikenttä, monirivinen tekstikenttä, numerokenttä)
        if kysymys_type == "string":
            vastaus_content = vastaus.first().string if vastaus and vastaus.first().string else ""
            html_list += pdf_html_string_kysymys_type_question(kysymys, vastaus_content)

        # multi-option field
        elif vastaustyyppi == "monivalinta":
            html_list += pdf_html_monivalinta_question(kysymys, vastaus, vastaukset, language)

        # matrix sliderscale
        elif vastaustyyppi == "matrix_root" and kysymys_type == "matrix_sliderscale":
            html_list += pdf_html_matrix_question(
                kysymysryhma, kysymys["matriisi_kysymysid"], language, "slider", vastaukset)

        # matrix radiobutton
        elif vastaustyyppi == "matrix_root" and kysymys_type == "matrix_radiobutton":
            html_list += pdf_html_matrix_question(
                kysymysryhma, kysymys["matriisi_kysymysid"], language, "radio", vastaukset)

    return html_list


def pdf_html_intertitle(kysymys: dict, language: str) -> List[str]:
    description = kysymys["metatiedot"].get("description", None)
    rows = description[language].split("\n") if description and description.get(language, None) else []

    return [
        render_to_string(
            "kysely_pdf_intertitle.html", {
                "question": kysymys["kysymys"].get(language, PDF_TRANSLATION_MISSING_TEXT),
                "rows": rows
            }
        )
    ]


def pdf_html_string_kysymys_type_question(kysymys: dict, vastaus: str = ""):
    is_numeric = kysymys["metatiedot"].get("numeric", None)
    is_multiline = kysymys["metatiedot"].get("multiline", None)

    field_type = ""
    vastaus_lines = []

    # textfield (tekstikenttä)
    if not is_numeric and not is_multiline:
        field_type = "textfield"

    # multiline textfield (monirivinen tekstikenttä)
    elif not is_numeric and is_multiline:
        field_type = "multiline"
        vastaus_lines = [line_content for line_content in vastaus.split("\n")]

    # numeric textfield (numerokenttä)
    elif is_numeric and not is_multiline:
        field_type = "numeric"

    return [render_to_string(
        "kysely_pdf_textfield.html", {
            "field_type": field_type,
            "vastaus": vastaus,
            "vastaus_lines": vastaus_lines})]


def pdf_html_question_and_description(kysymys: dict, language: str) -> List[str]:
    mandatory_append = " *" if kysymys["pakollinen"] and kysymys["matriisi_kysymysid"] is None else ""
    description = kysymys["metatiedot"].get("description", None)
    description_text = description[language] if description and description.get(language, None) else None

    return [
        render_to_string(
            "kysely_pdf_question.html", {
                "question": kysymys["kysymys"].get(language, PDF_TRANSLATION_MISSING_TEXT),
                "mandatory_append": mandatory_append,
                "description": description_text,
            }
        )
    ]


def pdf_html_monivalinta_question(kysymys, vastaus, vastaukset, language):
    kysymys_type = kysymys["metatiedot"].get("type", "")
    checkeds = set(vastaus.values_list("numerovalinta", flat=True)) if vastaus else set()

    # multi-option field, 1-choose, radiobutton (monivalinta 1-valinta)
    if kysymys_type == "radiobutton":
        return pdf_html_monivalinta_question_by_type(kysymys, language, "radio", vastaukset, checkeds)

    # multi-option field, multi-choose, checkbox (monivalinta usea-valinta)
    elif kysymys_type == "checkbox":
        return pdf_html_monivalinta_question_by_type(kysymys, language, "checkbox", vastaukset, checkeds)

    # multi-option field, 1-choose, dropdown (monivalinta pudotusvalikko) (radiobutton-outfit is used)
    elif kysymys_type == "dropdown":
        return pdf_html_monivalinta_question_by_type(kysymys, language, "radio", vastaukset, checkeds)

    return [""]


def pdf_html_monivalinta_question_by_type(
    kysymys: dict, language: str, monivalinta_type: str, vastaukset: QuerySet, checkeds: set = set()
) -> List[str]:
    choices = []
    for i, choice in enumerate(kysymys["metatiedot"].get("vastausvaihtoehdot", [])):
        checked = "checked" if choice["checked"] or choice["id"] in checkeds else ""
        title = choice["title"].get(language, PDF_TRANSLATION_MISSING_TEXT) if "title" in choice else "(title missing)"
        description = choice.get("description", None)
        description_text = description[language] if description and description.get(language, None) else None

        jatkokysymys = None
        for jatkokysymys_obj in kysymys["jatkokysymys_kysymys"]:
            if jatkokysymys_obj.kysymysid.pk == kysymys["kysymysid"] and jatkokysymys_obj.vastaus == str(choice["id"]):
                jatkokysymys = jatkokysymys_obj
                break

        jatkokysymys_text = "" if jatkokysymys else None
        if jatkokysymys and vastaukset:
            vastaus = vastaukset.filter(kysymysid=jatkokysymys.jatkokysymysid.pk)
            jatkokysymys_text = vastaus.first().string if vastaus.exists() and vastaus.first().string else ""

        choices.append(dict(
            index=i, checked=checked, title=title,
            description=description_text,
            jatkokysymys=jatkokysymys_text))

    return [
        render_to_string(
            "kysely_pdf_multioption.html", {
                "monivalinta_type": monivalinta_type,
                "kysymysid": kysymys["kysymysid"],
                "choices": choices
            }
        )
    ]


def pdf_html_matrix_question(kysymysryhma: dict, matriisi_kysymysid: int, language: str, matrix_type: str,
                             vastaukset: QuerySet = None) -> List[str]:
    vastaustyyppi = next((
        kysymys["vastaustyyppi"] for kysymys in kysymysryhma["kysymykset"]
        if kysymys["matriisi_kysymysid"] == matriisi_kysymysid and kysymys["vastaustyyppi"] != "matrix_root"), None)
    scale = get_scale(vastaustyyppi)
    if scale is None:
        return []

    if not kysymysryhma["kysymykset"]:
        return []

    subquestions = []
    for kysymys in kysymysryhma["kysymykset"]:
        if kysymys["matriisi_kysymysid"] == matriisi_kysymysid and kysymys["vastaustyyppi"] != "matrix_root":
            # skip hidden subquestions
            if kysymys["metatiedot"].get("hidden", None):
                continue
            mandatory_append = " *" if kysymys["pakollinen"] else ""
            description = kysymys["metatiedot"].get("description", None)
            description_text = description[language] if description and description.get(language, None) else None

            vastaus = vastaukset.filter(kysymysid=kysymys["kysymysid"]) if vastaukset else None
            checkeds = set(vastaus.values_list("numerovalinta", flat=True)) if vastaus else set()
            slidermarks = [
                dict(index=i, percentage=int(100.0 / (scale["step_count"] - 1) * i),
                     checked="-checked" if i + 1 in checkeds else "")
                for i in range(scale["step_count"])]
            radiobuttons = [dict(checked="checked" if i + 1 in checkeds else "") for i in range(scale["step_count"])]
            eos_checked = "checked" if vastaus and vastaus.first().en_osaa_sanoa else ""

            subquestions.append(
                dict(
                    question=kysymys["kysymys"].get(language, PDF_TRANSLATION_MISSING_TEXT),
                    mandatory_append=mandatory_append,
                    description=description_text,
                    slidermarks=slidermarks,
                    radiobuttons=radiobuttons,
                    eos=dict(
                        text=get_eos_translation(kysymys["vastaustyyppi"])[language],
                        allowed=kysymys["eos_vastaus_sallittu"],
                        checked=eos_checked,
                    ),
                )
            )

    return [
        render_to_string(
            "kysely_pdf_matrix.html", {
                "matrix_type": matrix_type,
                "scale_step_count": scale["step_count"],
                "scale_first": scale["scale"][0][language],
                "scale_last": scale["scale"][-1][language],
                "scale_middles": [scale_point[language] for scale_point in scale["scale"][1:-1]],
                "scale_points": [scale_point[language] for scale_point in scale["scale"]],
                "subquestions": subquestions,
            }
        )
    ]


def pdf_indicator_texts(kysymysryhma: dict, language: str) -> List[str]:
    texts = []
    main_indicator_key = kysymysryhma["paaindikaattori"].get("key", None)

    # "No indicators" on pdf with specific indicators
    if main_indicator_key in PDF_INDICATORS_NO_INDICATORS:
        return [PDF_NO_INDICATORS_TRANSLATIONS[language]]

    if main_indicator_key:
        localisation_key = f"indik.desc_{main_indicator_key}"
        indicator_text = get_localisation_values_by_key(localisation_key)[language]
        texts += [indicator_text]

    secondary_indicator_keys = [indicator.get("key") for indicator in kysymysryhma["sekondaariset_indikaattorit"]]
    for indicator_key in secondary_indicator_keys:
        if not indicator_key:
            continue
        localisation_key = f"indik.desc_{indicator_key}"
        indicator_text = get_localisation_values_by_key(localisation_key)[language]
        texts += [indicator_text]

    return texts


def get_kysely_by_kyselykertaid(kyselykertaid: int) -> dict:
    kyselykerta = Kyselykerta.objects.get(kyselykertaid=kyselykertaid)
    kysymysryhmat_data = [
        dict(
            nimi=dict(
                fi=kysymysryhma.nimi_fi,
                sv=kysymysryhma.nimi_sv,
                en=kysymysryhma.nimi_en,
            ),
            selite=dict(
                fi=kysymysryhma.selite_fi,
                sv=kysymysryhma.selite_sv,
                en=kysymysryhma.selite_en,
            ),
            tila=kysymysryhma.tila.nimi,
            kuvaus=dict(
                fi=kysymysryhma.kuvaus_fi,
                sv=kysymysryhma.kuvaus_sv,
                en=kysymysryhma.kuvaus_en,
            ),
            paaindikaattori=kysymysryhma.metatiedot.get("paaIndikaattori", {}),
            sekondaariset_indikaattorit=kysymysryhma.metatiedot.get("sekondaariset_indikaattorit", []),
            kysymykset=get_kysymykset_by_kysymysryhma(kysymysryhma))
        for kysymysryhma in kyselykerta.kyselyid.kysymysryhmat.all()
    ]

    return dict(kysymysryhmat=kysymysryhmat_data)


def get_kysymykset_by_kysymysryhma(kysymysryhma: Kysymysryhma):
    kysymys_list = Kysymys.objects.filter(kysymysryhmaid=kysymysryhma).order_by("jarjestys", "matriisi_jarjestys")
    kysymys_is_jatkokysymys_ids = {kysymys.kysymysid for kysymys in kysymys_list if kysymys.jatkokysymys}
    jatkokysymys_list = KysymysJatkokysymys.objects.filter(
        jatkokysymysid__in=kysymys_is_jatkokysymys_ids) \
        .select_related("kysymysid", "jatkokysymysid")
    jatkokysymys_dict = defaultdict(list)
    for jatkokysymys in jatkokysymys_list:
        jatkokysymys_dict[str(jatkokysymys.kysymysid.pk)].append(jatkokysymys)

    return [
        dict(
            kysymysid=kysymys.kysymysid,
            pakollinen=kysymys.pakollinen,
            vastaustyyppi=kysymys.vastaustyyppi,
            kysymys=dict(
                fi=kysymys.kysymys_fi,
                sv=kysymys.kysymys_sv,
                en=kysymys.kysymys_en,
            ),
            jarjestys=kysymys.jarjestys,
            monivalinta_max=kysymys.monivalinta_max,
            max_vastaus=kysymys.max_vastaus,
            eos_vastaus_sallittu=kysymys.eos_vastaus_sallittu,
            jatkokysymys=kysymys.jatkokysymys,
            jatkokysymys_kysymys=jatkokysymys_dict.get(str(kysymys.kysymysid), []),
            selite=dict(
                fi=kysymys.selite_fi,
                sv=kysymys.selite_sv,
                en=kysymys.selite_en,
            ),
            matriisi_kysymysid=kysymys.matriisi_kysymysid,
            matriisi_jarjestys=kysymys.matriisi_jarjestys,
            metatiedot=kysymys.metatiedot)
        for kysymys in kysymys_list
    ]


def get_scale(name: str) -> dict:
    return SCALES.get(name, None)


def update_global_scales():
    scales = get_scales()
    if scales is not None:
        for scale in scales:
            SCALES[scale["name"]] = scale
    return scales


def get_eos_translation(scale_type: str) -> dict:
    if scale_type in EOS_TRANSLATIONS.keys():
        return EOS_TRANSLATIONS[scale_type]
    return EOS_TRANSLATION_DEFAULT
