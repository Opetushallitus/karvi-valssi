import base64
import logging
import plotly.graph_objects as go
import plotly.io as pio
import weasyprint

from collections import defaultdict
from datetime import datetime
from typing import List, Set

from django.db.models import Count, Q, QuerySet
from django.template.loader import render_to_string

from raportointi.constants import (
    MATRIX_GRAPH_COLORS, MATRIX_ROOT_TYPE, DEFAULT_BLACK_COLOR, DEFAULT_WHITE_COLOR, REPORT_MIN_ANSWERS,
    DEFAULT_BLACK_FONT, PLOT_TRANSLATIONS, PDF_LOGO_PATHS,
    REPORT_PLOT_MIN_WIDTH, MATRIX_LEGEND_X_POSITIONS, MATRIX_LEGEND_Y_POSITIONS_BY_HEIGHT, DATE_INPUT_FORMAT,
    REPORT_TRANSLATIONS, PDF_INDICATOR_INFO_TRANSLATIONS, REPORT_MATRIX_MAX_SVG_QUESTIONS,
    REPORT_FILTER_LANGUAGE_CODES, MONIVALINTA_QUESTION_TYPE, MONIVALINTA_GRAPH_COLOR,
    REPORT_MONIVALINTA_MAX_SVG_QUESTIONS, ASIANTUNTIJA_LOMAKE_TYPES, PDF_TRANSLATION_MISSING_TEXT, TEXT_QUESTION_TYPE,
    PDF_ANSWERS_HIDDEN_TEXT,
)
from raportointi.models import (
    Kysymys, Vastaus, Scale, Kyselykerta, Vastaaja, Summary, Result, Vastaajatunnus, Kysymysryhma, Organisaatio,
    AluejakoAlue, Koodi,
)
from raportointi.utils import (
    insert_line_breaks, transform_tuples_lists_to_integers, convert_lists_to_percent, convert_lists_to_sum,
    convert_lists_to_bool_with_limit, convert_lists_to_average, convert_int_lists_to_zero_lists_if_total_lt_limit,
    get_localisation_values_by_key, convert_list_to_percent,
)
from raportointi.utils_datacollection import calculate_pct
from raportointi.utils_summary import pdf_indicator_texts
from raportointipalvelu.settings import DEBUG


logger = logging.getLogger(__name__)


def create_report_pdf(data, filters, language, lomake_language):
    """Generate a PDF report by rendering an HTML template with given data and
    converting it to PDF format."""

    html_data = create_html_report_data(data, language, lomake_language)

    show_filters = data["metatiedot"].get("lomaketyyppi") not in ASIANTUNTIJA_LOMAKE_TYPES
    html_string = render_to_string(
        "report_pdf_base.html", {
            "logo_src": PDF_LOGO_PATHS[language],
            "html_data": html_data,
            "show_filters": show_filters,
            "filter_texts": get_report_pdf_filter_texts(filters, language) if show_filters else None,
        },
    )

    stylesheet = weasyprint.CSS("raportointi/css/report.css")
    pdf_file = weasyprint.HTML(string=html_string, base_url=".") \
        .write_pdf(stylesheets=[stylesheet], presentational_hints=True)

    return pdf_file


def create_html_report_data(data, language, lomake_language):
    """Get the correct language specific data for the HTML report."""

    reporting_base = data["reporting_base"]
    reporting_template = reporting_base["reporting_template"]

    questions_data = get_questions_data(reporting_base, reporting_template, language, lomake_language)

    main_indicator_key = data["metatiedot"]["paaIndikaattori"].get("key", None)
    secondary_indicator_keys = [ind.get("key") for ind in data["metatiedot"].get("sekondaariset_indikaattorit")]
    indicator_keys = [main_indicator_key] + secondary_indicator_keys
    indicator_texts = pdf_indicator_texts(indicator_keys, language)

    report_data = {
        "language": language,
        "title": reporting_base[f"nimi_{lomake_language}"],
        "main_helptext": reporting_template[f"description_{language}"],
        "koulutustoimija": data[f"koulutustoimija_nimi_{language}"],
        "indicator_title": PDF_INDICATOR_INFO_TRANSLATIONS[language],
        "indicator_texts": indicator_texts,
        "data_collection_title": REPORT_TRANSLATIONS["data_collection_title"][language],
        "created_date": data["created_date"],
        "report_oppilaitos_answered_title": REPORT_TRANSLATIONS["report_oppilaitos_answered_title"][language],
        "report_oppilaitos_answered_text": get_report_oppilaitos_answered_text(data),
        "report_percentage_title": REPORT_TRANSLATIONS["report_percentage_title"][language],
        "report_percentage_text": get_report_percentage_text(data),
        "link": REPORT_TRANSLATIONS["report_link"][language],
        "link_text": REPORT_TRANSLATIONS["report_link_text"][language],
        "questions": questions_data,
    }

    return report_data


