import {useTranslation} from 'react-i18next';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import {ArvoKysely} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {
    isTypeOf,
    huoltajaLomakkeet,
    vardaLomakkeet,
} from '@cscfi/shared/utils/LomakeTyypit';
import ButtonWithLink from '../../../components/ButtonWithLink/ButtonWithLink';
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
    futureData?: boolean;
}

function ToimipaikatList({kysymysryhma, futureData}: KyselyLinkProps) {
    const {
        i18n: {language: lang},
        t,
    } = useTranslation(['esikatselu']);
    const langKey = lang as keyof TextType;
    const {id} = kysymysryhma;

    function createSubmitButtonBasedOnFutureData(
        futureData: boolean | undefined,
        linkTo: string,
        arvoKysely: ArvoKysely,
    ) {
        if (futureData) {
            return (
                <ButtonWithLink
                    linkTo={linkTo}
                    linkText={t('painike-lahetys')}
                    className="small"
                    disabled={futureData && futureData === true}
                    disabledExtraText={
                        t('kysely-alkaa') +
                        ' ' +
                        new Intl.DateTimeFormat('fi-FI').format(
                            new Date(Date.parse(arvoKysely.voimassa_alkupvm)),
                        ) +
                        ' ' +
                        t('kysely-paattyy') +
                        ' ' +
                        new Intl.DateTimeFormat('fi-FI').format(
                            new Date(Date.parse(arvoKysely.voimassa_loppupvm)),
                        )
                    }
                />
            );
        } else {
            return (
                <ButtonWithLink
                    linkTo={linkTo}
                    linkText={t('painike-lahetys')}
                    className="small"
                    disabled={futureData && futureData === true}
                />
            );
        }
    }

    return (
        <div className={styles['kysely-toimipaikka-list']}>
            {kysymysryhma?.kyselyt?.map((kysely) => {
                const extKysely = kysely as ExtendedArvoKysely;
                const arvoKysely = kysely as ArvoKysely;
                const linkTo = isTypeOf(vardaLomakkeet, kysymysryhma)
                    ? `/tyontekijat-vardasta-lahetys/${id}/${extKysely.oppilaitos}`
                    : `/lahetys?id=${id}&oid=${extKysely.oppilaitos}`;
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
                            {isTypeOf(huoltajaLomakkeet, kysymysryhma) ? (
                                <ButtonWithLink
                                    linkTo={linkTo}
                                    linkText={t('painike-luo-ryhmalinkki')}
                                    className="small"
                                    disabled={futureData && futureData === true}
                                />
                            ) : (
                                createSubmitButtonBasedOnFutureData(
                                    futureData,
                                    linkTo,
                                    arvoKysely,
                                )
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

export default ToimipaikatList;
