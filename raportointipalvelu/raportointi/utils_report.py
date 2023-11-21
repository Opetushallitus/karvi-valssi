import base64
import logging
import plotly.graph_objects as go
import plotly.io as pio
import weasyprint

from collections import defaultdict
from datetime import datetime
from typing import List

from django.db.models import Count, Q, QuerySet
from django.template.loader import render_to_string

from raportointi.constants import (
    MATRIX_GRAPH_COLORS, MATRIX_ROOT_TYPE, DEFAULT_FONT, DEFAULT_BLACK_COLOR, DEFAULT_WHITE_COLOR, REPORT_MIN_ANSWERS,
    PLOT_TRANSLATIONS, DATA_COLLECTION_TITLE, PLOTLY_FONT_SIZE, REPORT_LINK, REPORT_LINK_TEXT, PDF_LOGO_PATHS,
    REPORT_PLOT_MIN_WIDTH, MATRIX_LEGEND_X_POSITIONS, MATRIX_LEGEND_Y_POSITIONS_BY_HEIGHT, DATE_INPUT_FORMAT,
    REPORT_PERCENTAGE_TITLE, MAIN_INDICATOR_TITLE, SECONDARY_INDICATORS_TITLE)
from raportointi.models import (
    Kysymys, Vastaus, Scale, Kyselykerta, Vastaaja, Summary, Result, Vastaajatunnus, Kysymysryhma, Organisaatio)
from raportointi.utils import (
    insert_line_breaks, transform_tuples_lists_to_integers, convert_lists_to_percent, convert_lists_to_sum,
    convert_lists_to_bool_with_limit, convert_lists_to_average, convert_int_lists_to_zero_lists_if_total_lt_limit,
    get_localisation_values_by_key)
from raportointi.utils_datacollection import calculate_pct
from raportointipalvelu.settings import DEBUG


logger = logging.getLogger(__name__)


def create_report_pdf(data, language):
    """Generate a PDF report by rendering an HTML template with given data and
    converting it to PDF format."""
    html_data = create_html_report_data(data, language)

    html_string = render_to_string(
        "raportointi/report_pdf.html", {
            "logo_src": PDF_LOGO_PATHS[language],
            "html_data": html_data,
        },
    )

    stylesheet = weasyprint.CSS("raportointi/css/report.css")
    pdf_file = weasyprint.HTML(string=html_string, base_url=".") \
        .write_pdf(stylesheets=[stylesheet], presentational_hints=True)

    return pdf_file


def create_html_report_data(data, lang="fi"):
    """Get the correct language specific data for the HTML report."""
    reporting_base = data["reporting_base"]
    reporting_template = reporting_base["reporting_template"]
    questions = []
    for question in reporting_base["questions"]:
        svg_base64 = None
        if question["vastaustyyppi"] == MATRIX_ROOT_TYPE:  # Matrix question plot
            svg_base64 = create_matrix_plot(question, lang)

        question_helptext = ""
        for helptext in reporting_template["template_helptexts"]:
            if helptext["question_id"] == question["kysymysid"]:
                question_helptext = helptext[f"description_{lang}"] if helptext[f"description_{lang}"] else ""

        questions.append({
            "title": question[f"kysymys_{lang}"],
            "description": question["metatiedot"]["description"][lang],
            "helptext": question_helptext,
            "svg_base64": svg_base64,
            "matrix_root": question["vastaustyyppi"] == MATRIX_ROOT_TYPE
        })

    koulutustoimija_name = {
        "fi": data["koulutustoimija_nimi_fi"],
        "sv": data["koulutustoimija_nimi_sv"]
    }

    main_helptext = {
        "fi": reporting_template["description_fi"],
        "sv": reporting_template["description_sv"]
    }

    main_indicator_str, secondary_indicators_str = get_indicators_strs(data["metatiedot"], lang)

    report_data = {
        "language": lang,
        "title": reporting_base[f"nimi_{lang}"],
        "main_helptext": main_helptext[lang],
        "koulutustoimija": koulutustoimija_name[lang],
        "main_indicator_title": MAIN_INDICATOR_TITLE[lang],
        "main_indicator": main_indicator_str,
        "secondary_indicators_title": SECONDARY_INDICATORS_TITLE[lang],
        "secondary_indicators": secondary_indicators_str,
        "data_collection_title": DATA_COLLECTION_TITLE[lang],
        "created_date": data["created_date"],
        "report_percentage_title": REPORT_PERCENTAGE_TITLE[lang],
        "report_percentage_text": get_report_percentage_text(data),
        "link": REPORT_LINK[lang],
        "link_text": REPORT_LINK_TEXT[lang],
        "questions": questions
    }

    return report_data