def get_questions_data(reporting_base, reporting_template, language, lomake_language):
    questions = []
    for question in reporting_base["questions"]:
        svg_base64s = None
        answerer_counts = None
        text_answer = None

        is_hidden = question["metatiedot"].get("hidden", False)
        is_hidden_on_report = question["metatiedot"].get("is_hidden_on_report", False)
        is_text_question_type = question["vastaustyyppi"] == TEXT_QUESTION_TYPE
        question_meta_type = question["metatiedot"].get("type", "")

        if question["jatkokysymys"]:
            # Hide jatkokysymyses (automatically generated monivalinta "Muu mikä")
            continue
        elif is_hidden:
            # Hide hidden questions
            continue
        elif question_meta_type == "statictext":  # Väliotsikko
            pass
        elif is_hidden_on_report or is_text_question_type:
            text_answer = PDF_ANSWERS_HIDDEN_TEXT[language]
        elif question["vastaustyyppi"] == MATRIX_ROOT_TYPE:  # Matrix question plot
            svg_base64s = create_matrix_plots(question, language, lomake_language)
        elif question["vastaustyyppi"] == MONIVALINTA_QUESTION_TYPE:  # Monivalinta question
            svg_base64s = create_monivalinta_plots(question, language)

            question_answers = question["question_answers"]
            if question_answers["answers_available"]:
                answerer_counts = (f"{REPORT_TRANSLATIONS['report_percentage_title'][language]} "
                                   f"{question_answers['answers_count']}")
            if question_answers["answers_available"] and question_meta_type == "checkbox":
                answerer_counts += (f", {REPORT_TRANSLATIONS['report_answer_count_text'][language]} "
                                    f"{question_answers['answers_sum']}")

        description = question["metatiedot"]["description"][language] if "description" in question["metatiedot"] else ""

        question_helptext = get_question_helptext(reporting_template, question, language)

        questions.append({
            "title": question[f"kysymys_{lomake_language}"],
            "description": description,
            "helptext": question_helptext,
            "svg_base64s": svg_base64s,
            "answerer_counts": answerer_counts,
            "matrix_root": question["vastaustyyppi"] == MATRIX_ROOT_TYPE,
            "text_answer": text_answer,
        })

    return questions


def get_question_helptext(reporting_template, question, language):
    question_helptext = ""
    for helptext in reporting_template["template_helptexts"]:
        if helptext["question_id"] == question["kysymysid"]:
            question_helptext = helptext[f"description_{language}"] if helptext[f"description_{language}"] else ""

    return question_helptext


def create_matrix_plots(question: dict, language, lomake_language) -> List[str]:
    """Create a bar chart for a matrix question, using the question data and
    percentage answers."""

    if not question["question_answers"]:
        return None

    matrix_question_titles = []
    for matrix_question in question["matriisikysymykset"]:
        # skip hidden subquestions
        if matrix_question["metatiedot"].get("hidden", None):
            continue

        question_text = matrix_question.get(f"kysymys_{lomake_language}")
        if question_text is None:
            question_text = PDF_TRANSLATION_MISSING_TEXT

        matrix_question_titles.append(question_text)

    scales = [scale[lomake_language] for scale in question["matrix_question_scale"]]

    scale_length = len(question["matrix_question_scale"])
    question["scale_length"] = scale_length
    question["colors"] = MATRIX_GRAPH_COLORS[scale_length]
    question["scales"] = insert_line_breaks(scales, 13, 3)
    question["titles"] = insert_line_breaks(matrix_question_titles, 35, 5)

    # append answer counts to question titles (with newline)
    for i, question_title in enumerate(question["titles"]):
        question_answer_count = question["question_answers"]["answers_sum"][i]
        question["titles"][i] = question_title
        if question_answer_count >= REPORT_MIN_ANSWERS:
            question["titles"][i] += f"<br>(n = {question_answer_count})"

    # split bar charts
    splitted_charts = []
    max_svg_questions = REPORT_MATRIX_MAX_SVG_QUESTIONS
    split_count = (len(question["titles"]) + max_svg_questions - 1) // max_svg_questions
    for i in range(split_count):
        index0 = i * max_svg_questions
        index1 = (i + 1) * max_svg_questions
        splitted_chart = plotly_matrix_bar_chart(question, language, indices=(index0, index1))
        splitted_charts.append(splitted_chart)

    return splitted_charts


