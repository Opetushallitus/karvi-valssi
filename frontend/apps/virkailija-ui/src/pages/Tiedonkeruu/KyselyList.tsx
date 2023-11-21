import {getI18n, useTranslation} from 'react-i18next';
import {useEffect, useState} from 'react';
import {KyselyCollectionType} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {uniqueNumber} from '@cscfi/shared/utils/helpers';
import AnsweredLessThan50 from './AnsweredLessThan50';
import ButtonWithoutStyles from '../../components/ButtonWithoutStyles/ButtonWithoutStyles';
import GuardedComponentWrapper, {
    ValssiUserLevel,
} from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import LomakeTyyppi, {paakayttajaLomakkeet} from '../../utils/LomakeTyypit';

import Table from './Table';
import styles from './Tiedonkeruu.module.css';

interface KyselyTableProps {
    kyselyt: KyselyCollectionType[] | null;
}
function KyselyList({kyselyt}: KyselyTableProps) {
    const locale = getI18n().language;
    const {t} = useTranslation(['tiedonkeruun-seuranta']);
    const [kaynnissaOlevetKyselyt, setKaynnissaOlevetKyselyt] = useState<
        KyselyCollectionType[] | undefined | null
    >(null);
    const [sulkeutuneetKyselyt, setSulkeutuneetKyselyt] = useState<
        KyselyCollectionType[] | undefined | null
    >(null);
    useEffect(() => {
        const kaynnissaOlevetKyselytVar = kyselyt?.filter((kysely) => !kysely.is_closed);
        const sulkeutuneetKyselytVar = kyselyt?.filter((kysely) => kysely.is_closed);
        setKaynnissaOlevetKyselyt(kaynnissaOlevetKyselytVar?.reverse());
        setSulkeutuneetKyselyt(sulkeutuneetKyselytVar?.reverse());
    }, [kyselyt]);
    const [expanded, setExpanded] = useState<string[]>([]);

    const handleExpandedChange = (panel: string) => {
        if (expanded.includes(panel)) {
            setExpanded(expanded.filter((key) => key !== panel));
        } else {
            setExpanded([...expanded, panel]);
        }
    };

    return (
        <div>
            <h1> {t('tiedonkeruun-seuranta', {ns: 'ulkoasu'})}</h1>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.TOTEUTTAJA]}>
                <h2 className={styles['kyselyt-heading']}>
                    {t('kaynnissa-olevat-kyselyt')}
                </h2>
            </GuardedComponentWrapper>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.PAAKAYTTAJA]}>
                <h2 className={styles['kyselyt-heading']}>
                    {t('kayttoon-otetut-kyselyt')}
                </h2>
            </GuardedComponentWrapper>
            {kaynnissaOlevetKyselyt?.map((kysely) => (
                <div
                    key={`${kysely.kyselyid}_${uniqueNumber()}`}
                    className={styles['kyselyt-wrapper']}
                >
                    <h3>
                        {kysely && (locale === 'fi' ? kysely?.nimi_fi : kysely?.nimi_sv)}
                    </h3>
                    <Table kysely={kysely} />
                    {!paakayttajaLomakkeet.includes(
                        kysely?.lomaketyyppi as LomakeTyyppi,
                    ) && (
                        <GuardedComponentWrapper
                            allowedValssiRoles={[ValssiUserLevel.PAAKAYTTAJA]}
                        >
                            <div className={styles['open-answered-less-than50-wrapper']}>
                                <ButtonWithoutStyles
                                    onClick={() => handleExpandedChange(kysely.nimi_fi!)}
                                >
                                    <span style={{color: '#2f487f'}}>
                                        {t('nayta-toimipaikat')}
                                    </span>
                                </ButtonWithoutStyles>
                            </div>
                            {expanded.includes(kysely.nimi_fi!) && (
                                <AnsweredLessThan50
                                    kysely={kysely}
                                    handleExpandedChange={handleExpandedChange}
                                    kyselyNimi={kysely.nimi_fi!}
                                />
                            )}
                        </GuardedComponentWrapper>
                    )}
                </div>
            ))}
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.TOTEUTTAJA]}>
                <h2 className={styles['kyselyt-heading']}>{t('sulkeutuneet-kyselyt')}</h2>
            </GuardedComponentWrapper>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.PAAKAYTTAJA]}>
                <h2 className={styles['kyselyt-heading']}>
                    {t('viimeisimmat-sulkeutuneet-kyselyt')}
                </h2>
            </GuardedComponentWrapper>
            {sulkeutuneetKyselyt?.map((kysely) => (
                <div
                    key={`${kysely.kyselyid}_${uniqueNumber()}`}
                    className={styles['kyselyt-wrapper']}
                >
                    <h3>
                        {kysely && (locale === 'fi' ? kysely?.nimi_fi : kysely?.nimi_sv)}
                    </h3>

                    <Table kysely={kysely} />
                    {!paakayttajaLomakkeet.includes(
                        kysely?.lomaketyyppi as LomakeTyyppi,
                    ) && (
                        <GuardedComponentWrapper
                            allowedValssiRoles={[ValssiUserLevel.PAAKAYTTAJA]}
                        >
                            <div className={styles['open-answered-less-than50-wrapper']}>
                                <ButtonWithoutStyles
                                    onClick={() => handleExpandedChange(kysely.nimi_fi!)}
                                >
                                    <span style={{color: '#2f487f'}}>
                                        {t('nayta-toimipaikat')}
                                    </span>
                                </ButtonWithoutStyles>
                            </div>

                            {expanded.includes(kysely.nimi_fi!) && (
                                <AnsweredLessThan50
                                    kysely={kysely}
                                    handleExpandedChange={handleExpandedChange}
                                    kyselyNimi={kysely.nimi_fi!}
                                />
                            )}
                        </GuardedComponentWrapper>
                    )}
                </div>
            ))}
        </div>
    );
}
export default KyselyList;
