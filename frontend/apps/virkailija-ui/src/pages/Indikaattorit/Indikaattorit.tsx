import {useContext} from 'react';
import {useTranslation} from 'react-i18next';
import {useObservable} from 'rxjs-hooks';
import {of} from 'rxjs';
import {
    arvoGetAllKyselyt$,
    arvoGetKysymysRyhmat$,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {
    virkailijapalveluGetProsessitekijaIndikaattorit$,
    virkailijapalveluGetRakennetekijaIndikaattorit$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import UserContext from '../../Context';
import {ValssiUserLevel} from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import IndikaattoriRyhma from './IndikaattoriRyhma/IndikaattoriRyhma';
import styles from './Indikaattorit.module.css';

function Indikaattorit() {
    const {t} = useTranslation(['arvtyok']);
    const userInfo = useContext(UserContext);
    const currentUserRole = userInfo?.rooli.kayttooikeus;
    const arvoKyselyt = useObservable(
        () =>
            currentUserRole === ValssiUserLevel.PAAKAYTTAJA ||
            currentUserRole === ValssiUserLevel.TOTEUTTAJA
                ? arvoGetAllKyselyt$()
                : of([]),
        [],
    );
    const kyselyt = useObservable(() => arvoGetKysymysRyhmat$, []);
    const prosessitekijaIndikaattorit = useObservable(
        virkailijapalveluGetProsessitekijaIndikaattorit$(userInfo!),
        [],
    );
    const rakennetekijaIndikaattorit = useObservable(
        virkailijapalveluGetRakennetekijaIndikaattorit$(userInfo!),
        [],
    );

    return (
        <>
            <h1>{t('sivun-otsikko')}</h1>

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
                    {/* -------------------------------------------------------------------------------------------- */}
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
            </table>
        </>
    );
}

export default Indikaattorit;