def plotly_matrix_bar_chart(question_data: dict, lang: str, indices: tuple) -> str:
    """Create a bar chart for a matrix question, using the question data and the answer data."""
    i0, i1 = indices
    x_data = question_data["question_answers"]["answers_pct"][i0:i1]
    answers_available = question_data["question_answers"]["answers_available"][i0:i1]
    answers_average = question_data["question_answers"]["answers_average"][i0:i1]
    colors = question_data["colors"]
    y_data = question_data["titles"][i0:i1]
    legend_labels = question_data["scales"]
    scale_length = question_data["scale_length"]

    # Reverse in order to have matrix 1 on top instead of bottom.
    x_data.reverse()
    y_data.reverse()
    answers_available.reverse()
    answers_average.reverse()

    fig = go.Figure()

    add_bars_to_matrix_plot(fig, x_data, y_data, colors, legend_labels, answers_available)

    add_matrix_plot_configurations(fig, PLOT_TRANSLATIONS["percentage_title"][lang], y_data, scale_length)

    add_matrix_plot_annotations(
        fig, PLOT_TRANSLATIONS["answers_not_available_text"][lang],
        answers_available, x_data, y_data, answers_average,
        PLOT_TRANSLATIONS["average_title"][lang])

    # Set line for 0 %
    fig.update_xaxes(zeroline=True, zerolinewidth=1, zerolinecolor=DEFAULT_BLACK_COLOR)

    # Fails on M1 Mac Using docker without --single-process flag
    # https://github.com/plotly/Kaleido/issues/116
    if DEBUG:
        pio.kaleido.scope.chromium_args += ("--single-process",)

    return base64.b64encode(fig.to_image(format="svg")).decode()


def create_monivalinta_plots(question: dict, language) -> List[str]:
    """Create a bar chart for a monivalinta question, using the question data and
    percentage answers."""

    if not question["question_answers"]:
        return None

    question_titles = []
    for vastausvaihtoehto in question["metatiedot"]["vastausvaihtoehdot"]:
        question_titles.append(vastausvaihtoehto["title"][language])

    question["titles"] = insert_line_breaks(question_titles, 35, 5)

    # append answer counts to question titles (with newline)
    for i, question_title in enumerate(question["titles"]):
        question_answer_count = question["question_answers"]["answers_int"][i]
        question["titles"][i] = question_title
        if question["question_answers"]["answers_available"]:
            question["titles"][i] += f"<br>(n = {question_answer_count})"

    # split bar charts
    splitted_charts = []
    max_svg_questions = REPORT_MONIVALINTA_MAX_SVG_QUESTIONS
    split_count = (len(question["titles"]) + max_svg_questions - 1) // max_svg_questions
    for i in range(split_count):
        index0 = i * max_svg_questions
        index1 = (i + 1) * max_svg_questions
        splitted_chart = plotly_monivalinta_bar_chart(question, language, indices=(index0, index1))
        splitted_charts.append(splitted_chart)

    return splitted_charts


def plotly_monivalinta_bar_chart(question_data: dict, lang: str, indices: tuple) -> str:
    """Create a bar chart for a monivalinta question, using the question data and the answer data."""
    i0, i1 = indices
    x_data = question_data["question_answers"]["answers_pct"][i0:i1]
    y_data = question_data["titles"][i0:i1]
    answers_available = question_data["question_answers"]["answers_available"]

    # Reverse in order to have matrix 1 on top instead of bottom.
    x_data.reverse()
    y_data.reverse()

    fig = go.Figure()

    add_bars_to_monivalinta_plot(fig, x_data, y_data, answers_available)

    add_monivalinta_plot_configurations(fig, PLOT_TRANSLATIONS["percentage_title"][lang], y_data)

    add_monivalinta_plot_annotations(
        fig, PLOT_TRANSLATIONS["answers_not_available_text"][lang],
        answers_available, x_data, y_data)

    # Ensures x-axis always spans from 0 to 100
    fig.update_layout(xaxis=dict(range=[0, 100]))

    # Set lines for 0 % and 100 %
    fig.update_xaxes(zeroline=True, zerolinewidth=1, zerolinecolor=DEFAULT_BLACK_COLOR)
    add_plot_100_line(fig)

    return base64.b64encode(fig.to_image(format="svg")).decode()


def get_matrix_question_answers(kysymys, koulutustoimija, filters):
    kyselykerta_ids = get_filtered_kyselykerta_ids(kysymys, koulutustoimija, filters)

    matrix_questions = Kysymys.objects.filter(
        matriisi_kysymysid=kysymys.kysymysid,
        matriisi_jarjestys__gt=0
    ).order_by("matriisi_jarjestys")

    matrix_question_answers = []
    for matrix_question in matrix_questions:
        # skip hidden subquestions
        if matrix_question.metatiedot.get("hidden", None):
            continue

        answer_counts = get_filtered_answer_counts(matrix_question, kyselykerta_ids, filters)
        matrix_question_answers.append(list(answer_counts))

    scale = Scale.objects.get(name=matrix_questions.first().vastaustyyppi)
    question_answers_int = transform_tuples_lists_to_integers(scale.step_count, matrix_question_answers)
    question_answers_int = convert_int_lists_to_zero_lists_if_total_lt_limit(question_answers_int, REPORT_MIN_ANSWERS)

    return {
        "answers_int": question_answers_int,
        "answers_pct": convert_lists_to_percent(question_answers_int),
        "answers_sum": convert_lists_to_sum(question_answers_int),
        "answers_available": convert_lists_to_bool_with_limit(question_answers_int, REPORT_MIN_ANSWERS),
        "answers_average": convert_lists_to_average(question_answers_int),
    }