def create_matrix_plot(question: dict, lang="fi") -> str:
    """Create a bar chart for a matrix question, using the question data and
    percentage answers."""
    if question["question_answers"]:
        matrix_question_titles = []
        for matrix_question in question["matriisikysymykset"]:
            matrix_question_title = dict(
                fi=matrix_question["kysymys_fi"],
                sv=matrix_question["kysymys_sv"]
            )
            matrix_question_titles.append(matrix_question_title[lang])

        scales = dict(
            fi=[scale["fi"] for scale in question["matrix_question_scale"]],
            sv=[scale["sv"] for scale in question["matrix_question_scale"]]
        )

        scale_length = len(question["question_answers"]["answers_int"][0])
        question["scale_length"] = scale_length
        question["colors"] = MATRIX_GRAPH_COLORS[scale_length]
        question["scales"] = insert_line_breaks(scales[lang], 13, 3)
        question["titles"] = insert_line_breaks(matrix_question_titles, 35, 5)

        # append answer counts to question titles (with newline)
        for i, question_title in enumerate(question["titles"]):
            question_answer_count = question["question_answers"]["answers_sum"][i]
            if question_answer_count >= REPORT_MIN_ANSWERS:
                question["titles"][i] = question_title + f"<br>(n = {question_answer_count})"
            else:
                question["titles"][i] = question_title + f"<br>(n < {REPORT_MIN_ANSWERS})"

        return plotly_matrix_bar_chart(question, lang)


def plotly_matrix_bar_chart(question_data: dict, lang="fi") -> str:
    """Create a bar chart for a matrix question, using the question data and the answer data."""
    x_data = question_data["question_answers"]["answers_pct"]
    answers_available = question_data["question_answers"]["answers_available"]
    answers_average = question_data["question_answers"]["answers_average"]
    colors = question_data["colors"]
    y_data = question_data["titles"]
    legend_labels = question_data["scales"]
    scale_length = question_data["scale_length"]

    # Reverse in order to have matrix 1 on top instead of bottom.
    x_data.reverse()
    y_data.reverse()
    answers_available.reverse()
    answers_average.reverse()

    fig = go.Figure()

    add_bars_to_matrix_plot(fig, x_data, y_data, colors, legend_labels, answers_available)

    add_plot_configurations(fig, PLOT_TRANSLATIONS[lang]["percentage_title"], y_data, scale_length)

    add_plot_annotations(
        fig,
        PLOT_TRANSLATIONS[lang]["answers_not_available_text"],
        answers_available,
        x_data,
        y_data,
        answers_average,
        PLOT_TRANSLATIONS[lang]["average_title"])

    # Set line for 0 %
    fig.update_xaxes(zeroline=True, zerolinewidth=1, zerolinecolor=DEFAULT_BLACK_COLOR)

    # Fails on M1 Mac Using docker without --single-process flag
    # https://github.com/plotly/Kaleido/issues/116
    if DEBUG:
        pio.kaleido.scope.chromium_args += ("--single-process",)

    return base64.b64encode(fig.to_image(format="svg")).decode()


