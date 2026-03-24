import {useState} from 'react';
import {useTranslation} from 'react-i18next';
import DateRangePickerField from '@cscfi/shared/components/DateRangePickerField/DateRangePickerField';
import styles from './KyselyajankohtaValitsin.module.css';

interface KyselykertaValitsinProps {
    dateStart: Date | null;
    dateEnd: Date | null;
    onChangeStart: (date: Date | null) => void;
    onChangeEnd: (date: Date | null) => void;
    valuesRequired?: boolean | null;
    title?: string | null;
}

function KyselyajankohtaValitsin({
    dateStart,
    dateEnd,
    onChangeStart,
    onChangeEnd,
    valuesRequired,
    title,
}: KyselykertaValitsinProps) {
    const {t} = useTranslation(['tiedonkeruun-seuranta']);

    const [startDateValitsin, setStartDateValitsin] = useState<Date | null>(dateStart);
    const [endDateValitsin, setEndDateValitsin] = useState<Date | null>(dateEnd);

    return (
        <div>
            <h3>{title ? title : t('kyselyajnkohta-valitsin-otsikko')}</h3>
            <div className={styles['date-wrapper']}>
                <DateRangePickerField
                    dateStart={startDateValitsin || undefined}
                    dateEnd={endDateValitsin || undefined}
                    onChangeStart={setStartDateValitsin}
                    onChangeEnd={setEndDateValitsin}
                    labelStart={t('alkupvm', {ns: 'yleiset'})}
                    labelEnd={t('loppupvm', {ns: 'yleiset'})}
                />
            </div>
            <div className={styles['button-wrapper']}>
                {!valuesRequired && (
                    <button
                        disabled={startDateValitsin === null && endDateValitsin === null}
                        type="button"
                        className="secondary"
                        onClick={() => {
                            setStartDateValitsin(null);
                            setEndDateValitsin(null);
                            onChangeStart(null);
                            onChangeEnd(null);
                        }}
                    >
                        {t('kyselyajankohta-valitsin-tyhjenna')}
                    </button>
                )}
                <button
                    type="button"
                    onClick={() => {
                        onChangeStart(startDateValitsin);
                        onChangeEnd(endDateValitsin);
                    }}
                >
                    {t('kyselyajankohta-valitsin-paivita')}
                </button>
            </div>
        </div>
    );
}

export default KyselyajankohtaValitsin;
