import {useTranslation} from 'react-i18next';
import {arvoGetKysymysRyhmat$} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';

import {KyselyType, StatusType} from '@cscfi/shared/services/Data/Data-service';
import {useObservable} from 'rxjs-hooks';
import {concatMap, filter, map} from 'rxjs/operators';
import {from, take, reduce, groupBy, mergeMap} from 'rxjs';
import styles from './EtusivuKyselytList.module.css';
import KyselyLink from './KyselyLink';

const uusimmat = (a: KyselyType, b: KyselyType) => {
    if (a.muutettuaika !== undefined && b.muutettuaika !== undefined) {
        return Date.parse(b.muutettuaika) - Date.parse(a.muutettuaika);
    }
    return 0; // we can assume that muutettuaika has always value
};

class JulkaistuLuonnos {
    [StatusType.julkaistu]: KyselyType[] = [];

    [StatusType.luonnos]: KyselyType[] = [];
}

function EtusivuKyselytList() {
    const {t} = useTranslation(['etusivu']);
    const allKyselyt = useObservable(
        () =>
            arvoGetKysymysRyhmat$.pipe(
                map((kyselyt) => kyselyt.sort(uusimmat)),
                concatMap((kyselyt) => from(kyselyt)),
                filter((kysely) =>
                    [StatusType.luonnos, StatusType.julkaistu].includes(kysely.status),
                ),
                groupBy((kysely) => kysely.status),
                mergeMap((kyselyGroup$) => kyselyGroup$.pipe(take(5))),
                reduce((acc, kysely) => {
                    const kyselytByStatus = acc[kysely.status as keyof JulkaistuLuonnos];
                    return {
                        ...acc,
                        [kysely.status]: [...kyselytByStatus, kysely],
                    };
                }, new JulkaistuLuonnos()),
            ),
        new JulkaistuLuonnos(),
    );
    return (
        <>
            <h2>{t('yllapitaja_luonnokset')}</h2>
            {allKyselyt.luonnos.length > 0 ? (
                <ul className={styles['kysely-list']}>
                    {allKyselyt.luonnos.map((kysely) => (
                        <li className={styles.kysely} key={kysely.id}>
                            <KyselyLink kysely={kysely} key={kysely.id} />
                        </li>
                    ))}
                </ul>
            ) : (
                <p>{t('ei_kyselyita')}</p>
            )}
            <h2>{t('yllapitaja_julkaistut')}</h2>
            {allKyselyt.julkaistu.length > 0 ? (
                <ul className={styles['kysely-list']}>
                    {allKyselyt.julkaistu.map((kysely) => (
                        <li className={styles.kysely} key={kysely.id}>
                            <KyselyLink kysely={kysely} key={kysely.id} />
                        </li>
                    ))}
                </ul>
            ) : (
                <p>{t('ei_julkaistuja_kyselyita')}</p>
            )}
        </>
    );
}

export default EtusivuKyselytList;
