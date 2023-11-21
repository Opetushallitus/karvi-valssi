import {useContext, useEffect, useState} from 'react';
import {useObservable} from 'rxjs-hooks';
import {
    KysymysryhmaCollectionType,
    raportiointipalveluGetKysymysryhmaDataCollection$,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {useTranslation} from 'react-i18next';
import {Table, TableBody, TableCell, TableHead, TableRow} from '@mui/material';
import {formatDate} from '@cscfi/shared/utils/helpers';
import SinglePanelAccordion from '../../components/SinglePanelAccordion/SinglePanelAccordion';
import UserContext from '../../Context';
import styles from './Tiedonkeruu.module.css';

function TiedonkeruuYllapitaja() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['tiedonkeruun-seuranta']);
    const userInfo = useContext(UserContext);
    const kysymysryhmat = useObservable(
        () =>
            raportiointipalveluGetKysymysryhmaDataCollection$(userInfo!)(
                userInfo!.rooli.kayttooikeus,
                userInfo!.rooli.organisaatio,
            ),
        null,
    );
    const [krList, setKrList] = useState<KysymysryhmaCollectionType[] | undefined | null>(
        null,
    );
    useEffect(() => {
        setKrList(
            kysymysryhmat
                ? kysymysryhmat.sort(
                      (a, b) =>
                          Date.parse(a.earliest_usage_date) -
                          Date.parse(b.earliest_usage_date),
                  )
                : null,
        );
    }, [kysymysryhmat]);
    return (
        <div>
            <h1 className={styles['datacollection-heading']}>
                {t('tiedonkeruun-seuranta', {ns: 'ulkoasu'})}
            </h1>
            {krList?.map((kysymysryhma) => (
                <SinglePanelAccordion
                    dataCollection
                    alignLeft
                    alignColumn
                    openText={t('avaa', {ns: 'yleiset'})}
                    closeText={t('sulje', {ns: 'yleiset'})}
                    title={
                        kysymysryhma &&
                        (lang === 'fi' ? kysymysryhma?.nimi_fi : kysymysryhma?.nimi_sv)
                    }
                >
                    <div className={styles['tables-wrapper']}>
                        <div className={styles['left-table-wrapper']}>
                            <Table size="small" className={styles['left-table']}>
                                <TableHead>
                                    <TableRow>
                                        <TableCell />
                                        <TableCell variant="head">
                                            {t('kaytosssa')}
                                        </TableCell>
                                        <TableCell variant="head">
                                            {t('lahetetty')}
                                        </TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    <TableRow>
                                        <TableCell
                                            variant="head"
                                            component="th"
                                            scope="row"
                                        >
                                            {t('toimijat')}
                                        </TableCell>
                                        <TableCell>
                                            {kysymysryhma?.koulutustoimija_statistics
                                                ?.in_use_count ?? '-'}
                                        </TableCell>
                                        <TableCell>
                                            {kysymysryhma?.koulutustoimija_statistics
                                                ?.sent_count ?? '-'}
                                        </TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell
                                            variant="head"
                                            component="th"
                                            scope="row"
                                        >
                                            {t('toimipaikat')}
                                        </TableCell>
                                        <TableCell>
                                            {kysymysryhma?.oppilaitos_statistics
                                                ?.in_use_count ?? '-'}
                                        </TableCell>
                                        <TableCell>
                                            {kysymysryhma?.oppilaitos_statistics
                                                ?.sent_count ?? '-'}
                                        </TableCell>
                                    </TableRow>
                                </TableBody>
                            </Table>
                            <Table size="small" className={styles['left-table']}>
                                <TableHead>
                                    <TableRow>
                                        <TableCell> </TableCell>
                                        <TableCell variant="head">
                                            {t('lahetetty')}
                                        </TableCell>
                                        <TableCell variant="head">
                                            {t('vastannut')}
                                        </TableCell>
                                        <TableCell variant="head">
                                            {t('vastausprosentti')}
                                        </TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    <TableRow>
                                        <TableCell
                                            variant="head"
                                            component="th"
                                            scope="row"
                                        >
                                            {t('vastaajat')}
                                        </TableCell>
                                        <TableCell>
                                            {
                                                kysymysryhma?.vastaaja_statistics
                                                    ?.sent_count
                                            }
                                        </TableCell>
                                        <TableCell>
                                            {
                                                kysymysryhma?.vastaaja_statistics
                                                    ?.answered_count
                                            }
                                        </TableCell>
                                        <TableCell>
                                            {
                                                kysymysryhma?.vastaaja_statistics
                                                    ?.answer_pct
                                            }{' '}
                                            %
                                        </TableCell>
                                    </TableRow>
                                </TableBody>
                            </Table>
                        </div>
                        <div className={styles['right-table-wrapper']}>
                            <table className={styles['right-table']}>
                                <tbody>
                                    <tr>
                                        <th>{t('lomake-julkaistu')}</th>
                                        <td>{formatDate(kysymysryhma?.released_date)}</td>
                                    </tr>
                                    <tr>
                                        <th>{t('lomake-otettu-kayttoon')}</th>
                                        <td>
                                            {formatDate(
                                                kysymysryhma?.earliest_usage_date,
                                            )}
                                        </td>
                                    </tr>
                                    <tr>
                                        <th>{t('viimeisin-kysely-sulkeutuu')}</th>
                                        <td>
                                            {formatDate(kysymysryhma?.latest_ending_date)}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </SinglePanelAccordion>
            ))}
        </div>
    );
}

export default TiedonkeruuYllapitaja;
