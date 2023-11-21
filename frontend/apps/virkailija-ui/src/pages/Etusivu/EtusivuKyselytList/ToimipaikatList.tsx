import {useTranslation} from 'react-i18next';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import {ArvoKysely} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import ButtonWithLink from '../../../components/ButtonWithLink/ButtonWithLink';
import LomakeTyyppi, {huoltajaLomakkeet} from '../../../utils/LomakeTyypit';
import styles from './EtusivuKyselytList.module.css';

export type ExtendedArvoKysely = ArvoKysely & {
    oppilaitos_nimi?: TextType;
};
export type KyselyRequestType = {
    kysymysryhmaid: number;
    organisaatio: string;
};

export type ExtendedKyselyType = KyselyType & {
    kyselyt: ExtendedArvoKysely[];
    kyselykertaid?: number;
    lastKyselysend?: any;
    voimassaLoppupvm?: Date;
};

interface KyselyLinkProps {
    kysymysryhma: ExtendedKyselyType;
}

function ToimipaikatList({kysymysryhma}: KyselyLinkProps) {
    const {
        i18n: {language: lang},
        t,
    } = useTranslation(['esikatselu']);
    const langKey = lang as keyof TextType;
    const {id} = kysymysryhma;
    const lomakeTyyppiVardaCheck =
        kysymysryhma.lomaketyyppi.includes('henkilostolomake') ||
        kysymysryhma.lomaketyyppi.includes('taydennyskoulutuslomake');
    const urlLink = lomakeTyyppiVardaCheck ? 'tyontekijat-vardasta-lahetys' : 'lahetys';
    return (
        <div className={styles['kysely-toimipaikka-list']}>
            {kysymysryhma?.kyselyt?.map((kysely) => {
                const extKysely = kysely as ExtendedArvoKysely;
                const linkTo = lomakeTyyppiVardaCheck
                    ? `/${urlLink}/${id}/${extKysely.oppilaitos}`
                    : `/${urlLink}?id=${id}&oid=${extKysely.oppilaitos}`;
                return (
                    <div
                        key={extKysely.oppilaitos}
                        className={styles['kysely-toimipaikka-container']}
                    >
                        <div className={styles['kysely-toimipaikka-nimi']}>
                            {extKysely.oppilaitos_nimi?.[langKey] ||
                                extKysely.oppilaitos_nimi?.fi ||
                                extKysely.oppilaitos}
                        </div>
                        <div className={styles['kysely-toimipaikka-buttons']}>
                            {huoltajaLomakkeet.includes(
                                kysymysryhma.lomaketyyppi as LomakeTyyppi,
                            ) ? (
                                <ButtonWithLink
                                    linkTo={linkTo}
                                    linkText={t('painike-luo-ryhmalinkki')}
                                    className="small"
                                />
                            ) : (
                                <ButtonWithLink
                                    linkTo={linkTo}
                                    linkText={t('painike-lahetys')}
                                    className="small"
                                />
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

export default ToimipaikatList;