def get_matrix_question_answers(instance, koulutustoimija, filters):
    kyselykerta_query = Q(
        kyselyid__koulutustoimija=koulutustoimija,
        kyselyid__metatiedot__valssi_kysymysryhma=instance.kysymysryhmaid.kysymysryhmaid
    )
    # Use filters if parameters are given
    if filters and filters.get("kyselykerta_alkupvm"):
        kyselykerta_query &= Q(voimassa_alkupvm=filters["kyselykerta_alkupvm"])

    kyselykerta_ids = Kyselykerta.objects.filter(kyselykerta_query).values_list("kyselykertaid", flat=True)

    matrix_questions = Kysymys.objects.filter(
        matriisi_kysymysid=instance.kysymysid,
        matriisi_jarjestys__gt=0
    ).order_by("matriisi_jarjestys")

    matrix_question_answers = []
    for question in matrix_questions:
        vastaus_query = Q(kysymysid=question.kysymysid, vastaajaid__kyselykertaid__in=list(kyselykerta_ids))
        # Use filters if parameters are given
        if filters and filters.get("answer_filters"):
            vastaus_query &= Q(vastaajaid__tehtavanimikkeet__contains=[filters["answer_filters"]])
        answers = Vastaus.objects.filter(vastaus_query).values(
            "numerovalinta"
        ).annotate(
            count=Count("numerovalinta")
        ).order_by(
            "numerovalinta"
        ).values_list(
            "numerovalinta", "count"
        )

        matrix_question_answers.append(list(answers))

    scale = Scale.objects.get(name=matrix_questions.first().vastaustyyppi)
    question_answers_int = transform_tuples_lists_to_integers(scale.step_count, matrix_question_answers)
    question_answers_int = convert_int_lists_to_zero_lists_if_total_lt_limit(question_answers_int, REPORT_MIN_ANSWERS)
    question_answers_pct = convert_lists_to_percent(question_answers_int)
    question_answers_sum = convert_lists_to_sum(question_answers_int)
    question_answers_available = convert_lists_to_bool_with_limit(question_answers_int, REPORT_MIN_ANSWERS)
    question_answers_average = convert_lists_to_average(question_answers_int)
    question_answers = {
        "answers_int": question_answers_int,
        "answers_pct": question_answers_pct,
        "answers_sum": question_answers_sum,
        "answers_available": question_answers_available,
        "answers_average": question_answers_average,
    }

    return question_answers


def add_bars_to_matrix_plot(fig, x_data, y_data, colors, legend_labels, answers_available):
    """Adds matrix bars to the plot.
    NOTE! If the name of two matrix question titles are the same, the bars will be stacked on top of each other.
    """
    rows_added = []
    legends_added = []
    for i in range(0, len(x_data[0])):
        for j, (xd, yd, available) in enumerate(zip(x_data, y_data, answers_available)):
            showlegend = False
            x_widths = calculate_plot_bar_widths(xd)
            if not available:  # Make bar with answers < REPORT_MIN_ANSWERS white
                if j not in rows_added:
                    fig.add_trace(go.Bar(
                        x=[100], y=[yd],
                        orientation="h",
                        marker=dict(
                            color=DEFAULT_WHITE_COLOR,
                            line=dict(color=DEFAULT_WHITE_COLOR, width=1)
                        ),
                        marker_line=dict(width=1, color=DEFAULT_BLACK_COLOR),
                        name=legend_labels[i],
                        showlegend=showlegend,
                    ))
                    rows_added.append(j)
                else:
                    continue
            else:
                if legend_labels[i] not in legends_added:
                    legends_added.append(legend_labels[i])
                    showlegend = True
                fig.add_trace(go.Bar(
                    x=[x_widths[i]], y=[yd],
                    orientation="h",
                    marker=dict(
                        color=colors[i],
                        line=dict(color=DEFAULT_WHITE_COLOR, width=1)
                    ),
                    marker_line=dict(width=1, color=DEFAULT_BLACK_COLOR),
                    name=legend_labels[i],
                    showlegend=showlegend,
                ))


