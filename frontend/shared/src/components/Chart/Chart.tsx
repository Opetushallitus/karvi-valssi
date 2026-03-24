import {getI18n, useTranslation} from 'react-i18next';
import {MatrixQuestionScaleType} from '@cscfi/shared/services/Data/Data-service';
import styles from './styles.module.css';

interface ChartProps {
    answersSum?: Array<number>;
    answersPct: Array<number>;
    range: string;
    average?: string;
    scale?: Array<MatrixQuestionScaleType>;
    nlimit: number;
}

function Chart({answersSum, answersPct, range, average, scale, nlimit}: ChartProps) {
    const {t} = useTranslation(['raportointi']);
    const locale = getI18n().language;
    const total = answersSum?.reduce((acc, n) => acc + n, 0);
    if (total < nlimit) {
        return (
            <div className={styles['list-wrapper']}>
                <div className={styles['list-cutter']}>
                    <ul className={styles.empty}>
                        <li>
                            <span>
                                {t('vastauksia-vahemman-kuin-5-ei-voida-nayttaa')}
                            </span>
                        </li>
                    </ul>
                </div>
            </div>
        );
    }
    return (
        <div className={styles['list-wrapper']}>
            <ul className={styles.chart}>
                {answersPct?.map(
                    (item, i) =>
                        item > 0 && (
                            <li
                                className={styles[`item-${i}-range-${range}`]}
                                style={{
                                    width: `${(answersSum[i] / total) * 100}%`,
                                }}
                                aria-label={scale && scale[i]?.[locale]}
                                key={`value_${i}`}
                            >
                                <span>{item}</span>
                            </li>
                        ),
                )}
            </ul>
            <p>{average}</p>
        </div>
    );
}

export default Chart;
