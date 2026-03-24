import {useEffect, useMemo, useRef, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {KysymysType, TextType} from '@cscfi/shared/services/Data/Data-service';

import Chart from '@cscfi/shared/components/Chart/Chart';
import {ReportingTemplateHelpText} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import InputTypes, {
    KysymysMatrixTypes,
    KysymysStringTypes,
    MonivalintaTypes,
} from '@cscfi/shared/components/InputType/InputTypes';
import TitleField from '@cscfi/shared/components/Form/FormFields/TitleField/TitleField';
import MultipleChoiceChart from '@cscfi/virkailija-ui/src/pages/Raportointi/MultipleChoiceChart/MultipleChoiceChart';
import RenderScales from './RenderScales';

import styles from './styles.module.css';

interface ChartGroupProps {
    data?: Array<KysymysType>;
    kysymysryhmaId: number | null;
    nlimit?: number;
    preview: boolean;
    helptexts?: Array<ReportingTemplateHelpText>;
    language?: string;
}

function ChartGroup({
    data,
    kysymysryhmaId,
    nlimit = 5,
    preview,
    helptexts,
    language,
}: ChartGroupProps) {
    const {i18n} = useTranslation(['raportointi']);

    const langKey = language ?? i18n.language;

    const uiLang = i18n.language;

    const fixedT = useMemo(() => i18n.getFixedT(langKey, 'raportointi'), [langKey, i18n]);

    const forceUpdate: () => void = useState({})[1].bind(null, {}); // Doesn't work without

    const itemsEls = useRef([]) as any;

    const previewHelpTexts = useMemo(() => {
        if (!preview) return undefined;
        const raw = sessionStorage.getItem(`reportPreviewData_${kysymysryhmaId}`);
        try {
            return raw ? JSON.parse(raw) : undefined;
        } catch {
            return undefined;
        }
    }, [preview, kysymysryhmaId]);

    const percentList = [0, 20, 40, 60, 80, 100];
    useEffect(() => {
        window.addEventListener('resize', forceUpdate);
        // This removes listener, so it's not used on other pages.
        return () => window.removeEventListener('resize', forceUpdate);
    }, [forceUpdate]);

    useEffect(() => {
        data?.forEach((_item, index) => {
            if (document.getElementById(`chartMarkers${index}`)) {
                document.getElementById(`chartMarkers${index}`).style.height = `${
                    itemsEls?.current?.length > 0 &&
                    itemsEls.current[index].clientHeight - 13
                }px`;
            }
        });
    });

    return (
        <div>
            {data?.map((item, index) => {
                const kysymys = langKey as keyof TextType;

                if (item?.hidden) {
                    return null;
                }

                // support for more question types can be added below

                if (KysymysStringTypes.includes(item.inputType) && !item.insta) {
                    return (
                        <div key={`kysymys_${item.id}_${index}`}>
                            <div className={styles['heading-and-scale']}>
                                <h3>{item?.title[kysymys]}</h3>
                                <p>{item?.string_answer[uiLang]}</p>
                            </div>
                        </div>
                    );
                }

                if (item.inputType === InputTypes.statictext) {
                    if (item?.string_answer?.fi) {
                        return (
                            <div key={`kysymys_${item.id}_${index}`}>
                                <div className={styles['heading-and-scale']}>
                                    <h3>{item?.title[kysymys]}</h3>
                                    <p>{item?.string_answer[uiLang]}</p>
                                </div>
                            </div>
                        );
                    }
                    return (
                        <div key={`kysymys_${item.id}_${index}`}>
                            <div className={styles['heading-and-scale']}>
                                <TitleField
                                    title={item?.title[langKey as keyof TextType]}
                                    description={
                                        item?.description[langKey as keyof TextType]
                                    }
                                />
                            </div>
                            <p className={styles['reportbase-question-text']}>
                                {!preview
                                    ? helptexts.find((x) =>
                                          item.id === x.question_id ? x : null,
                                      )?.description_fi
                                    : previewHelpTexts?.[`kysymys_${item.id}`]?.[
                                          langKey
                                      ] || null}
                            </p>
                        </div>
                    );
                }
                if (KysymysMatrixTypes.includes(item.inputType)) {
                    if (item?.string_answer?.fi) {
                        return (
                            <div key={`kysymys_${item.id}_${index}`}>
                                <div className={styles['heading-and-scale']}>
                                    <h3>{item?.title[kysymys]}</h3>
                                    <p>{item?.string_answer[uiLang]}</p>
                                </div>
                            </div>
                        );
                    }
                    return (
                        <div key={`kysymys_${item.id}`}>
                            <div className={styles['heading-and-scale']}>
                                <h3>{item?.title[kysymys]}</h3>
                                <p>{item?.description[langKey]}</p>
                                <span className={styles.avarage}>{fixedT('ka')}</span>
                            </div>
                            <div>
                                <div
                                    ref={(element) => {
                                        itemsEls.current[index] = element;
                                    }}
                                    className={styles['chart-wrapper']}
                                >
                                    {item?.matrixQuestions.map((matrixquestion, i) => {
                                        const langSelection = langKey as keyof TextType;
                                        const answerSum =
                                            typeof item?.question_answers?.answers_sum[
                                                i
                                            ] === 'number'
                                                ? (item?.question_answers?.answers_sum[
                                                      i
                                                  ] as number)
                                                : 0;
                                        return (
                                            <div
                                                className={styles['heading-and-chart']}
                                                key={`matriisiJarjestys_${matrixquestion.id + '_' + i}`}
                                            >
                                                <div className={styles['left-wrapper']}>
                                                    <h4>
                                                        {
                                                            matrixquestion.title[
                                                                langSelection
                                                            ]
                                                        }
                                                        {item.required && ' *'}
                                                        <br />

                                                        {item?.question_answers
                                                            ? answerSum >= nlimit &&
                                                              `(n = ${item?.question_answers?.answers_sum[i]})`
                                                            : `(n = 0)`}
                                                    </h4>
                                                </div>
                                                <Chart
                                                    answersSum={
                                                        item?.question_answers
                                                            ?.answers_int[
                                                            i
                                                        ] as Array<number>
                                                    }
                                                    answersPct={
                                                        item?.question_answers
                                                            ?.answers_pct[
                                                            i
                                                        ] as Array<number>
                                                    }
                                                    range={`${
                                                        item.matrix_question_scale?.[0]
                                                            ?.value
                                                    }-${
                                                        item.matrix_question_scale?.[
                                                            item.matrix_question_scale
                                                                .length - 1
                                                        ]?.value
                                                    }`}
                                                    average={item?.question_answers?.answers_average[
                                                        i
                                                    ].toString()}
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
                                    <ul
                                        className={styles['percent-list']}
                                        aria-hidden="true"
                                    >
                                        {percentList.map((number, i) => (
                                            <li
                                                className={
                                                    styles[`percent-list-item-${i}`]
                                                }
                                                key={`percent_list${number}`}
                                            >
                                                {number}%
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                                <p className={styles[`percent-info-text`]}>
                                    {fixedT('osuus-vastaajista')} (%)
                                </p>
                                <RenderScales
                                    item={item}
                                    scale={
                                        item.matrix_question_scale &&
                                        item.matrix_question_scale
                                    }
                                    language={langKey}
                                />
                            </div>
                            <p className={styles['reportbase-question-text']}>
                                {!preview
                                    ? helptexts.find((x) =>
                                          item.id === x.question_id ? x : null,
                                      )?.description_fi
                                    : previewHelpTexts?.[`kysymys_${item.id}`]?.[
                                          langKey
                                      ] || null}
                            </p>
                        </div>
                    );
                }
                if (MonivalintaTypes.includes(item.inputType)) {
                    if (item?.string_answer?.fi) {
                        return (
                            <div key={`kysymys_${item.id}_${index}`}>
                                <div className={styles['heading-and-scale']}>
                                    <h3>{item?.title[kysymys]}</h3>
                                    <p>{item?.string_answer[uiLang]}</p>
                                </div>
                            </div>
                        );
                    }
                    return (
                        <div key={item.id}>
                            <div className={styles['heading-and-scale']}>
                                <h3>{item.title[kysymys]?.toString()}</h3>
                                {item.description[langKey] && (
                                    <p className={styles['heading-description']}>
                                        {item.description[langKey]}
                                    </p>
                                )}
                            </div>
                            <MultipleChoiceChart
                                questions={item.answerOptions}
                                answers={item.question_answers}
                                multipleSelect={item.inputType === InputTypes.checkbox}
                                language={langKey}
                            />
                        </div>
                    );
                }
                return <div key={item.id} />;
            })}
        </div>
    );
}

export default ChartGroup;