def get_monivalinta_question_answers(kysymys, koulutustoimija, filters):
    # Skip hidden questions
    if kysymys.metatiedot.get("hidden", None):
        return None

    kyselykerta_ids = get_filtered_kyselykerta_ids(kysymys, koulutustoimija, filters)

    vastausvaihtoehdot_count = len(kysymys.metatiedot["vastausvaihtoehdot"])
    vastaus_objs = get_filtered_monivalinta_vastaus_objs(kysymys, kyselykerta_ids, filters)
    answers_count = len({obj.vastaajaid for obj in vastaus_objs})

    if answers_count < REPORT_MIN_ANSWERS:
        return {
            "answers_int": [0] * vastausvaihtoehdot_count,
            "answers_pct": [0] * vastausvaihtoehdot_count,
            "answers_sum": 0,
            "answers_count": 0,
            "answers_available": False,
        }

    filtered_answer_counts = get_filtered_answer_counts(kysymys, kyselykerta_ids, filters)
    question_answers_int = transform_tuples_lists_to_integers(
        vastausvaihtoehdot_count, [list(filtered_answer_counts)])[0]

    return {
        "answers_int": question_answers_int,
        "answers_pct": convert_list_to_percent(question_answers_int, fixed_denominator=answers_count),
        "answers_sum": sum(question_answers_int),
        "answers_count": answers_count,
        "answers_available": True,
    }


def get_filtered_kyselykerta_ids(kysymys, koulutustoimija, filters):
    kyselykerta_query = Q(
        kyselyid__koulutustoimija=koulutustoimija,
        kyselyid__metatiedot__valssi_kysymysryhma=kysymys.kysymysryhmaid.kysymysryhmaid,
    )

    # Use filters if parameters are given
    if filters and filters.get("kyselykerta_alkupvm"):
        kyselykerta_query &= Q(voimassa_alkupvm=filters["kyselykerta_alkupvm"])

    if filters and filters.get("aluejako"):
        kyselykerta_query &= Q(kyselyid__oppilaitos__metatiedot__aluejako=filters["aluejako"])

    kyselykertas = Kyselykerta.objects.filter(kyselykerta_query) \
        .select_related("kyselyid__oppilaitos")

    if filters and filters.get("language_codes"):
        kyselykertas = [
            kyselykerta for kyselykerta in kyselykertas
            if kyselykerta.kyselyid.oppilaitos and
            get_report_language_codes(
                kyselykerta.kyselyid.oppilaitos.metatiedot.get("toimintakieli_koodi", [])
            ) & filters.get("language_codes")]

    return {kyselykerta.pk for kyselykerta in kyselykertas}


def get_filtered_answer_counts(kysymys, kyselykerta_ids, filters):
    vastaus_query = Q(
        kysymysid=kysymys.kysymysid,
        vastaajaid__kyselykertaid__in=list(kyselykerta_ids))

    # Use filters if parameters are given
    if filters and filters.get("answer_filters"):
        vastaus_query &= Q(vastaajaid__tehtavanimikkeet__contains=[filters["answer_filters"]])

    answer_counts = Vastaus.objects.filter(vastaus_query).values(
        "numerovalinta"
    ).annotate(
        count=Count("numerovalinta")
    ).order_by(
        "numerovalinta"
    ).values_list(
        "numerovalinta", "count"
    )

    return answer_counts


def get_filtered_monivalinta_vastaus_objs(kysymys, kyselykerta_ids, filters):
    vastaus_query = Q(
        kysymysid=kysymys.kysymysid,
        vastaajaid__kyselykertaid__in=list(kyselykerta_ids),
        numerovalinta__isnull=False,
    )

    # Use filters if parameters are given
    if filters and filters.get("answer_filters"):
        vastaus_query &= Q(vastaajaid__tehtavanimikkeet__contains=[filters["answer_filters"]])

    return Vastaus.objects.filter(vastaus_query)


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

            if available:
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
            else:  # Make bar with answers < REPORT_MIN_ANSWERS white
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


