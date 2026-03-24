import {useContext, useEffect, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {useObservableState} from 'observable-hooks';
import {forkJoin, of} from 'rxjs';
import {
    arvoGetAllKyselyt$,
    arvoGetKysymysRyhmat$,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import {
    IndikaattoriGroupType,
    virkailijapalveluGetKansallisetIndikaattorit$,
    virkailijapalveluGetProsessitekijaIndikaattorit$,
    virkailijapalveluGetRakennetekijaIndikaattorit$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {KyselyType} from '@cscfi/shared/services/Data/Data-service';
import UserContext from '../../Context';
import IndikaattoriRyhma from './IndikaattoriRyhma/IndikaattoriRyhma';
import FocusableHeader from '../../components/FocusableHeader/FocusableHeader';
import styles from './Indikaattorit.module.css';

function Indikaattorit() {
    const {t} = useTranslation(['arvtyok']);
    const userInfo = useContext(UserContext);
    const currentUserRole = userInfo?.rooli.kayttooikeus;
    const [arvoKyselyt] = useObservableState(
        () =>
            currentUserRole === ArvoRoles.PAAKAYTTAJA ||
            currentUserRole === ArvoRoles.TOTEUTTAJA
                ? arvoGetAllKyselyt$()
                : of([]),
        [],
    );

    const [
        [
            kyselyt,
            prosessitekijaIndikaattorit,
            rakennetekijaIndikaattorit,
            kansallisetIndikaattorit,
        ],
        setKyselyData,
    ] = useState<
        [
            KyselyType[],
            IndikaattoriGroupType[],
            IndikaattoriGroupType[],
            IndikaattoriGroupType[],
        ]
    >([[], [], [], []]);

    useEffect(() => {
        const kyselyQueries = forkJoin([
            arvoGetKysymysRyhmat$,
            virkailijapalveluGetProsessitekijaIndikaattorit$(userInfo!)(),
            virkailijapalveluGetRakennetekijaIndikaattorit$(userInfo!)(),
            virkailijapalveluGetKansallisetIndikaattorit$(userInfo!)(),
        ]);

        kyselyQueries.subscribe(
            ([kysymysryhmat, prosIndk, rakIndk, kansIndk]: [
                kysymysryhmat: KyselyType[],
                prosIndk: IndikaattoriGroupType[],
                rakIndk: IndikaattoriGroupType[],
                kansIndk: IndikaattoriGroupType[],
            ]) => {
                setKyselyData([kysymysryhmat, prosIndk, rakIndk, kansIndk]);
            },
        );
    }, [userInfo]);

    return (
        <>
            <FocusableHeader>
                <>{t('sivun-otsikko')}</>
            </FocusableHeader>

            <table className={styles.indikaattorit}>
                <thead>
                    <tr>
                        <th className={styles.indikaattoriryhma}>
                            {t('th-prosessitekijat')}
                        </th>
                        <th className={styles.tyokalut}>{t('th-arviointityokalut')}</th>
                    </tr>
                </thead>
                <tbody>
                    {prosessitekijaIndikaattorit.map((indikaattoriRyhma) => (
                        <IndikaattoriRyhma
                            item={indikaattoriRyhma}
                            key={indikaattoriRyhma.group_id}
                            kyselyt={kyselyt}
                            currentUserRole={currentUserRole!}
                            arvoKyselyt={arvoKyselyt}
                        />
                    ))}
                </tbody>
                <thead>
                    <tr>
                        <th className={styles.indikaattoriryhma}>
                            {t('th-rakennetekijat')}
                        </th>
                        <th className={styles.tyokalut}>{t('th-arviointityokalut')}</th>
                    </tr>
                </thead>
                <tbody>
                    {rakennetekijaIndikaattorit.map((indikaattoriRyhma) => (
                        <IndikaattoriRyhma
                            item={indikaattoriRyhma}
                            key={indikaattoriRyhma.group_id}
                            kyselyt={kyselyt}
                            currentUserRole={currentUserRole!}
                            arvoKyselyt={arvoKyselyt}
                        />
                    ))}
                </tbody>
                <thead>
                    <tr>
                        <th className={styles.indikaattoriryhma}>
                            {t('th-kansalliset-kyselyt')}
                        </th>
                        <th className={styles.tyokalut}>{t('th-arviointityokalut')}</th>
                    </tr>
                </thead>
                <tbody>
                    {kansallisetIndikaattorit.map((indikaattoriRyhma) => (
                        <IndikaattoriRyhma
                            item={indikaattoriRyhma}
                            key={indikaattoriRyhma.group_id}
                            kyselyt={kyselyt}
                            currentUserRole={currentUserRole!}
                            arvoKyselyt={arvoKyselyt}
                            emptyText
                        />
                    ))}
                </tbody>
            </table>
        </>
    );
}

export default Indikaattorit;