def add_plot_configurations(fig, percentage_title, y_data, scale_length):
    """Add plot configurations to the plot."""
    graphs_count = len(y_data)
    br_count = max(title.count("<br>") for title in y_data)
    height = (100 * graphs_count) + (br_count * 50)

    legend_x = MATRIX_LEGEND_X_POSITIONS[scale_length]
    legend_y = -0.35  # default
    for y_pos in MATRIX_LEGEND_Y_POSITIONS_BY_HEIGHT:
        if height >= y_pos["min_height"]:
            legend_y = y_pos["y"]
            break

    fig.update_layout(
        xaxis=dict(
            gridcolor=DEFAULT_BLACK_COLOR,
            showgrid=True,
            showline=True,
            showticklabels=True,
            zeroline=True,
            domain=[0.15, 1],
            title=percentage_title,
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=True,
        ),
        height=height,
        barmode="stack",
        paper_bgcolor=DEFAULT_WHITE_COLOR,
        plot_bgcolor=DEFAULT_WHITE_COLOR,
        margin=dict(l=150, r=20, t=50, b=0),
        bargap=0.6 + br_count * 0.02,
        legend_traceorder="normal",
        legend=dict(
            orientation="h",
            y=legend_y,
            x=legend_x,
        ),
    )


def add_plot_annotations(
        fig,
        answers_not_available_text,
        answers_available,
        x_data,
        y_data,
        answers_average,
        average_title):
    """Add annotations to the plot."""
    annotations = []

    for yd, xd, available, average in zip(y_data, x_data, answers_available, answers_average):
        x_bar_widths = calculate_plot_bar_widths(xd)

        # labeling the y-axis
        annotations.append(dict(xref="paper", yref="y",
                                x=-0.25, y=yd,
                                xanchor="left",
                                text=str(yd),
                                font=dict(family=DEFAULT_FONT, size=PLOTLY_FONT_SIZE,
                                          color=DEFAULT_BLACK_COLOR),
                                showarrow=False, align="left"))

        if available:
            # Adding average values of each bar
            annotations.append(dict(xref="paper", yref="y",
                                    x=1.020, y=yd,
                                    xanchor="right",
                                    text=average,
                                    font=dict(family=DEFAULT_FONT, size=PLOTLY_FONT_SIZE,
                                              color=DEFAULT_BLACK_COLOR),
                                    showarrow=False, align="right"))

            # Labeling values of each bar (x_axis)
            for i in range(len(xd)):
                text = str(xd[i]) if xd[i] > 0 else ""  # dont show zeros
                annotations.append(dict(xref="x", yref="y",
                                        x=sum(x_bar_widths[:i]) + (x_bar_widths[i] / 2), y=yd,
                                        text=text,
                                        font=dict(family=DEFAULT_FONT, size=PLOTLY_FONT_SIZE,
                                                  color=DEFAULT_BLACK_COLOR),
                                        showarrow=False))

        else:
            # Labeling answers not available for white bar
            annotations.append(dict(xref="x", yref="y",
                                    x=50, y=yd,
                                    text=answers_not_available_text,
                                    font=dict(family=DEFAULT_FONT, size=PLOTLY_FONT_SIZE,
                                              color=DEFAULT_BLACK_COLOR),
                                    showarrow=False))

    # Adding average values of all bars

    # Add average title
    annotations.append(dict(xref="paper", yref="y",
                            x=1.020, y=y_data[-1],
                            yshift=30,
                            xanchor="right",
                            text=average_title,
                            font=dict(family=DEFAULT_FONT, size=PLOTLY_FONT_SIZE,
                                      color=DEFAULT_BLACK_COLOR),
                            showarrow=False, align="right"))

    # Add annotations to the plot
    fig.update_layout(annotations=annotations)


