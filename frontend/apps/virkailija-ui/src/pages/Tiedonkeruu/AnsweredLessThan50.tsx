import {useTranslation, getI18n} from 'react-i18next';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import {
    KyselyCollectionType,
    Answer50Type,
    KyselyNotSentType,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {uniqueNumber} from '@cscfi/shared/utils/helpers';
import Grid from '@mui/material/Grid';
import ButtonWithoutStyles from '../../components/ButtonWithoutStyles/ButtonWithoutStyles';
import styles from './Tiedonkeruu.module.css';

interface KyselyTableProps {
    id: string;
    kysely: KyselyCollectionType | null;
    handleExpandedChange: () => void;
}
function AnsweredLessThan50({id, kysely, handleExpandedChange}: KyselyTableProps) {
    const {t} = useTranslation(['tiedonkeruun-seuranta']);
    const locale = getI18n().language;

    const nameAndPct = (item: Answer50Type) => {
        const name = locale === 'fi' ? item.nimi_fi : item.nimi_sv;
        return (
            <tr key={`${name}_${uniqueNumber()}`}>
                <td>{name}</td>
                <td>{item.answer_pct} %</td>
            </tr>
        );
    };

    const nameAndPctList = (items: any | undefined) =>
        items?.length > 0 ? (
            <table className={styles['toimipaikat-list']}>
                <tbody>{items.map((item: Answer50Type) => nameAndPct(item))}</tbody>
            </table>
        ) : (
            []
        );

    return (
        <Grid
            container
            direction="column"
            className={styles['answered-less-than50-wrapper']}
        >
            <Grid size="auto" alignSelf="flex-end" marginBottom="0.5rem">
                <ButtonWithoutStyles
                    onClick={() => handleExpandedChange()}
                    style={{color: 'grey'}}
                    isExpanded
                    ariaControls={id}
                >
                    <span className={styles['close-button-content']}>
                        {t('sulje', {ns: 'yleiset'})}
                        <ExpandLessIcon />
                    </span>
                </ButtonWithoutStyles>
            </Grid>
            <Grid container direction="row" rowSpacing={4} columnSpacing={6} id={id}>
                <Grid>
                    <h4 className={styles['list-heading']}>
                        {t('toimipaikat-jotka-eivat-ole')}
                    </h4>
                    <ul className={styles['toimipaikat-list']}>
                        {kysely?.toimipaikka_statistics?.extra_data?.kysely_not_sent?.map(
                            (item: KyselyNotSentType) => {
                                const name =
                                    locale === 'fi' ? item.nimi_fi : item.nimi_sv;
                                return <li key={`${name}_${uniqueNumber()}`}>{name}</li>;
                            },
                        )}
                    </ul>
                </Grid>
                <Grid>
                    <h4 className={styles['list-heading']}>
                        {t('toimipaikat-joiden-vastausprosentti-alle-50')}
                    </h4>
                    {nameAndPctList(
                        kysely?.toimipaikka_statistics?.extra_data?.answer_pct_lt_50,
                    )}
                </Grid>
                <Grid>
                    <h4 className={styles['list-heading']}>
                        {t('toimipaikat-joiden-vastausprosentti-yli-50')}
                    </h4>
                    {nameAndPctList(
                        kysely?.toimipaikka_statistics?.extra_data?.answer_pct_gte_50,
                    )}
                </Grid>
            </Grid>
        </Grid>
    );
}
export default AnsweredLessThan50;
