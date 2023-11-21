import {useEffect, useRef, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {KysymysType, TextType} from '@cscfi/shared/services/Data/Data-service';

import Chart from '@cscfi/shared/components/Chart/Chart';
import {ReportingTemplateHelpText} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import InputTypes from '@cscfi/shared/components/InputType/InputTypes';
import {uniqueNumber} from '@cscfi/shared/utils/helpers';
import RenderScales from './RenderScales';

import styles from './styles.module.css';

interface ChartGroupProps {
    data?: Array<KysymysType>;
    kysymysryhmaId: number | null;
    nlimit?: number;
    preview: boolean;
    helptexts?: Array<ReportingTemplateHelpText>;
}

function ChartGroup({
    data,
    kysymysryhmaId,
    nlimit = 5,
    preview,
    helptexts,
}: ChartGroupProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['raportointi']);
    const forceUpdate: () => void = useState({})[1].bind(null, {}); // Doesn't work without

    const itemsEls = useRef([]) as any;

    const [previewHelpTexts, setPreviewHelpTexts] = useState<object>({});
    const percentList = [0, 20, 40, 60, 80, 100];
    useEffect(() => {
        window.addEventListener('resize', forceUpdate);
        // This removes listener, so it's not used on other pages.
        return () => window.removeEventListener('resize', forceUpdate);
    }, [forceUpdate]);

    // When in preview, get helper texts
    useEffect(() => {
        if (preview) {
            const reportPreviewData = JSON.parse(
                sessionStorage.getItem(`reportPreviewData_${kysymysryhmaId}`),
            );
            setPreviewHelpTexts(reportPreviewData);
        }
    }, [kysymysryhmaId, preview]);

    useEffect(() => {
        data?.forEach((_item, index) => {
            if (document.getElementById(`chartMarkers${index}`)) {
                document.getElementById(`chartMarkers${index}`).style.height = `${
                    itemsEls &&
                    itemsEls.current?.length > 0 &&
                    itemsEls.current[index].clientHeight - 13
                }px`;
            }
        });
    });
    return (
        <div>
            {data?.map((item, index) => {
                const kysymys = `${lang}` as keyof TextType;

                // TODO: support for monivalinta and possibly text questions, when specified.

                if (item.inputType === InputTypes.statictext) {
                    return (
                        <>
                            <div
                                key={`kysymys_${item.id}`}
                                className={styles['heading-and-scale']}
                            >
                                <h3>{item.title[lang as keyof TextType]}</h3>
                                <p>{item.description[lang as keyof TextType]}</p>
                            </div>
                            <p className={styles['reportbase-question-text']}>
                                {!preview
                                    ? helptexts.find((x) =>
                                          item.id === x.question_id ? x : null,
                                      )?.description_fi
                                    : previewHelpTexts?.[`kysymys_${item.id}`]?.[lang] ||
                                      null}
                            </p>
                        </>
                    );
                }
                if (!item.matrix_question_scale) {
                    return <div key={item.id} />;
                }

                return (
                    <div key={`kysymys_${item.id}`}>
                        <div className={styles['heading-and-scale']}>
                            <h3>{item.title[kysymys]?.toString()}</h3>
                            <p>{item.description[lang]}</p>
                            <span className={styles.avarage}>{t('ka')}</span>
                        </div>
                        <div>
                            <div
                                ref={(element) => {
                                    itemsEls.current[index] = element;
                                }}
                                className={styles['chart-wrapper']}
                            >
                                {item?.matrixQuestions.map((matrixquestion, i) => {
                                    const langKey = `${lang}` as keyof TextType;
                                    const answerSum =
                                        typeof item?.question_answers?.answers_sum[i] ===
                                        'number'
                                            ? (item?.question_answers?.answers_sum[
                                                  i
                                              ] as number)
                                            : 0;
                                    return (
                                        <div
                                            className={styles['heading-and-chart']}
                                            key={`matriisiJarjestys_${uniqueNumber()}`}
                                        >
                                            <div className={styles['left-wrapper']}>
                                                <h4>
                                                    {matrixquestion.title[langKey]}
                                                    {item.required && ' *'}
                                                    <br />

                                                    {item.question_answers
                                                        ? answerSum >= nlimit &&
                                                          `(n = ${item?.question_answers?.answers_sum[i]})`
                                                        : `(n = 0)`}
                                                </h4>
                                            </div>
                                            <Chart
                                                data={
                                                    item?.question_answers?.answers_int[i]
                                                }
                                                range={`${
                                                    item.matrix_question_scale &&
                                                    item.matrix_question_scale[0]?.value
                                                }-${
                                                    item.matrix_question_scale &&
                                                    item.matrix_question_scale[
                                                        item.matrix_question_scale
                                                            .length - 1
                                                    ]?.value
                                                }`}
                                                scale={item.matrix_question_scale}
                                                nlimit={nlimit}
                                            />
                                        </div>
                                    );
                                })}
                                <div
                                    id={`chartMarkers${index}`}
                                    className={styles[`percent-markers`]}
                                >
                                    {percentList.map((marker) => (
                                        <span key={`percent_scale${marker}`} />
                                    ))}
                                </div>
                                <ul className={styles['percent-list']} aria-hidden="true">
                                    {percentList.map((number, i) => (
                                        <li
                                            className={styles[`percent-list-item-${i}`]}
                                            key={`percent_list${number}`}
                                        >
                                            {number}%
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            <p className={styles[`percent-info-text`]}>
                                {t('osuus-vastaajista')} (%)
                            </p>
                            <RenderScales
                                item={item}
                                scale={
                                    item.matrix_question_scale &&
                                    item.matrix_question_scale
                                }
                            />
                        </div>
                        <p className={styles['reportbase-question-text']}>
                            {!preview
                                ? helptexts.find((x) =>
                                      item.id === x.question_id ? x : null,
                                  )?.description_fi
                                : previewHelpTexts?.[`kysymys_${item.id}`]?.[lang] ||
                                  null}
                        </p>
                    </div>
                );
            })}
        </div>
    );
}

export default ChartGroup;