def add_bars_to_monivalinta_plot(fig, x_data, y_data, answers_available):
    """Adds monivalinta bars to the plot.
    NOTE! If the name of two question titles are the same, the bars will be stacked on top of each other.
    """
    for xd, yd in zip(x_data, y_data):
        x_width = xd

        if answers_available:
            fig.add_trace(go.Bar(
                x=[x_width], y=[yd],
                orientation="h",
                marker=dict(
                    color=MONIVALINTA_GRAPH_COLOR,
                    line=dict(color=DEFAULT_WHITE_COLOR, width=1)
                ),
                marker_line=dict(width=1, color=DEFAULT_BLACK_COLOR),
                showlegend=False,
            ))
        else:  # Make bar with answers < REPORT_MIN_ANSWERS white
            fig.add_trace(go.Bar(
                x=[100], y=[yd],
                orientation="h",
                marker=dict(
                    color=DEFAULT_WHITE_COLOR,
                    line=dict(color=DEFAULT_WHITE_COLOR, width=1)
                ),
                marker_line=dict(width=1, color=DEFAULT_BLACK_COLOR),
                showlegend=False,
            ))


def add_matrix_plot_configurations(fig, percentage_title, y_data, scale_length):
    graphs_count = len(y_data)
    br_count = max(title.count("<br>") for title in y_data)
    height = (100 * graphs_count) + (br_count * 50)

    if scale_length:
        legend_y = -0.35  # default
        for y_pos in MATRIX_LEGEND_Y_POSITIONS_BY_HEIGHT:
            if height >= y_pos["min_height"]:
                legend_y = y_pos["y"]
                break
        legend = dict(
            orientation="h",
            y=legend_y,
            x=MATRIX_LEGEND_X_POSITIONS[scale_length],
        )
    else:
        legend = None

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
        legend=legend,
    )


def add_monivalinta_plot_configurations(fig, percentage_title, y_data):
    graphs_count = len(y_data)
    br_count = sum(title.count("<br>") for title in y_data)
    height = (70 * graphs_count) + (br_count * 14)

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
        margin=dict(l=150, r=20, t=10, b=0),
        bargap=0.6,
    )


def add_matrix_plot_annotations(
        fig,
        answers_not_available_text,
        answers_available,
        x_data,
        y_data,
        answers_average,
        average_title):
    """Add annotations to the matrix plot."""
    annotations = []

    for yd, xd, available, average in zip(y_data, x_data, answers_available, answers_average):
        x_bar_widths = calculate_plot_bar_widths(xd)

        # labeling the y-axis
        annotations.append(dict(xref="paper", yref="y",
                                x=-0.25, y=yd,
                                xanchor="left",
                                text=str(yd),
                                font=DEFAULT_BLACK_FONT,
                                showarrow=False, align="left"))

        if available:
            # Adding average values of each bar
            annotations.append(dict(xref="paper", yref="y",
                                    x=1.020, y=yd,
                                    xanchor="right",
                                    text=average,
                                    font=DEFAULT_BLACK_FONT,
                                    showarrow=False, align="right"))

            # Labeling values of each bar (x_axis)
            for i in range(len(xd)):
                text = str(xd[i]) if xd[i] > 0 else ""  # dont show zeros
                annotations.append(dict(xref="x", yref="y",
                                        x=sum(x_bar_widths[:i]) + (x_bar_widths[i] / 2), y=yd,
                                        text=text,
                                        font=DEFAULT_BLACK_FONT,
                                        showarrow=False))

        else:
            # Labeling answers not available for white bar
            annotations.append(dict(xref="x", yref="y",
                                    x=50, y=yd,
                                    text=answers_not_available_text,
                                    font=DEFAULT_BLACK_FONT,
                                    showarrow=False))

    # Adding average values of all bars

    # Add average title
    annotations.append(dict(xref="paper", yref="y",
                            x=1.020, y=y_data[-1],
                            yshift=30,
                            xanchor="right",
                            text=average_title,
                            font=DEFAULT_BLACK_FONT,
                            showarrow=False, align="right"))

    # Add annotations to the plot
    fig.update_layout(annotations=annotations)


def add_monivalinta_plot_annotations(
        fig,
        answers_not_available_text,
        answers_available,
        x_data,
        y_data):
    """Add annotations to the monivalinta plot."""
    annotations = []

    for yd, xd in zip(y_data, x_data):
        x_bar_width = xd

        # labeling the y-axis
        annotations.append(dict(xref="paper", yref="y",
                                x=-0.25, y=yd,
                                xanchor="left",
                                text=str(yd),
                                font=DEFAULT_BLACK_FONT,
                                showarrow=False, align="left"))

        if answers_available:
            # Labeling value of x-bar
            text = str(xd)
            text_x = x_bar_width / 2 if x_bar_width > 5 else x_bar_width + 2
            annotations.append(dict(xref="x", yref="y",
                                    x=text_x, y=yd,
                                    text=text,
                                    font=DEFAULT_BLACK_FONT,
                                    showarrow=False))
        else:
            # Labeling answers not available for white bar
            annotations.append(dict(xref="x", yref="y",
                                    x=50, y=yd,
                                    text=answers_not_available_text,
                                    font=DEFAULT_BLACK_FONT,
                                    showarrow=False))

    # Add annotations to the plot
    fig.update_layout(annotations=annotations)


