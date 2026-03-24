import {useTranslation} from 'react-i18next';
import {useMemo} from 'react';
import {KyselyCollectionType} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {uniqueNumber} from '@cscfi/shared/utils/helpers';
import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import FocusableHeader from '../../components/FocusableHeader/FocusableHeader';
import GuardedComponentWrapper from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import styles from './Tiedonkeruu.module.css';
import TiedonkeruuKysely from './TiedonkeruuKysely';

interface KyselyTableProps {
    kyselyt: KyselyCollectionType[] | null;
}
function KyselyList({kyselyt}: KyselyTableProps) {
    const {t} = useTranslation(['tiedonkeruun-seuranta']);

    const kaynnissaOlevetKyselyt = useMemo(
        () => kyselyt?.filter((k) => !k.is_closed) ?? [],
        [kyselyt],
    );
    const sulkeutuneetKyselyt = useMemo(
        () => kyselyt?.filter((k) => k.is_closed) ?? [],
        [kyselyt],
    );

    return (
        <div>
            <FocusableHeader>
                <>{t('tiedonkeruun-seuranta', {ns: 'ulkoasu'})}</>
            </FocusableHeader>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.TOTEUTTAJA]}}>
                <h2 className={styles['kyselyt-heading']}>
                    {t('kaynnissa-olevat-kyselyt')}
                </h2>
            </GuardedComponentWrapper>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.PAAKAYTTAJA]}}>
                <h2 className={styles['kyselyt-heading']}>
                    {t('kayttoon-otetut-kyselyt')}
                </h2>
            </GuardedComponentWrapper>
            {kaynnissaOlevetKyselyt?.map((kysely) => (
                <TiedonkeruuKysely
                    key={`activeKysely_${kysely.kysymysryhmaid || uniqueNumber()}_${
                        kysely.voimassa_alkupvm
                    }`}
                    kysely={kysely}
                />
            ))}
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.TOTEUTTAJA]}}>
                <h2 className={styles['kyselyt-heading']}>{t('sulkeutuneet-kyselyt')}</h2>
            </GuardedComponentWrapper>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.PAAKAYTTAJA]}}>
                <h2 className={styles['kyselyt-heading']}>
                    {t('viimeisimmat-sulkeutuneet-kyselyt')}
                </h2>
            </GuardedComponentWrapper>
            {sulkeutuneetKyselyt?.map((kysely) => (
                <TiedonkeruuKysely
                    key={`closedKysely_${kysely.kysymysryhmaid || uniqueNumber()}_${
                        kysely.voimassa_alkupvm
                    }`}
                    kysely={kysely}
                />
            ))}
        </div>
    );
}
export default KyselyList;