def survey_participant_count(kysymysryhma: Kysymysryhma, kyselykertas: QuerySet[Kyselykerta],
                             koulutustoimija: Organisaatio, vastaajas: QuerySet[Vastaaja], filters: dict) -> int:
    kyselykertas_filtered = [
        kyselykerta for kyselykerta in kyselykertas
        if kyselykerta.kyselyid.koulutustoimija == koulutustoimija and
        kyselykerta.kyselyid.metatiedot.get("valssi_kysymysryhma") == kysymysryhma.kysymysryhmaid]

    if filters and filters.get("kyselykerta_alkupvm"):
        alkupvm = filters.get("kyselykerta_alkupvm")
        if isinstance(alkupvm, str):
            alkupvm = datetime.strptime(alkupvm, DATE_INPUT_FORMAT).date()
        kyselykertas_filtered = [kyselykerta for kyselykerta in kyselykertas_filtered
                                 if kyselykerta.voimassa_alkupvm == alkupvm]

    kyselykertaids = {kyselykerta.pk for kyselykerta in kyselykertas_filtered}
    participant_count = len([1 for vastaaja in vastaajas if vastaaja.kyselykertaid in kyselykertaids])

    return participant_count


def survey_sent_count(kysymysryhma: Kysymysryhma, kyselykertas: QuerySet[Kyselykerta],
                      koulutustoimija: Organisaatio, filters: dict) -> int:
    kyselykertas_filtered = [
        kyselykerta for kyselykerta in kyselykertas
        if kyselykerta.kyselyid.koulutustoimija == koulutustoimija and
        kyselykerta.kyselyid.metatiedot.get("valssi_kysymysryhma") == kysymysryhma.kysymysryhmaid]

    if filters and filters.get("kyselykerta_alkupvm"):
        alkupvm = filters.get("kyselykerta_alkupvm")
        if isinstance(alkupvm, str):
            alkupvm = datetime.strptime(alkupvm, DATE_INPUT_FORMAT).date()
        kyselykertas_filtered = [kyselykerta for kyselykerta in kyselykertas_filtered
                                 if kyselykerta.voimassa_alkupvm == alkupvm]

    kyselykertaids = {kyselykerta.pk for kyselykerta in kyselykertas_filtered}

    return Vastaajatunnus.objects.filter(kyselykertaid__pk__in=kyselykertaids).count()


def get_available_codes(kysymysryhma: Kysymysryhma,
                        kyselykertas: QuerySet[Kyselykerta], koulutustoimija: Organisaatio,
                        vastaajas: QuerySet[Vastaaja], filters: dict):
    kyselykertas_filtered = [
        kyselykerta for kyselykerta in kyselykertas
        if kyselykerta.kyselyid.koulutustoimija == koulutustoimija and
        kyselykerta.kyselyid.metatiedot.get("valssi_kysymysryhma") == kysymysryhma.kysymysryhmaid]

    if filters and filters.get("kyselykerta_alkupvm"):
        alkupvm = filters.get("kyselykerta_alkupvm")
        if isinstance(alkupvm, str):
            alkupvm = datetime.strptime(alkupvm, DATE_INPUT_FORMAT).date()
        kyselykertas_filtered = [kyselykerta for kyselykerta in kyselykertas_filtered
                                 if kyselykerta.voimassa_alkupvm == alkupvm]

    kyselykertaids = {kyselykerta.pk for kyselykerta in kyselykertas_filtered}

    vastaajas_tehtnim = [vastaaja.tehtavanimikkeet for vastaaja in vastaajas
                         if vastaaja.kyselykertaid in kyselykertaids]

    return list({tehtnim["tehtavanimike_koodi"]
                 for vastaaja_tehtnim in vastaajas_tehtnim
                 for tehtnim in vastaaja_tehtnim
                 if isinstance(tehtnim, dict) and "tehtavanimike_koodi" in tehtnim})


def get_job_title_names_from_codes(koodis, respondent_codes, lang="fi"):
    if lang == "fi":
        return [{"name": koodi.nimi_fi, "job_title_code": koodi.koodi_arvo}
                for koodi in koodis if koodi.koodi_arvo in respondent_codes]
    return [{"name": koodi.nimi_sv, "job_title_code": koodi.koodi_arvo}
            for koodi in koodis if koodi.koodi_arvo in respondent_codes]