def add_plot_100_line(fig):
    fig.add_shape(xref="x", yref="paper",
                  type="line",
                  x0=100, x1=100,
                  y0=0, y1=1,
                  line=dict(width=2, color=DEFAULT_BLACK_COLOR))


def survey_participant_count(kysymysryhma: Kysymysryhma, kyselykertas: QuerySet[Kyselykerta],
                             koulutustoimija: Organisaatio, vastaajas: QuerySet[Vastaaja], filters: dict,
                             return_oppilaitos_count: bool = False) -> int:
    kyselykertas_filtered = [
        kyselykerta for kyselykerta in kyselykertas
        if kyselykerta.kyselyid.koulutustoimija == koulutustoimija and
        kyselykerta.kyselyid.kysymysryhmat.all()[0].kysymysryhmaid == kysymysryhma.kysymysryhmaid]

    kyselykertas_filtered = filter_kyselykertas_by_alkupvm(kyselykertas_filtered, filters)
    kyselykertas_filtered = filter_kyselykertas_by_language_codes(kyselykertas_filtered, filters)
    kyselykertas_filtered = filter_kyselykertas_by_aluejako(kyselykertas_filtered, filters)

    kyselykertaids = {kyselykerta.pk for kyselykerta in kyselykertas_filtered}

    if return_oppilaitos_count:
        kyselykerta_oppilaitos_dict = {
            vastaajatunnus.kyselykertaid.pk: vastaajatunnus.kyselykertaid.kyselyid.oppilaitos_id
            for vastaajatunnus in Vastaajatunnus.objects.filter(kyselykertaid__pk__in=kyselykertaids)
            .select_related("kyselykertaid__kyselyid")
            if vastaajatunnus.kyselykertaid.kyselyid.oppilaitos}
        answered_oppilaitos_ids = {
            kyselykerta_oppilaitos_dict[vastaaja.kyselykertaid]
            for vastaaja in vastaajas
            if kyselykerta_oppilaitos_dict.get(vastaaja.kyselykertaid)}
        return len(answered_oppilaitos_ids)

    # participant count
    return len([1 for vastaaja in vastaajas if vastaaja.kyselykertaid in kyselykertaids])


def survey_sent_count(kysymysryhma: Kysymysryhma, kyselykertas: QuerySet[Kyselykerta],
                      koulutustoimija: Organisaatio, filters: dict,
                      return_oppilaitos_count: bool = False) -> int:
    kyselykertas_filtered = [
        kyselykerta for kyselykerta in kyselykertas
        if kyselykerta.kyselyid.koulutustoimija == koulutustoimija and
        kyselykerta.kyselyid.metatiedot.get("valssi_kysymysryhma") == kysymysryhma.kysymysryhmaid]

    kyselykertas_filtered = filter_kyselykertas_by_alkupvm(kyselykertas_filtered, filters)
    kyselykertas_filtered = filter_kyselykertas_by_language_codes(kyselykertas_filtered, filters)
    kyselykertas_filtered = filter_kyselykertas_by_aluejako(kyselykertas_filtered, filters)

    kyselykertaids = {kyselykerta.pk for kyselykerta in kyselykertas_filtered}

    if return_oppilaitos_count:
        oppilaitos_ids = {
            vastaajatunnus.kyselykertaid.kyselyid.oppilaitos_id
            for vastaajatunnus in Vastaajatunnus.objects.filter(kyselykertaid__pk__in=kyselykertaids)
            .select_related("kyselykertaid__kyselyid")
            if vastaajatunnus.kyselykertaid.kyselyid.oppilaitos}
        return len(oppilaitos_ids)
    return Vastaajatunnus.objects.filter(kyselykertaid__pk__in=kyselykertaids).count()


def survey_oppilaitoses_activated_count(
        kysymysryhma: Kysymysryhma, kyselykertas: QuerySet[Kyselykerta],
        koulutustoimija: Organisaatio, filters: dict) -> int:
    kyselykertas_filtered = [
        kyselykerta for kyselykerta in kyselykertas
        if kyselykerta.kyselyid.koulutustoimija == koulutustoimija and
        kyselykerta.kyselyid.kysymysryhmat.all()[0].kysymysryhmaid == kysymysryhma.kysymysryhmaid]

    kyselykertas_filtered = filter_kyselykertas_by_alkupvm(kyselykertas_filtered, filters)
    kyselykertas_filtered = filter_kyselykertas_by_aluejako(kyselykertas_filtered, filters)

    oppilaitos_ids = {
        kyselykerta.kyselyid.oppilaitos_id
        for kyselykerta in kyselykertas_filtered
        if kyselykerta.kyselyid.oppilaitos}
    return len(oppilaitos_ids)


