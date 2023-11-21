import {useContext, useEffect, useMemo, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {
    arvoGetAllKyselyt$,
    arvoGetKysymysRyhmat$,
    arvoGetOppilaitos$,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {useObservable} from 'rxjs-hooks';
import {forkJoin, from} from 'rxjs';
import {concatMap, filter, map, toArray} from 'rxjs/operators';
import {isBefore, isSameDay, parseISO} from 'date-fns';
import {kyselyNameGenerator, notEmpty} from '@cscfi/shared/utils/helpers';
// eslint-disable-next-line max-len
import {virkailijapalveluPostMultiKyselykerta$} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import UserContext from '../../../Context';
import LomakeTyyppi, {paakayttajaLomakkeet} from '../../../utils/LomakeTyypit';
import KyselyLink from './KyselyLink';
import ToimipaikatList, {
    ExtendedArvoKysely,
    ExtendedKyselyType,
    KyselyRequestType,
} from './ToimipaikatList';
import styles from './EtusivuKyselytList.module.css';

function EtusivuKyselytList() {
    const {t} = useTranslation(['etusivu']);
    const [renderList, setRenderList] = useState<ExtendedKyselyType[]>([]);
    const userInfo = useContext(UserContext);
    const userOppilaitokset: string[] = userInfo
        ? userInfo.rooli.oppilaitokset.map((opp) => opp.oppilaitos_oid)
        : [];

    const toteuttajanKyselyt = useObservable(
        () =>
            forkJoin([
                arvoGetKysymysRyhmat$,
                arvoGetAllKyselyt$(),
                arvoGetOppilaitos$(),
            ]).pipe(
                concatMap(([kysymysryhmat, kyselyt, oppilaitokset]) =>
                    from(kysymysryhmat).pipe(
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
                    ),
                ),
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
    return (
        <>
            <h2>{t('toteuttaja_kyselyt')}</h2>
            {renderList?.length > 0 ? (
                <ul className={styles['kysely-list']}>
                    {renderList.map((tempKysymysryhma: any) => (
                        <li
                            className={`${styles.kysely} ${styles.toteuttaja}`}
                            key={tempKysymysryhma.id}
                        >
                            <KyselyLink
                                kysely={tempKysymysryhma}
                                key={tempKysymysryhma.id}
                            />
                            {(tempKysymysryhma?.kyselyt?.length || 0) > 0 && (
                                <ToimipaikatList kysymysryhma={tempKysymysryhma} />
                            )}
                        </li>
                    ))}
                </ul>
            ) : (
                <p>{t('toteuttaja_ei_kyselyita')}</p>
            )}
        </>
    );
}

export default EtusivuKyselytList;