def create_available_kyselykertas(kysymysryhma, kyselykertas_start_times, koulutustoimija, kyselykertas, vastaajas):
    date_count = defaultdict(int)
    for date in kyselykertas_start_times:
        year_month = date.strftime("%-m/%Y")
        date_count[year_month] += 1

    date_month_count = {year_month: 1 for year_month in date_count}

    summary_objs = Summary.objects.filter(
        kysymysryhmaid=kysymysryhma.kysymysryhmaid,
        koulutustoimija=koulutustoimija.oid,
        is_locked=True)

    result_objs = Result.objects.filter(
        kysymysryhmaid=kysymysryhma.kysymysryhmaid,
        koulutustoimija=koulutustoimija.oid,
        is_locked=True)

    available_kyselykertas = []
    for date in kyselykertas_start_times:
        # Check if Kyselykerta has enough answers
        display_report = survey_participant_count(
            kysymysryhma, kyselykertas, koulutustoimija, vastaajas,
            dict(kyselykerta_alkupvm=date)) >= REPORT_MIN_ANSWERS

        # Check if Summary exists for the given date
        summary_exists = any([summary_obj.kysely_voimassa_alkupvm == date for summary_obj in summary_objs])

        # Check if Result exists for the given date
        result_exists = any([result_obj.kysely_voimassa_alkupvm == date for result_obj in result_objs])

        year_month = date.strftime("%-m/%Y")
        title_number = date_month_count.setdefault(year_month, 1)
        date_month_count[year_month] += 1
        is_available = date_count[year_month] == 1
        suffix = "" if is_available else f"_{title_number}"
        nimi_fi = f"{kysymysryhma.nimi_fi} {year_month}{suffix}" \
            if kysymysryhma.nimi_fi else f"{kysymysryhma.nimi_sv} {year_month}{suffix}"
        nimi_sv = f"{kysymysryhma.nimi_sv} {year_month}{suffix}" \
            if kysymysryhma.nimi_sv else f"{kysymysryhma.nimi_fi} {year_month}{suffix}"

        available_kyselykertas.append({
            "nimi_fi": nimi_fi,
            "nimi_sv": nimi_sv,
            "kyselykerta_alkupvm": date.strftime("%Y-%m-%d"),
            "display_report": display_report,
            "show_summary": summary_exists,
            "show_result": result_exists
        })

    return available_kyselykertas


def calculate_plot_bar_widths(data: List[int]) -> List[int]:
    if sum(data) < 90:
        return data

    widths = data.copy()
    more_than_limit_sum_fixed = 100  # full width
    more_than_limit_sum = 0
    for i, width in enumerate(widths):
        if 1 <= width <= REPORT_PLOT_MIN_WIDTH:
            widths[i] = REPORT_PLOT_MIN_WIDTH
            more_than_limit_sum_fixed -= REPORT_PLOT_MIN_WIDTH
        else:
            more_than_limit_sum += width

    # scale those parts which are > REPORT_PLOT_MIN_WIDTH
    if more_than_limit_sum_fixed != more_than_limit_sum:
        for i, width in enumerate(widths):
            if width > REPORT_PLOT_MIN_WIDTH:
                widths[i] = round(width * more_than_limit_sum_fixed / more_than_limit_sum, 2)

    return widths


def get_report_percentage_text(data: dict) -> str:
    survey_participants_count = data["survey_participants_count"]
    survey_sent_count = data["survey_sent_count"]
    percentage = calculate_pct(survey_participants_count, survey_sent_count)
    return f"{survey_participants_count}/{survey_sent_count} ({percentage} %)"


def get_indicators_strs(metatiedot: dict, language: str) -> (str, str):
    main_indicator_key = metatiedot["paaIndikaattori"].get("key", None)
    main_indicator_str = get_localisation_values_by_key(main_indicator_key)[language]

    secondary_indicator_keys = [ind.get("key") for ind in metatiedot.get("sekondaariset_indikaattorit")]
    secondary_indicator_strs = [get_localisation_values_by_key(key)[language] for key in secondary_indicator_keys]

    return main_indicator_str, ", ".join(secondary_indicator_strs)
