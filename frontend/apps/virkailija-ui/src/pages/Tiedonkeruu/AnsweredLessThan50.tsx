import {useTranslation, getI18n} from 'react-i18next';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import {
    KyselyCollectionType,
    Answer50Type,
    KyselyNotSentType,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {uniqueNumber} from '@cscfi/shared/utils/helpers';
import ButtonWithoutStyles from '../../components/ButtonWithoutStyles/ButtonWithoutStyles';
import styles from './Tiedonkeruu.module.css';

interface KyselyTableProps {
    kysely: KyselyCollectionType | null;
    handleExpandedChange: any;
    kyselyNimi: string;
}
function AnsweredLessThan50({
    kysely,
    handleExpandedChange,
    kyselyNimi,
}: KyselyTableProps) {
    const {t} = useTranslation(['tiedonkeruun-seuranta']);
    const locale = getI18n().language;
    return (
        <div className={styles['answered-less-than50-wrapper']}>
            <div className={styles['left-wrapper']}>
                <h4>{t('toimipaikat-jotka-eivat-ole')}</h4>
                {kysely?.toimipaikka_statistics?.extra_data?.kysely_not_sent?.length >
                    0 && (
                    <ul>
                        {kysely?.toimipaikka_statistics?.extra_data?.kysely_not_sent?.map(
                            (item: KyselyNotSentType) =>
                                locale === 'fi' ? (
                                    <li key={`${item.nimi_fi}_${uniqueNumber()}`}>
                                        {item.nimi_fi}
                                    </li>
                                ) : (
                                    <li key={`${item.nimi_sv}_${uniqueNumber()}`}>
                                        {item.nimi_sv}
                                    </li>
                                ),
                        )}
                    </ul>
                )}
            </div>
            <div className={styles['middle-wrapper']}>
                <h4>{t('toimipaikat-joiden-vastausprosentti-alle-50')}</h4>
                {kysely?.toimipaikka_statistics?.extra_data?.answer_pct_lt_50?.length >
                    0 && (
                    <table>
                        <tbody>
                            {kysely?.toimipaikka_statistics?.extra_data?.answer_pct_lt_50?.map(
                                (item: Answer50Type) => (
                                    <tr key={`${item.nimi_fi}_${uniqueNumber()}`}>
                                        <td>
                                            {locale === 'fi'
                                                ? item.nimi_fi
                                                : item.nimi_sv}
                                        </td>
                                        <td>{item.answer_pct} %</td>
                                    </tr>
                                ),
                            )}
                        </tbody>
                    </table>
                )}
            </div>
            <div className={styles['right-wrapper']}>
                <ButtonWithoutStyles
                    onClick={() => handleExpandedChange(kyselyNimi)}
                    style={{color: 'grey'}}
                >
                    <>
                        {t('sulje', {ns: 'yleiset'})}
                        <span className={styles['icon-wrapper']}>
                            <ExpandLessIcon />
                        </span>
                    </>
                </ButtonWithoutStyles>
            </div>
        </div>
    );
}
export default AnsweredLessThan50;
