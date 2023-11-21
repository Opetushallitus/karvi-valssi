import {useObservable} from 'rxjs-hooks';
import {useTranslation} from 'react-i18next';
import {
    arvoGetAllKyselyt$,
    arvoGetKysymysRyhmat$,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {forkJoin, from, concatMap, map, reduce, filter} from 'rxjs';
import {isBefore, isSameDay, parseISO} from 'date-fns';
import {useContext, useMemo} from 'react';
import {kyselyNameGenerator} from '@cscfi/shared/utils/helpers';
import LomakeTyyppi, {paakayttajaLomakkeet} from '../../../utils/LomakeTyypit';
import KyselyLink from './KyselyLink';
import styles from './EtusivuKyselytList.module.css';
import {ExtendedKyselyType} from './ToimipaikatList';
import ButtonWithLink from '../../../components/ButtonWithLink/ButtonWithLink';
import JatkaAikaa from './JatkaAikaa';
import UserContext from '../../../Context';

function EtusivuKyselytList() {
    const {t} = useTranslation(['etusivu']);
    const userInfo = useContext(UserContext);

    const allKyselyt = useObservable(
        () =>
            forkJoin([arvoGetKysymysRyhmat$, arvoGetAllKyselyt$()]).pipe(
                concatMap(([kysymysryhmat, kyselyt]) =>
                    from(kysymysryhmat).pipe(
                        map((kysymysryhma) => {
                            const filteredKyselyt = kyselyt.filter((kysely) => {
                                const loppu = parseISO(kysely.voimassa_loppupvm);
                                const nyt = new Date();

                                return (
                                    kysymysryhma.id ===
                                        kysely.metatiedot.valssi_kysymysryhma &&
                                    (isSameDay(nyt, loppu) || isBefore(nyt, loppu))
                                );
                            });
                            return {
                                kysymysryhma,
                                kyselyt: filteredKyselyt,
                            };
                        }),
                    ),
                ),
                filter(({kyselyt}) => kyselyt.length > 0),
                reduce(
                    (acc, {kysymysryhma, kyselyt}) => {
                        const kyselytFirst = kyselyt.find((k) => !!k);
                        const topic = kyselyNameGenerator(
                            kysymysryhma,
                            kyselytFirst && parseISO(kyselytFirst.voimassa_alkupvm),
                            null,
                            null,
                        );
                        const kyselyType = paakayttajaLomakkeet.includes(
                            kysymysryhma.lomaketyyppi as LomakeTyyppi,
                        )
                            ? 'paakayttaja'
                            : 'toteuttaja';

                        const kyselytByType = acc[kyselyType];
                        return {
                            ...acc,
                            [kyselyType]: [
                                ...kyselytByType,
                                {
                                    ...kysymysryhma,
                                    topic,
                                    kyselyt,
                                },
                            ],
                        };
                    },
                    {toteuttaja: [], paakayttaja: []},
                ),
            ),
        {toteuttaja: [] as ExtendedKyselyType[], paakayttaja: [] as ExtendedKyselyType[]},
    );

    const sortedKyselyt = useMemo(
        () => ({
            toteuttaja: allKyselyt.toteuttaja.sort((kra, krb) =>
                parseISO(kra.kyselyt.find((k) => !!k)!.voimassa_alkupvm) >
                parseISO(krb.kyselyt.find((k) => !!k)!.voimassa_alkupvm)
                    ? -1
                    : 1,
            ),
            paakayttaja: allKyselyt.paakayttaja.sort((kra, krb) =>
                parseISO(kra.kyselyt.find((k) => !!k)!.voimassa_alkupvm) >
                parseISO(krb.kyselyt.find((k) => !!k)!.voimassa_alkupvm)
                    ? -1
                    : 1,
            ),
        }),
        [allKyselyt],
    );

    return (
        <>
            <h2>{t('paakayttaja_kyselyt')}</h2>
            <h3>{t('paakayttaja_toteuttajan_kyselyt')}</h3>
            {sortedKyselyt.toteuttaja.length > 0 ? (
                <ul className={styles['kysely-list']}>
                    {sortedKyselyt.toteuttaja.map((tempKysymysryhma) => (
                        <li className={styles.kysely} key={tempKysymysryhma.id}>
                            <KyselyLink
                                kysely={tempKysymysryhma}
                                key={tempKysymysryhma.id}
                            />
                            <ButtonWithLink
                                linkTo={`/aktivointi?id=${tempKysymysryhma.id}`}
                                linkText={t('painike-aktivointi-lisaa', {
                                    ns: 'esikatselu',
                                })}
                                className="small"
                            />
                            <JatkaAikaa
                                kysely={tempKysymysryhma}
                                koulutustoimija={userInfo?.rooli.organisaatio}
                                startDate={parseISO(
                                    tempKysymysryhma.kyselyt[0].voimassa_alkupvm,
                                )}
                                endDate={parseISO(
                                    tempKysymysryhma.kyselyt[0].voimassa_loppupvm,
                                )}
                            />
                        </li>
                    ))}
                </ul>
            ) : (
                <p>{t('paakayttaja_ei_kyselyita')}</p>
            )}

            <h3>{t('paakayttaja_omat_kyselyt')}</h3>
            {sortedKyselyt.paakayttaja.length > 0 ? (
                <ul className={styles['kysely-list']}>
                    {sortedKyselyt.paakayttaja.map((tempKysymysryhma) => (
                        <li className={styles.kysely} key={tempKysymysryhma.id}>
                            <KyselyLink
                                kysely={tempKysymysryhma}
                                key={tempKysymysryhma.id}
                            />
                            <ButtonWithLink
                                linkTo={`/lahetys?id=${tempKysymysryhma.id}`}
                                linkText={t('painike-lahetys', {ns: 'esikatselu'})}
                                className="small"
                            />
                            <JatkaAikaa
                                kysely={tempKysymysryhma}
                                koulutustoimija={userInfo?.rooli.organisaatio}
                                startDate={parseISO(
                                    tempKysymysryhma.kyselyt[0].voimassa_alkupvm,
                                )}
                                endDate={parseISO(
                                    tempKysymysryhma.kyselyt[0].voimassa_loppupvm,
                                )}
                            />
                        </li>
                    ))}
                </ul>
            ) : (
                <p>{t('paakayttaja_ei_lahetettyja_kyselyita')}</p>
            )}
        </>
    );
}

export default EtusivuKyselytList;
