import {useContext, useEffect, useMemo, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {
    arvoGetAllKyselyt$,
    arvoGetKysymysRyhmat$,
    arvoGetOppilaitos$,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {useObservableState} from 'observable-hooks';
import {mergeMap, forkJoin, from} from 'rxjs';
import {concatMap, filter, map, toArray} from 'rxjs/operators';
import {isBefore, isSameDay, parseISO} from 'date-fns';
import {kyselyNameGenerator, notEmpty, uniqueNumber} from '@cscfi/shared/utils/helpers';
import {virkailijapalveluPostMultiKyselykerta$} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import LomakeTyyppi, {paakayttajaLomakkeet} from '@cscfi/shared/utils/LomakeTyypit';
import {
    Laatutekija,
    raportiointipalveluGetRaportit$,
    RaportitKyselykertaType,
    raportointipalveluPostSetSkipped$,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import UserContext from '../../../Context';
import KyselyLink from './KyselyLink';
import ToimipaikatList, {
    ExtendedArvoKysely,
    ExtendedKyselyType,
    KyselyRequestType,
} from './ToimipaikatList';
import styles from './EtusivuKyselytList.module.css';
import ToimipaikkaLink from './ToimipaikkaLink';

type ExtendedRaportitKyselykertaType = RaportitKyselykertaType & {
    oppilaitosName?: TextType;
};

type KyselykertaInfoType = {
    name: TextType;
    kyselykertas: ExtendedRaportitKyselykertaType[];
};

function EtusivuKyselytList() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['etusivu', 'raportointi']);

    const [renderList, setRenderList] = useState<ExtendedKyselyType[]>([]);
    const [showConfirmationDialog, setShowConfirmationDialog] = useState(false);
    const userInfo = useContext(UserContext);
    const userOppilaitokset: string[] = userInfo
        ? userInfo.rooli.oppilaitokset.map((opp) => opp.oppilaitos_oid)
        : [];

    const [kysymysryhmaList, setKysymysryhmaList] = useState<KyselyType[]>([]);

    function updateOhitaKysely(
        kyselyid: number,
        name: string,
        mainDivId: string,
        listId: string,
    ) {
        const element = document.getElementById(name);
        if (element) {
            element.style.display = 'none';
        }
        const mainDivElement = document.getElementById(mainDivId);
        if (mainDivElement) {
            let numberOfVisibleSubDivElements = 0;
            const subDivCollection = mainDivElement.getElementsByTagName('div');
            if (subDivCollection.length === 0) {
                numberOfVisibleSubDivElements = 0;
            } else {
                for (const subDiv of subDivCollection) {
                    if (
                        subDiv &&
                        subDiv.style.display != 'none' &&
                        subDiv.classList.contains('divIdClass')
                    ) {
                        numberOfVisibleSubDivElements = numberOfVisibleSubDivElements + 1;
                    }
                }
            }
            if (numberOfVisibleSubDivElements === 0) {
                const listElement = document.getElementById(listId);
                if (listElement) {
                    listElement.style.display = 'none';
                }
            }
        }
        raportointipalveluPostSetSkipped$(userInfo!)(kyselyid).subscribe((value) => {
            if (value === 'OK') {
                // do nothing
            } else {
                console.log('updateOhitaKysely returned an error: ' + value);
                const alert = {
                    bodyPlain:
                        t('taustajarjestelma-error-body', {ns: 'alert'}) + ' ' + value,
                    severity: 'error',
                    title: {key: 'taustajarjestelma-error-title', ns: 'alert'},
                    sticky: true,
                    disabled: false,
                } as AlertType;
                AlertService.showAlert(alert);
            }
        });
    }
    const [toteuttajanKyselyt] = useObservableState(
        () =>
            forkJoin([
                arvoGetKysymysRyhmat$,
                arvoGetAllKyselyt$(),
                arvoGetOppilaitos$(),
            ]).pipe(
                concatMap(([kysymysryhmat, kyselyt, oppilaitokset]) => {
                    setKysymysryhmaList(kysymysryhmat);
                    return from(kysymysryhmat).pipe(
                        map((kysymysryhma) => {
                            /**
                             * match kysymysryhma to kysely
                             * filter ongoing questionnaires
                             * (covers case of impersonation filter oppilaitokset where user has permissions)
                             */
                            const filteredKyselyt = kyselyt.filter((kysely) => {
                                const alku = parseISO(kysely.voimassa_alkupvm);
                                const loppu = parseISO(kysely.voimassa_loppupvm);
                                const nyt = new Date();

                                return (
                                    kysymysryhma.id ===
                                        kysely.metatiedot.valssi_kysymysryhma &&
                                    (isSameDay(alku, nyt) || isBefore(alku, nyt)) &&
                                    (isSameDay(nyt, loppu) || isBefore(nyt, loppu)) &&
                                    userOppilaitokset.includes(kysely.oppilaitos)
                                );
                            });

                            const extendedKyselyt: ExtendedArvoKysely[] =
                                filteredKyselyt.map((kysely) => {
                                    const oppilaitos = oppilaitokset.find(
                                        (opp) => opp.oid === kysely.oppilaitos,
                                    );
                                    return {
                                        ...kysely,
                                        ...(oppilaitos && {
                                            oppilaitos_nimi: {
                                                fi: oppilaitos.nimi_fi || '-',
                                                sv: oppilaitos.nimi_sv || '-',
                                            },
                                        }),
                                    };
                                });

                            return {
                                kysymysryhma,
                                kyselyt: extendedKyselyt,
                            };
                        }),
                    );
                }),
                filter(({kyselyt}) => kyselyt.length > 0),
                filter(
                    ({kysymysryhma}) =>
                        !paakayttajaLomakkeet.includes(
                            kysymysryhma.lomaketyyppi as LomakeTyyppi,
                        ),
                ),
                map(({kysymysryhma, kyselyt}) => {
                    const kyselytFirst = kyselyt.find((k) => !!k);
                    const topic = kyselyNameGenerator(
                        kysymysryhma,
                        kyselytFirst && parseISO(kyselytFirst.voimassa_alkupvm),
                        null,
                        null,
                    );
                    return {
                        ...kysymysryhma,
                        topic,
                        kyselyt,
                    } as ExtendedKyselyType;
                }),
                toArray(),
            ),
        [],
    );

    const [toteuttajanTulevatKyselyt] = useObservableState(
        () =>
            forkJoin([
                arvoGetKysymysRyhmat$,
                arvoGetAllKyselyt$(),
                arvoGetOppilaitos$(),
            ]).pipe(
                concatMap(([kysymysryhmat, kyselyt, oppilaitokset]) => {
                    setKysymysryhmaList(kysymysryhmat);
                    return from(kysymysryhmat).pipe(
                        map((kysymysryhma) => {
                            /**
                             * match kysymysryhma to kysely
                             * filter ongoing questionnaires
                             * (covers case of impersonation filter oppilaitokset where user has permissions)
                             */
                            const filteredKyselyt = kyselyt.filter((kysely) => {
                                const alku = parseISO(kysely.voimassa_alkupvm);
                                const loppu = parseISO(kysely.voimassa_loppupvm);
                                const nyt = new Date();

                                return (
                                    kysymysryhma.id ===
                                        kysely.metatiedot.valssi_kysymysryhma &&
                                    isBefore(nyt, alku) &&
                                    isBefore(nyt, loppu) &&
                                    userOppilaitokset.includes(kysely.oppilaitos)
                                );
                            });

                            const extendedKyselyt: ExtendedArvoKysely[] =
                                filteredKyselyt.map((kysely) => {
                                    const oppilaitos = oppilaitokset.find(
                                        (opp) => opp.oid === kysely.oppilaitos,
                                    );
                                    return {
                                        ...kysely,
                                        ...(oppilaitos && {
                                            oppilaitos_nimi: {
                                                fi: oppilaitos.nimi_fi || '-',
                                                sv: oppilaitos.nimi_sv || '-',
                                            },
                                        }),
                                    };
                                });

                            return {
                                kysymysryhma,
                                kyselyt: extendedKyselyt,
                            };
                        }),
                    );
                }),
                filter(({kyselyt}) => kyselyt.length > 0),
                filter(
                    ({kysymysryhma}) =>
                        !paakayttajaLomakkeet.includes(
                            kysymysryhma.lomaketyyppi as LomakeTyyppi,
                        ),
                ),
                map(({kysymysryhma, kyselyt}) => {
                    const kyselytFirst = kyselyt.find((k) => !!k);
                    const topic = kyselyNameGenerator(
                        kysymysryhma,
                        kyselytFirst && parseISO(kyselytFirst.voimassa_alkupvm),
                        null,
                        null,
                    );
                    return {
                        ...kysymysryhma,
                        topic,
                        kyselyt,
                    } as ExtendedKyselyType;
                }),
                toArray(),
            ),
        [],
    );

    const sortedKyselyt = useMemo(
        () =>
            toteuttajanKyselyt.sort((kra, krb) =>
                parseISO(kra.kyselyt.find((k) => !!k)!.voimassa_alkupvm) >
                parseISO(krb.kyselyt.find((k) => !!k)!.voimassa_alkupvm)
                    ? -1
                    : 1,
            ),
        [toteuttajanKyselyt],
    );

    const sortedTulevatKyselyt = useMemo(
        () =>
            toteuttajanTulevatKyselyt.sort((kra, krb) =>
                parseISO(kra.kyselyt.find((k) => !!k)!.voimassa_alkupvm) <
                parseISO(krb.kyselyt.find((k) => !!k)!.voimassa_alkupvm)
                    ? -1
                    : 1,
            ),
        [toteuttajanTulevatKyselyt],
    );

    useEffect(() => {
        const postMultiKyselykerta = (body: any) =>
            virkailijapalveluPostMultiKyselykerta$(userInfo!)(body);
        const onkoLahetetty: KyselyRequestType[] = sortedKyselyt.map((sk) => ({
            kysymysryhmaid: sk.id,
            organisaatio: sk.kyselyt[0].oppilaitos,
        }));
        if (onkoLahetetty.length > 0) {
            postMultiKyselykerta(onkoLahetetty).subscribe((isSent) => {
                const enrichedKyselyt = sortedKyselyt
                    .map((sk) => {
                        const isSentData = isSent?.find(
                            (sentObj: any) => sentObj.kysymysryhmaid === sk.id,
                        );
                        return isSentData
                            ? {
                                  ...sk,
                                  kyselykertaid: isSentData.kyselykertaid,
                                  lastKyselysend: isSentData.last_kyselysend,
                                  voimassaLoppupvm: new Date(
                                      isSentData.voimassa_loppupvm,
                                  ),
                              }
                            : null;
                    })
                    .filter(notEmpty);
                setRenderList(enrichedKyselyt);
            });
        }
    }, [sortedKyselyt, userInfo]);

    const [puuttuvatYhteenvedot] = useObservableState(
        () =>
            forkJoin([
                raportiointipalveluGetRaportit$(userInfo!)(
                    userInfo!.rooli.organisaatio,
                    userInfo!.rooli.kayttooikeus,
                ),
                arvoGetAllKyselyt$(),
                arvoGetOppilaitos$(),
            ]).pipe(
                concatMap(([raportit, kyselyt, oppilaitokset]) =>
                    from(raportit).pipe(
                        filter(
                            (raportti) =>
                                !(
                                    raportti.is_paakayttaja_lomake ||
                                    raportti.kyselykertas.length === 0 ||
                                    raportti.available_kyselykertas.length === 0 ||
                                    raportti.laatutekija === Laatutekija.kansallinen
                                ),
                        ),
                        mergeMap((raportti) =>
                            raportti.available_kyselykertas
                                .filter((akk) => !akk.show_result)
                                .map((akk) => {
                                    const tempKk: KyselykertaInfoType = {
                                        name: {fi: akk.nimi_fi, sv: akk.nimi_sv},
                                        kyselykertas: raportti.kyselykertas.filter(
                                            (kk) =>
                                                kk.voimassa_alkupvm ===
                                                akk.kyselykerta_alkupvm,
                                        ),
                                    };
                                    tempKk.kyselykertas = tempKk.kyselykertas
                                        .filter((kk) => !kk.show_summary)
                                        .map((kk) => {
                                            const tempKysely = kyselyt.find(
                                                (kysely) =>
                                                    kysely.kyselyid ===
                                                    kk.kysely.kyselyid,
                                            );
                                            const tempOppilaitos = oppilaitokset.find(
                                                (ol) => ol.oid === tempKysely?.oppilaitos,
                                            );
                                            return {
                                                ...kk,
                                                oppilaitosName: {
                                                    fi: tempOppilaitos?.nimi_fi || '-',
                                                    sv: tempOppilaitos?.nimi_sv || '-',
                                                },
                                            };
                                        });
                                    return tempKk;
                                })
                                .filter((r) => r.kyselykertas.length > 0),
                        ),
                    ),
                ),
                toArray(),
            ),
        [],
    );

    const sortedPuuttuvatYhteenvedot = useMemo(
        () =>
            puuttuvatYhteenvedot.sort((a, b) =>
                a.kyselykertas[0].kysely.voimassa_alkupvm >
                b.kyselykertas[0].kysely.voimassa_alkupvm
                    ? -1
                    : 1,
            ),
        [puuttuvatYhteenvedot],
    );

    return (
        <>
            <h2>{t('toteuttaja_kyselyt_myos_tulevat')}</h2>

            {renderList?.length > 0 ? (
                <ul className={styles['kysely-list']}>
                    {renderList.map((tempKysymysryhma) => (
                        <li
                            className={`${styles.kysely} ${styles.toteuttaja}`}
                            key={tempKysymysryhma.id}
                        >
                            <KyselyLink
                                kysely={tempKysymysryhma}
                                key={`${tempKysymysryhma.id}_${uniqueNumber()}`}
                            />
                            {(tempKysymysryhma?.kyselyt?.length || 0) > 0 && (
                                <ToimipaikatList kysymysryhma={tempKysymysryhma} />
                            )}
                        </li>
                    ))}
                </ul>
            ) : (
                <></>
            )}
            {sortedTulevatKyselyt?.length > 0 ? (
                <ul className={styles['kysely-list']}>
                    {sortedTulevatKyselyt.map((tempKysymysryhma) => (
                        <li
                            className={`${styles.kysely} ${styles.toteuttaja}`}
                            key={tempKysymysryhma.id}
                        >
                            <KyselyLink
                                kysely={tempKysymysryhma}
                                key={`${tempKysymysryhma.id}_${uniqueNumber()}`}
                            />
                            {(tempKysymysryhma?.kyselyt?.length || 0) > 0 && (
                                <ToimipaikatList
                                    kysymysryhma={tempKysymysryhma}
                                    futureData={true}
                                />
                            )}
                        </li>
                    ))}
                </ul>
            ) : (
                <></>
            )}
            {renderList?.length === 0 && sortedTulevatKyselyt?.length === 0 ? (
                <p>{t('toteuttaja_ei_kyselyita')}</p>
            ) : (
                <></>
            )}

            {sortedPuuttuvatYhteenvedot && sortedPuuttuvatYhteenvedot.length > 0 && (
                <>
                    <h2>{t('toteuttaja_paattyneet_kyselyt')}</h2>
                    <ul className={styles['kysely-list']}>
                        {puuttuvatYhteenvedot.map((py) => {
                            const kysymysryhma = kysymysryhmaList.find(
                                (kr) =>
                                    kr.id ===
                                    py.kyselykertas[0].kysely.metatiedot
                                        .valssi_kysymysryhma,
                            );
                            const krtopic =
                                kysymysryhma &&
                                kyselyNameGenerator(
                                    kysymysryhma,
                                    py.kyselykertas[0].kysely &&
                                        parseISO(
                                            py.kyselykertas[0].kysely.voimassa_alkupvm,
                                        ),
                                    null,
                                    null,
                                );
                            return kysymysryhma && krtopic ? (
                                <>
                                    <li
                                        className={`${styles.kysely} ${styles.toteuttaja}`}
                                        key={py.name[lang as keyof TextType]}
                                        id={'list_id_' + py.name[lang as keyof TextType]}
                                    >
                                        <KyselyLink
                                            kysely={{...kysymysryhma, topic: krtopic}}
                                            key={`${kysymysryhma.id}_${uniqueNumber()}`}
                                        />
                                        <div
                                            id={
                                                py.name[lang as keyof TextType] +
                                                py.id +
                                                '_main'
                                            }
                                            className={styles['kysely-toimipaikka-list']}
                                        >
                                            {py?.kyselykertas.map((kk) => (
                                                <div
                                                    id={
                                                        py.name[lang as keyof TextType] +
                                                        kk.kysely.kyselyid
                                                    }
                                                    style={{
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                    }}
                                                    className={'divIdClass'}
                                                >
                                                    <ToimipaikkaLink
                                                        toimipaikkaNimi={
                                                            kk.oppilaitosName?.[
                                                                lang as keyof TextType
                                                            ] || '-'
                                                        }
                                                        linkText={t('tayta-yhteenveto', {
                                                            ns: 'raportointi',
                                                        })}
                                                        linkTo={`/yhteenveto?id=${kk.kysely.kyselyid}`}
                                                    />
                                                    <ConfirmationDialog
                                                        title={t(
                                                            'ohita-yhteenveto-kysymys',
                                                            {ns: 'raportointi'},
                                                        )}
                                                        content={t(
                                                            'ohita-yhteenveto-sisalto',
                                                            {ns: 'raportointi'},
                                                        )}
                                                        confirmBtnText={t(
                                                            'ohita-yhteenveto',
                                                            {ns: 'raportointi'},
                                                        )}
                                                        cancelBtnText={t(
                                                            'painike-peruuta',
                                                            {ns: 'yleiset'},
                                                        )}
                                                        confirm={() => {
                                                            updateOhitaKysely(
                                                                kk.kysely.kyselyid,
                                                                py.name[
                                                                    lang as keyof TextType
                                                                ] + kk.kysely.kyselyid,
                                                                py.name[
                                                                    lang as keyof TextType
                                                                ] +
                                                                    py.id +
                                                                    '_main',
                                                                'list_id_' +
                                                                    py.name[
                                                                        lang as keyof TextType
                                                                    ],
                                                            );
                                                            setShowConfirmationDialog(
                                                                false,
                                                            );
                                                        }}
                                                        cancel={() =>
                                                            setShowConfirmationDialog(
                                                                false,
                                                            )
                                                        }
                                                        showDialogBoolean={
                                                            showConfirmationDialog
                                                        }
                                                    >
                                                        <button
                                                            className="small secondary"
                                                            onClick={() => {
                                                                setShowConfirmationDialog(
                                                                    true,
                                                                );
                                                            }}
                                                        >
                                                            {t('ohita-yhteenveto', {
                                                                ns: 'raportointi',
                                                            })}
                                                        </button>
                                                    </ConfirmationDialog>
                                                </div>
                                            ))}
                                        </div>
                                    </li>
                                    <br />
                                </>
                            ) : null;
                        })}
                    </ul>
                </>
            )}
        </>
    );
}

export default EtusivuKyselytList;
