import {
    raportointipalveluGetRangeResultCsv$,
    raportointipalveluGetRangeSummaryCsv$,
    raportointipalveluGetYllapitajaRaportit,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import React, {useContext, useEffect, useState} from 'react';
import {subYears, format, subDays} from 'date-fns';
import Grid from '@mui/material/Grid';
import {downloadCsv} from '@cscfi/shared/utils/helpers';
import {useTranslation} from 'react-i18next';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import KyselyajankohtaValitsin from '../../components/KyselyajankohtaValitsin/KyselyajankohtaValitsin';
import styles from '../Tiedonkeruu/Tiedonkeruu.module.css';
import UserContext from '../../Context';

function YllapitajaList() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['raportointi']);
    const langKey = lang as keyof TextType;
    const userInfo = useContext(UserContext);
    const [startDate, setStartDate] = useState<Date | null>(subYears(new Date(), 1));
    const [endDate, setEndDate] = useState<Date | null>(subDays(new Date(), 1));
    const [raportit, setRaportit] = useState([]);

    useEffect(() => {
        raportointipalveluGetYllapitajaRaportit(userInfo!)(
            startDate ? format(startDate, 'yyyy-MM-dd') : '',
            endDate ? format(endDate, 'yyyy-MM-dd') : '',
        ).subscribe((yllapitajanRaportit) => {
            setRaportit(yllapitajanRaportit);
        });
    }, [startDate, endDate, userInfo]);

    function handleYhteenvetoClick(raportName: string, kysymysryhmaid: string) {
        downloadCsv(
            raportointipalveluGetRangeSummaryCsv$(userInfo!)(
                kysymysryhmaid,
                startDate ? format(startDate, 'yyyy-MM-dd') : '',
                endDate ? format(endDate, 'yyyy-MM-dd') : '',
            ),
            t('yhteenvedot') + '_' + raportName + '.csv',
        );
    }

    function handleArviointituloksetClick(raportName: string, kysymysryhmaid: string) {
        downloadCsv(
            raportointipalveluGetRangeResultCsv$(userInfo!)(
                kysymysryhmaid,
                startDate ? format(startDate, 'yyyy-MM-dd') : '',
                endDate ? format(endDate, 'yyyy-MM-dd') : '',
            ),
            t('esikatselu-otsikko', {ns: 'arviointitulokset'}) +
                '_' +
                raportName +
                '.csv',
        );
    }

    return (
        <div>
            <div className={styles['tiedonkeruu-options-wrapper']}>
                <KyselyajankohtaValitsin
                    dateStart={startDate}
                    dateEnd={endDate}
                    onChangeStart={setStartDate}
                    onChangeEnd={setEndDate}
                    valuesRequired={true}
                />
            </div>

            {raportit && (
                <div>
                    <h3>{t('prosessitekijat')}</h3>
                    {raportit
                        .filter((raportti2) => raportti2?.laatutekija === 'prosessi')
                        .map((raportti) => (
                            <div>
                                <div>
                                    <Grid
                                        container
                                        item
                                        className={styles['grid-row']}
                                        size={12}
                                    >
                                        <Grid
                                            item
                                            style={{alignContent: 'center'}}
                                            size={6}
                                        >
                                            {langKey === 'fi'
                                                ? raportti?.name?.fi
                                                : raportti?.name?.sv}
                                        </Grid>
                                        <Grid item size={1.5}>
                                            <button disabled={true}>
                                                {t('aineisto')}
                                            </button>
                                        </Grid>
                                        <Grid item size={1.5}>
                                            <button disabled={true}>
                                                {t('raportti')}
                                            </button>
                                        </Grid>
                                        <Grid item size={1.5}>
                                            <button
                                                disabled={!raportti?.show_summary}
                                                onClick={() =>
                                                    handleYhteenvetoClick(
                                                        langKey === 'fi'
                                                            ? raportti?.name?.fi
                                                            : raportti?.name?.sv,
                                                        raportti?.kysymysryhmaid,
                                                    )
                                                }
                                            >
                                                {t('yhteenvedot')}
                                            </button>
                                        </Grid>
                                        <Grid item size={1.5}>
                                            <button
                                                disabled={!raportti?.show_result}
                                                onClick={() =>
                                                    handleArviointituloksetClick(
                                                        langKey === 'fi'
                                                            ? raportti?.name?.fi
                                                            : raportti?.name?.sv,
                                                        raportti?.kysymysryhmaid,
                                                    )
                                                }
                                            >
                                                {t('esikatselu-otsikko', {
                                                    ns: 'arviointitulokset',
                                                })}
                                            </button>
                                        </Grid>
                                    </Grid>
                                </div>
                            </div>
                        ))}
                </div>
            )}

            {raportit && (
                <div>
                    <h3>{t('rakennetekijat')}</h3>
                    {raportit
                        .filter((raportti2) => raportti2?.laatutekija === 'rakenne')
                        .map((raportti) => (
                            <div>
                                <div>
                                    <Grid
                                        container
                                        item
                                        className={styles['grid-row']}
                                        size={12}
                                    >
                                        <Grid
                                            item
                                            style={{alignContent: 'center'}}
                                            size={6}
                                        >
                                            {langKey === 'fi'
                                                ? raportti?.name?.fi
                                                : raportti?.name?.sv}
                                        </Grid>
                                        <Grid item size={1.5}>
                                            <button disabled={true}>
                                                {t('aineisto')}
                                            </button>
                                        </Grid>
                                        <Grid item size={1.5}>
                                            <button disabled={true}>
                                                {t('raportti')}
                                            </button>
                                        </Grid>
                                        <Grid item size={1.5}>
                                            <button
                                                disabled={!raportti?.show_summary}
                                                onClick={() =>
                                                    handleYhteenvetoClick(
                                                        langKey === 'fi'
                                                            ? raportti?.name?.fi
                                                            : raportti?.name?.sv,
                                                        raportti?.kysymysryhmaid,
                                                    )
                                                }
                                            >
                                                {t('yhteenvedot')}
                                            </button>
                                        </Grid>
                                        <Grid item size={1.5}>
                                            <button
                                                disabled={!raportti?.show_result}
                                                onClick={() =>
                                                    handleArviointituloksetClick(
                                                        langKey === 'fi'
                                                            ? raportti?.name?.fi
                                                            : raportti?.name?.sv,
                                                        raportti?.kysymysryhmaid,
                                                    )
                                                }
                                            >
                                                {t('esikatselu-otsikko', {
                                                    ns: 'arviointitulokset',
                                                })}
                                            </button>
                                        </Grid>
                                    </Grid>
                                </div>
                            </div>
                        ))}
                </div>
            )}

            {raportit && (
                <div>
                    <h3>{t('th-kansalliset-kyselyt', {ns: 'arvtyok'})}</h3>
                    {raportit
                        .filter((raportti2) => raportti2?.laatutekija === 'kansallinen')
                        .map((raportti) => (
                            <div>
                                <div>
                                    <Grid
                                        container
                                        item
                                        className={styles['grid-row']}
                                        size={12}
                                    >
                                        <Grid
                                            item
                                            style={{alignContent: 'center'}}
                                            size={6}
                                        >
                                            {langKey === 'fi'
                                                ? raportti?.name?.fi
                                                : raportti?.name?.sv}
                                        </Grid>
                                        <Grid item size={1.5}>
                                            <button disabled={true}>
                                                {t('aineisto')}
                                            </button>
                                        </Grid>
                                        <Grid item size={1.5}>
                                            <button disabled={true}>
                                                {t('raportti')}
                                            </button>
                                        </Grid>
                                        <Grid item size={1.5}>
                                            <button
                                                disabled={!raportti?.show_summary}
                                                onClick={() =>
                                                    handleYhteenvetoClick(
                                                        langKey === 'fi'
                                                            ? raportti?.name?.fi
                                                            : raportti?.name?.sv,
                                                        raportti?.kysymysryhmaid,
                                                    )
                                                }
                                            >
                                                {t('yhteenvedot')}
                                            </button>
                                        </Grid>
                                        <Grid item size={1.5}>
                                            <button
                                                disabled={!raportti?.show_result}
                                                onClick={() =>
                                                    handleArviointituloksetClick(
                                                        langKey === 'fi'
                                                            ? raportti?.name?.fi
                                                            : raportti?.name?.sv,
                                                        raportti?.kysymysryhmaid,
                                                    )
                                                }
                                            >
                                                {t('esikatselu-otsikko', {
                                                    ns: 'arviointitulokset',
                                                })}
                                            </button>
                                        </Grid>
                                    </Grid>
                                </div>
                            </div>
                        ))}
                </div>
            )}
        </div>
    );
}

export default YllapitajaList;
