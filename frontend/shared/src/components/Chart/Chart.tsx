import {getI18n, useTranslation} from 'react-i18next';
import {MatrixQuestionScaleType} from '@cscfi/shared/services/Data/Data-service';
import {round} from '@cscfi/shared/utils/helpers';
import styles from './styles.module.css';

interface ChartProps {
    data?: Array<number>;
    range: string;
    scale?: Array<MatrixQuestionScaleType>;
    nlimit: number;
}

function Chart({data, range, scale, nlimit}: ChartProps) {
    const {t} = useTranslation(['raportointi']);
    const locale = getI18n().language;
    let total = 0;
    let totalScale = 0;
    data?.forEach((element, i) => {
        total += element;
        totalScale += (i + 1) * element;
    });
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
                {data?.map(
                    (item, i) =>
                        item > 0 && (
                            <li
                                className={styles[`item-${i}-range-${range}`]}
                                style={{
                                    width: `${(item / total) * 100}%`,
                                }}
                                aria-label={scale && scale[i]?.[locale]}
                                key={`value_${Math.random()}`}
                            >
                                <span>{round((item / total) * 100)}</span>
                            </li>
                        ),
                )}
            </ul>
            <p>
                {round(totalScale / total, 1)
                    .toString()
                    .replace('.', ',')}
            </p>
        </div>
    );
}

export default Chart;