def kyselykerta_created_date(kysymysryhmaid, kyselykertas, koulutustoimija, filters):
    kyselykertas_filtered = [
        kyselykerta for kyselykerta in kyselykertas
        if kyselykerta.kyselyid.metatiedot.get("valssi_kysymysryhma") == kysymysryhmaid and
        kyselykerta.kyselyid.koulutustoimija == koulutustoimija]

    kyselykertas_filtered = filter_kyselykertas_by_alkupvm(kyselykertas_filtered, filters)
    kyselykertas_filtered = filter_kyselykertas_by_language_codes(kyselykertas_filtered, filters)
    kyselykertas_filtered = filter_kyselykertas_by_aluejako(kyselykertas_filtered, filters)

    if not kyselykertas_filtered:
        return None
    created_date = kyselykertas_filtered[0].voimassa_alkupvm
    return created_date.strftime("%d.%m.%Y")


def get_available_codes(kysymysryhma: Kysymysryhma,
                        kyselykertas: QuerySet[Kyselykerta], koulutustoimija: Organisaatio,
                        vastaajas: QuerySet[Vastaaja], filters: dict):
    kyselykertas_filtered = [
        kyselykerta for kyselykerta in kyselykertas
        if kyselykerta.kyselyid.koulutustoimija == koulutustoimija and
        kyselykerta.kyselyid.metatiedot.get("valssi_kysymysryhma") == kysymysryhma.kysymysryhmaid]

    kyselykertas_filtered = filter_kyselykertas_by_alkupvm(kyselykertas_filtered, filters)
    kyselykertas_filtered = filter_kyselykertas_by_language_codes(kyselykertas_filtered, filters)

    kyselykertaids = {kyselykerta.pk for kyselykerta in kyselykertas_filtered}

    vastaajas_tehtnim = [vastaaja.tehtavanimikkeet for vastaaja in vastaajas
                         if vastaaja.kyselykertaid in kyselykertaids]

    return list({tehtnim["tehtavanimike_koodi"]
                 for vastaaja_tehtnim in vastaajas_tehtnim
                 for tehtnim in vastaaja_tehtnim
                 if isinstance(tehtnim, dict) and "tehtavanimike_koodi" in tehtnim})


def get_report_language_codes(language_codes: List[str]) -> Set[str]:
    modified_language_codes = set()
    for language_code in language_codes:
        if language_code in REPORT_FILTER_LANGUAGE_CODES["all"]:
            modified_language_codes.add(language_code)
        else:
            modified_language_codes.add(REPORT_FILTER_LANGUAGE_CODES["other"])

    return modified_language_codes


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


def get_active_aluejako_ids(
    kysymysryhma: Kysymysryhma,
    kyselykertas: QuerySet[Kyselykerta],
    koulutustoimija: Organisaatio,
    vastaajas: QuerySet[Vastaaja],
    filters: dict
):
    kyselykertas_filtered = [
        kyselykerta for kyselykerta in kyselykertas
        if kyselykerta.kyselyid.koulutustoimija == koulutustoimija and
        kyselykerta.kyselyid.metatiedot.get("valssi_kysymysryhma") == kysymysryhma.kysymysryhmaid]

    kyselykertas_filtered = filter_kyselykertas_by_alkupvm(kyselykertas_filtered, filters)
    kyselykertas_filtered = filter_kyselykertas_by_language_codes(kyselykertas_filtered, filters)

    answered_kyselykertaids = {
        vastaaja.kyselykertaid for vastaaja in vastaajas}

    active_aluejako_ids = set()
    for kyselykerta in kyselykertas_filtered:
        if (
            kyselykerta.kyselykertaid in answered_kyselykertaids and
            kyselykerta.kyselyid.oppilaitos and
            kyselykerta.kyselyid.oppilaitos.metatiedot.get("aluejako")
        ):
            active_aluejako_ids.add(kyselykerta.kyselyid.oppilaitos.metatiedot.get("aluejako"))

    return active_aluejako_ids


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
    if survey_sent_count:
        percentage = calculate_pct(survey_participants_count, survey_sent_count)
        return f"{survey_participants_count}/{survey_sent_count} ({percentage} %)"
    return ""


def get_report_oppilaitos_answered_text(data: dict) -> str:
    survey_oppilaitoses_answered_count = data["survey_oppilaitoses_answered_count"]
    survey_oppilaitoses_activated_count = data["survey_oppilaitoses_activated_count"]

    if survey_oppilaitoses_activated_count:
        return f"{survey_oppilaitoses_answered_count}/{survey_oppilaitoses_activated_count}"
    return ""


def filter_kyselykertas_by_alkupvm(kyselykertas: list, filters: dict):
    kyselykertas_filtered = kyselykertas
    if filters and filters.get("kyselykerta_alkupvm"):
        alkupvm = filters.get("kyselykerta_alkupvm")
        if isinstance(alkupvm, str):
            alkupvm = datetime.strptime(alkupvm, DATE_INPUT_FORMAT).date()
        kyselykertas_filtered = [
            kyselykerta for kyselykerta in kyselykertas_filtered
            if kyselykerta.voimassa_alkupvm == alkupvm]

    return kyselykertas_filtered


