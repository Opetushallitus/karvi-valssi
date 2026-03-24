import React, {useContext, useState, useEffect} from 'react';
import {
    KysymysryhmaCollectionType,
    KysymysryhmaStatisticsType,
    raportiointipalveluGetKysymysryhmaDataCollection$,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {useTranslation} from 'react-i18next';
import {subYears, format} from 'date-fns';
import {Table, TableBody, TableCell, TableHead, TableRow} from '@mui/material';
import {formatDate} from '@cscfi/shared/utils/helpers';
import KyselyajankohtaValitsin from '../../components/KyselyajankohtaValitsin/KyselyajankohtaValitsin';
import FocusableHeader from '../../components/FocusableHeader/FocusableHeader';
import SinglePanelAccordion from '../../components/SinglePanelAccordion/SinglePanelAccordion';
import UserContext from '../../Context';
import styles from './Tiedonkeruu.module.css';

function getUsageDate(krCollection: KysymysryhmaCollectionType, earliestUsage = true) {
    const dates = [
        krCollection.kunnallinen[
            earliestUsage ? 'earliest_usage_date' : 'latest_ending_date'
        ],
        krCollection.yksityinen[
            earliestUsage ? 'earliest_usage_date' : 'latest_ending_date'
        ],
    ];
    return new Date(Math.max(...dates.map((date) => Date.parse(date))));
}

function TiedonkeruuYllapitaja() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['tiedonkeruun-seuranta']);
    const userInfo = useContext(UserContext);

    const [startDate, setStartDate] = useState<Date | null>(subYears(new Date(), 1));
    const [endDate, setEndDate] = useState<Date | null>(null);
    const [krList, setKrList] = useState<KysymysryhmaCollectionType[]>([]);

    useEffect(() => {
        raportiointipalveluGetKysymysryhmaDataCollection$(userInfo!)(
            userInfo!.rooli.kayttooikeus,
            userInfo!.rooli.organisaatio,
            startDate && format(startDate, 'yyyy-MM-dd'),
            endDate && format(endDate, 'yyyy-MM-dd'),
        ).subscribe((krcoll) => {
            setKrList(
                krcoll.sort(
                    (a, b) =>
                        getUsageDate(a, true).getTime() - getUsageDate(b, true).getTime(),
                ),
            );
        });
    }, [startDate, endDate, userInfo]);

    function statTables(
        kr: KysymysryhmaCollectionType,
        statistics: KysymysryhmaStatisticsType,
        yksityinen: boolean,
    ) {
        const toimijaType = yksityinen ? 'yksityinen' : 'kunnallinen';
        return (
            <>
                <h4 className={styles['stat-table-heading']}>
                    {t(yksityinen ? 'otsikko-yksityiset' : 'otsikko-kunnat')}
                </h4>
                <div className={styles['tables-wrapper']}>
                    <div className={styles['left-table-wrapper']}>
                        <Table size="small" className={styles['left-table']}>
                            <TableHead>
                                <TableRow>
                                    <TableCell />
                                    <TableCell variant="head">{t('kaytosssa')}</TableCell>
                                    <TableCell variant="head">{t('lahetetty')}</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                <TableRow>
                                    <TableCell variant="head" component="th" scope="row">
                                        {t('toimijat')}
                                    </TableCell>
                                    <TableCell>
                                        {statistics.koulutustoimija_statistics
                                            ?.in_use_count ?? '-'}
                                    </TableCell>
                                    <TableCell>
                                        {statistics.koulutustoimija_statistics
                                            ?.sent_count ?? '-'}
                                    </TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell variant="head" component="th" scope="row">
                                        {t('toimipaikat')}
                                    </TableCell>
                                    <TableCell>
                                        {statistics.oppilaitos_statistics?.in_use_count ??
                                            '-'}
                                    </TableCell>
                                    <TableCell>
                                        {statistics.oppilaitos_statistics?.sent_count ??
                                            '-'}
                                    </TableCell>
                                </TableRow>
                            </TableBody>
                        </Table>
                        <Table size="small" className={styles['left-table']}>
                            <TableHead>
                                <TableRow>
                                    <TableCell> </TableCell>
                                    <TableCell variant="head">
                                        {t('toimipaikat')}
                                    </TableCell>
                                    <TableCell variant="head">{t('lahetetty')}</TableCell>
                                    <TableCell variant="head">{t('vastannut')}</TableCell>
                                    <TableCell variant="head">
                                        {t('vastausprosentti')}
                                    </TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                <TableRow>
                                    <TableCell variant="head" component="th" scope="row">
                                        {t('vastaajat')}
                                    </TableCell>
                                    <TableCell>
                                        {
                                            statistics.vastaaja_statistics
                                                ?.oppilaitos_answered_count
                                        }
                                    </TableCell>
                                    <TableCell>
                                        {statistics.vastaaja_statistics?.sent_count}
                                    </TableCell>
                                    <TableCell>
                                        {statistics.vastaaja_statistics?.answered_count}
                                    </TableCell>
                                    <TableCell>
                                        {statistics.vastaaja_statistics?.answer_pct} %
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
                                    <td>{formatDate(kr?.released_date)}</td>
                                </tr>
                                <tr>
                                    <th>{t('lomake-otettu-kayttoon')}</th>
                                    <td>
                                        {formatDate(
                                            kr?.[`${toimijaType}`].earliest_usage_date,
                                        )}
                                    </td>
                                </tr>
                                <tr>
                                    <th>{t('viimeisin-kysely-sulkeutuu')}</th>
                                    <td>
                                        {formatDate(
                                            kr?.[`${toimijaType}`].latest_ending_date,
                                        )}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </>
        );
    }

    return (
        <div>
            <FocusableHeader className={styles['datacollection-heading']}>
                <>{t('tiedonkeruun-seuranta', {ns: 'ulkoasu'})}</>
            </FocusableHeader>

            <div>
                <h2>{t('lomakkeiden-suodatus')}</h2>
                <div className={styles['tiedonkeruu-options-wrapper']}>
                    <KyselyajankohtaValitsin
                        dateStart={startDate}
                        dateEnd={endDate}
                        onChangeStart={setStartDate}
                        onChangeEnd={setEndDate}
                    />
                </div>
            </div>

            <div className={styles['tiedonkeruu-page-wrapper']}>
                {krList?.map((kysymysryhma) => (
                    <React.Fragment key={`key_${kysymysryhma.kysymysryhmaid}`}>
                        <SinglePanelAccordion
                            dataCollection
                            alignLeft
                            alignColumn
                            openText={t('avaa', {ns: 'yleiset'})}
                            closeText={t('sulje', {ns: 'yleiset'})}
                            title={
                                kysymysryhma &&
                                (lang === 'fi'
                                    ? kysymysryhma?.nimi_fi
                                    : kysymysryhma?.nimi_sv)
                            }
                        >
                            {statTables(kysymysryhma, kysymysryhma.kunnallinen, false)}
                            {statTables(kysymysryhma, kysymysryhma.yksityinen, true)}
                        </SinglePanelAccordion>
                    </React.Fragment>
                ))}
            </div>
        </div>
    );
}

export default TiedonkeruuYllapitaja;
