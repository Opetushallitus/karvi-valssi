import {
    Bar,
    BarChart,
    CartesianGrid,
    LabelList,
    ResponsiveContainer,
    Text,
    XAxis,
    YAxis,
} from 'recharts';
import {
    CheckBoxType,
    QuestionAnswersType,
    TextType,
} from '@cscfi/shared/services/Data/Data-service';
import {useTranslation} from 'react-i18next';
import {useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState} from 'react';
import styles from './MultipleChoiceChart.module.css';

interface MultipleChoiceChartProps {
    questions: CheckBoxType[];
    answers: QuestionAnswersType;
    multipleSelect: boolean;
    language?: string;
}

const MultipleChoiceChart = ({
    questions,
    answers,
    multipleSelect,
    language,
}: MultipleChoiceChartProps) => {
    const {i18n} = useTranslation(['raportointi']);

    const [langKey, setLangKey] = useState<string>(language ?? i18n.language);

    useEffect(() => {
        if (language) {
            setLangKey(language);
        }
    }, [language]);

    useEffect(() => {
        setLangKey(i18n.language);
    }, [i18n.language]);

    const fixedT = useMemo(() => i18n.getFixedT(langKey, 'raportointi'), [langKey, i18n]);
    const answersAvailable = answers?.answers_available;

    const [rowHeights, setRowHeights] = useState<number[]>([]);
    const [labelContainerWidth, setLabelContainerWidth] = useState<number>(200);
    const labelContainerRef = useRef<HTMLDivElement | null>(null);

    // Initialize chart data. Empty last row for the purposes of the x-axis labels.
    const data = questions
        .map((question, i) => {
            return {
                name: question.title[langKey as keyof TextType],
                int: answers?.answers_int?.[i] || 0,
                pct: answers?.answers_pct?.[i] || 0,
            };
        })
        .concat([{name: '', int: 0, pct: 0}]);

    useLayoutEffect(() => {
        const el = labelContainerRef.current;
        if (!el) return;

        const update = () => setLabelContainerWidth(el.offsetWidth);

        update(); // mittaa heti
        const ro = new ResizeObserver(() => update());
        ro.observe(el);
        return () => ro.disconnect();
    }, []);

    // Trigger one resize to make sure labels adjust correctly
    useEffect(() => {
        const timeout = setTimeout(() => {
            window.dispatchEvent(new Event('resize'));
        }, 100); // delay for resize
        return () => clearTimeout(timeout);
    }, []);

    const barSize = 40; // Height of each bar in px
    const surfaceHeight = 85;

    const CustomYTick = (props: any) => {
        const {x, payload, height, tickIndex, showN} = props;

        // Päivitä mitattu korkeus tilaan vain kun arvo oikeasti muuttuu
        const measureRef = useCallback(
            (el: HTMLDivElement | null) => {
                if (el) {
                    const measured = Math.max(el.offsetHeight, surfaceHeight);
                    setRowHeights((prev) => {
                        if (prev[tickIndex] === measured) return prev;
                        const next = [...prev];
                        next[tickIndex] = measured;
                        return next;
                    });
                }
            },
            [tickIndex],
        );

        const thisHeight = rowHeights[tickIndex] ?? surfaceHeight;
        const parentWidth = labelContainerWidth; // ei ref-lukua renderissä
        const gYPosition = height / 2 - (thisHeight ?? 0) / 2;

        // n arvo haetaan datasta kuten ennenkin
        const n = data[tickIndex]?.int ?? 0;

        return (
            <g transform={`translate(${x},${gYPosition})`}>
                <foreignObject x={-56} width={parentWidth} height={thisHeight}>
                    <div
                        ref={measureRef}
                        style={{display: 'flex', flexDirection: 'column'}}
                    >
                        <span className={styles['label-text']}>{payload.value}</span>
                        {showN && <span children={`(n = ${n})`} />}
                    </div>
                </foreignObject>
            </g>
        );
    };

    // Content shown inside an individual bar
    const customLabelContent = (props: any) => {
        const {x, y, width, height, value, showPct} = props;
        const fireOffset = value <= 5; // content shown on right side of the bar

        return (
            showPct && (
                <Text
                    x={fireOffset ? x + width + 5 : x + width / 2}
                    y={y + height / 2}
                    textAnchor={fireOffset ? 'start' : 'middle'}
                    verticalAnchor={'middle'}
                    alignmentBaseline="central"
                    fill={'black'}
                >
                    {value}
                </Text>
            )
        );
    };

    /*
     * The chart is formed of multiple charts. For each row the Y-axis
     * labels and the bar are individual charts, and the X-axis labels
     * are their own chart.
     *
     * The reason is that Recharts does not support variable bar
     * heights for each bar in a bar chart. If Rechars ever starts
     * supporting this, the chart can be made with a single <BarChart>.
     * */
    return (
        <>
            {answersAvailable ? (
                <span className={styles['answer-count']}>
                    {fixedT('vastausprosentti')}: {answers?.answers_count || 0}
                    {multipleSelect &&
                        `, ${fixedT('vastausten-maara')}: ${answers?.answers_sum || 0}`}
                </span>
            ) : (
                <span className={styles['answer-count']}>
                    <b>{fixedT('vastauksia-vahemman-kuin-5-ei-voida-nayttaa')}</b>
                </span>
            )}

            {data.map((d, i) => {
                const lastItem = i === data.length - 1;
                const elementHeight = rowHeights[i] ?? surfaceHeight;
                return (
                    <div
                        key={`chartrow_${i}`}
                        className={styles['chart-wrapper']}
                        style={{
                            height: !lastItem ? elementHeight : 20,
                        }}
                    >
                        <div style={{width: '35%'}} ref={labelContainerRef}>
                            {!lastItem && (
                                <ResponsiveContainer width="100%" height={elementHeight}>
                                    <BarChart layout="vertical" data={[d]}>
                                        <YAxis
                                            type="category"
                                            dataKey="name"
                                            axisLine={false}
                                            stroke={'black'}
                                            tickLine={false}
                                            tick={
                                                lastItem ? (
                                                    <></>
                                                ) : (
                                                    <CustomYTick
                                                        height={elementHeight}
                                                        tickIndex={i}
                                                        showN={answersAvailable}
                                                    />
                                                )
                                            }
                                        />
                                    </BarChart>
                                </ResponsiveContainer>
                            )}
                        </div>

                        <div style={{width: '65%'}}>
                            <ResponsiveContainer
                                width="100%"
                                height={!lastItem ? elementHeight : 20}
                            >
                                <BarChart
                                    layout="vertical"
                                    data={[d]}
                                    barSize={barSize}
                                    barGap={elementHeight}
                                    margin={{top: 0, bottom: 0, right: 0, left: 0}}
                                >
                                    {!lastItem && (
                                        <CartesianGrid
                                            horizontalValues={['']}
                                            stroke="#000000"
                                        />
                                    )}

                                    <XAxis
                                        type="number"
                                        hide={!lastItem}
                                        domain={[0, 100]}
                                        scale={'linear'}
                                        axisLine={false}
                                        stroke={'black'}
                                        tickFormatter={(tick) => `${tick}%`}
                                        tickMargin={10}
                                    />

                                    <YAxis type="category" dataKey={'name'} hide />

                                    {!lastItem && (
                                        <Bar
                                            dataKey="pct"
                                            fill="#85c598"
                                            stroke={'black'}
                                            strokeWidth={1}
                                        >
                                            <LabelList
                                                dataKey="pct"
                                                content={(props) =>
                                                    customLabelContent({
                                                        ...props,
                                                        showPct: answersAvailable,
                                                    })
                                                }
                                                fill={'black'}
                                            />
                                        </Bar>
                                    )}
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                );
            })}
        </>
    );
};

export default MultipleChoiceChart;