def filter_kyselykertas_by_language_codes(kyselykertas: list, filters: dict):
    kyselykertas_filtered = kyselykertas
    if filters and filters.get("language_codes"):
        kyselykertas_filtered = [
            kyselykerta for kyselykerta in kyselykertas_filtered
            if kyselykerta.kyselyid.oppilaitos and
            get_report_language_codes(
                kyselykerta.kyselyid.oppilaitos.metatiedot.get("toimintakieli_koodi", [])
            ) & filters.get("language_codes")]

    return kyselykertas_filtered


def filter_kyselykertas_by_aluejako(kyselykertas: list, filters: dict):
    kyselykertas_filtered = kyselykertas
    if filters and filters.get("aluejako"):
        aluejako = filters.get("aluejako")
        kyselykertas_filtered = [
            kyselykerta for kyselykerta in kyselykertas_filtered
            if kyselykerta.kyselyid.oppilaitos and
            kyselykerta.kyselyid.oppilaitos.metatiedot.get("aluejako", 0) == aluejako]

    return kyselykertas_filtered


def get_report_pdf_filter_texts(filters, language):
    filter_texts = {
        "title": REPORT_TRANSLATIONS["report_filter_title"][language],
        "jobtitle_title": REPORT_TRANSLATIONS["report_filter_jobtitle"][language],
        "jobtitle": REPORT_TRANSLATIONS["report_filter_no_choice"][language],
        "eligibility_title": REPORT_TRANSLATIONS["report_filter_eligibility"][language],
        "eligibility": REPORT_TRANSLATIONS["report_filter_no_choice"][language],
        "language_title": REPORT_TRANSLATIONS["report_filter_language"][language],
        "language": REPORT_TRANSLATIONS["report_filter_no_choice"][language],
        "aluejako_title": REPORT_TRANSLATIONS["report_filter_alue"][language],
        "aluejako": REPORT_TRANSLATIONS["report_filter_no_choice"][language],
    }

    if "answer_filters" in filters:
        tehtavanimike_koodi = filters["answer_filters"].get("tehtavanimike_koodi", None)
        if tehtavanimike_koodi:
            koodi_obj = Koodi.objects.filter(koodi_arvo=tehtavanimike_koodi).first()
            if koodi_obj:
                jobtitle_text = koodi_obj.nimi_fi if language == "fi" else koodi_obj.nimi_sv
                filter_texts["jobtitle"] = jobtitle_text

        kelpoisuus_kytkin = filters["answer_filters"].get("kelpoisuus_kytkin", None)
        if kelpoisuus_kytkin:
            filter_texts["eligibility"] = REPORT_TRANSLATIONS["report_filter_yes_choice"][language]

    language_codes = filters.get("language_codes", None)
    if language_codes:
        language_texts = []
        for language_code in language_codes:
            language_localisations = get_localisation_values_by_key(
                f"raportointi.toimintakieli-{language_code.lower()}")
            language_texts.append(language_localisations[language])
        language_text = ", ".join(language_texts)
    else:
        language_text = REPORT_TRANSLATIONS["report_filter_no_choice"][language]
    filter_texts["language"] = language_text

    aluejako_code = filters.get("aluejako", None)
    if aluejako_code:
        aluejakoalue_obj = AluejakoAlue.objects.filter(id=aluejako_code).first()
        if aluejakoalue_obj:
            aluejako_text = aluejakoalue_obj.name_fi if language == "fi" else aluejakoalue_obj.name_sv
            filter_texts["aluejako"] = aluejako_text

    return filter_texts


def remove_duplicate_kysymysryhmas(kysymysryhma_objs: List[Kysymysryhma]):
    kysymysryhmas_no_duplicates = []
    kysymysryhma_ids = set()
    for kysymysryhma_obj in kysymysryhma_objs:
        if kysymysryhma_obj.kysymysryhmaid not in kysymysryhma_ids:
            kysymysryhmas_no_duplicates.append(kysymysryhma_obj)
            kysymysryhma_ids.add(kysymysryhma_obj.kysymysryhmaid)

    return kysymysryhmas_no_duplicates


def sort_kysymysryhmas_by_laatutekija(kysymysryhma_objs: List[Kysymysryhma]):
    sorted_kysymysryhmas = []
    for group_range in [range(1000, 2000), range(2000, 3000), range(3000, 4000)]:
        for kysymysryhma_obj in kysymysryhma_objs:
            main_indicator = kysymysryhma_obj.metatiedot.get("paaIndikaattori", dict())
            indicator_group = main_indicator.get("group", 0)
            if indicator_group in group_range:
                sorted_kysymysryhmas.append(kysymysryhma_obj)

    return sorted_kysymysryhmas
