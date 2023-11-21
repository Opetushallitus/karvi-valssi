import {Fragment, useContext} from 'react';
import {NavLink} from 'react-router-dom';
import {useObservable} from 'rxjs-hooks';
import {useTranslation} from 'react-i18next';
import {
    AvailableKyselykertaType,
    raportiointipalveluGetRaportit$,
    RaportitKyselykertaType,
    RaportitKyselyType,
    RaportitType,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import UserContext from '../../Context';
import GuardedComponentWrapper, {
    ValssiUserLevel,
} from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import ButtonWithLink from '../../components/ButtonWithLink/ButtonWithLink';
import styles from './raportit.module.css';

interface RaporttiToteuttajaRowProps {
    raportti: RaportitType;
    kyselykerta: RaportitKyselykertaType;
    lang: string;
    t: (key: string, options?: object) => string;
}

function raporttiToteuttajaRow({
    raportti,
    kyselykerta,
    lang,
    t,
}: RaporttiToteuttajaRowProps) {
    const {kysely} = kyselykerta;
    const kyselyNimiKey = `nimi_${lang}` as keyof RaportitKyselyType;
    const kyselyNimi = kysely[kyselyNimiKey] as string;
    return (
        <Fragment key={kyselyNimi}>
            <div
                className={
                    !kyselykerta.display_report ? styles['grid-a'] : styles['grid-a-b']
                }
            >
                {kyselykerta.display_report ? (
                    <NavLink
                        end
                        to={{
                            pathname: '/raportointi',
                            search: `?raportti=${raportti.kysymysryhmaid}&alkupvm=${kyselykerta.voimassa_alkupvm}`,
                        }}
                    >
                        {kyselyNimi}
                    </NavLink>
                ) : (
                    <span className={styles['no-link']}>{kyselyNimi}</span>
                )}
            </div>

            {!kyselykerta.display_report && (
                <div className={styles['grid-b']}>
                    <p>{t('alle-6-vastausta')}</p>
                </div>
            )}
            <div className={styles['grid-c']}>
                {kyselykerta.show_summary ? (
                    <NavLink
                        className={styles.linkToSummaryView}
                        end
                        to={{
                            pathname: `/yhteenveto`,
                            search: `?id=${kysely.kyselyid}`,
                        }}
                    >
                        {t('katso-yhteenveto')}
                    </NavLink>
                ) : (
                    <ButtonWithLink
                        linkTo={`/yhteenveto?id=${kysely.kyselyid}`}
                        linkText={t('tayta-yhteenveto')}
                        className="small"
                    />
                )}
            </div>
        </Fragment>
    );
}

interface RaporttiPaakayttajaRowProps {
    raportti: RaportitType;
    availableKyselykerta: AvailableKyselykertaType;
    lang: string;
    t: (key: string, options?: object) => string;
}

function raporttiPaakayttajaRow({
    raportti,
    availableKyselykerta,
    lang,
    t,
}: RaporttiPaakayttajaRowProps) {
    const kyselyNimiKey = `nimi_${lang}` as keyof AvailableKyselykertaType;
    const kyselyNimi = availableKyselykerta[kyselyNimiKey] as string;
    // eslint-disable-next-line max-len
    const arviointiTulosUrlParams = `id=${raportti.kysymysryhmaid}&koulutustoimija_oid=${raportti.koulutustoimija_oid}&alkupvm=${availableKyselykerta.kyselykerta_alkupvm}`;
    return (
        <Fragment key={kyselyNimi}>
            <div className={styles['grid-a']}>
                {availableKyselykerta.display_report ? (
                    <NavLink
                        end
                        to={{
                            pathname: `/raportointi`,
                            // eslint-disable-next-line max-len
                            search: `?raportti=${raportti.kysymysryhmaid}&alkupvm=${availableKyselykerta.kyselykerta_alkupvm}`,
                        }}
                    >
                        {kyselyNimi}
                    </NavLink>
                ) : (
                    <span className={styles['no-link']}>{kyselyNimi}</span>
                )}
                {!availableKyselykerta.display_report && <p>({t('alle-6-vastausta')})</p>}
            </div>

            <div className={styles['grid-b']}>
                {availableKyselykerta.show_summary ? (
                    <NavLink
                        className={styles.linkToSummaryView}
                        end
                        to={{
                            pathname: `/yhteenvedot`,
                            search: `?${arviointiTulosUrlParams}`,
                        }}
                    >
                        {t('katso-yhteenvedot')}
                    </NavLink>
                ) : (
                    <p>{t('ei-toimipaikkojen-yhteenvetoja')}</p>
                )}
            </div>
            <div className={styles['grid-c']}>
                {availableKyselykerta.show_result ? (
                    <NavLink
                        className={styles.linkToSummaryView}
                        end
                        to={{
                            pathname: `/arviointitulokset`,
                            search: `?${arviointiTulosUrlParams}`,
                        }}
                    >
                        {t('katso-arviointitulokset')}
                    </NavLink>
                ) : (
                    <ButtonWithLink
                        linkTo={`/arviointitulokset?${arviointiTulosUrlParams}`}
                        linkText={t('tayta-arviointitulokset')}
                        className="small"
                    />
                )}
            </div>
        </Fragment>
    );
}

function List() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['raportointi']);
    const userInfo = useContext(UserContext);
    const raportit = useObservable(
        () =>
            raportiointipalveluGetRaportit$(userInfo!)(
                userInfo!.rooli.organisaatio,
                userInfo!.rooli.kayttooikeus,
            ),
        [],
    );

    return (
        <div className={styles['grid-wrapper']}>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.PAAKAYTTAJA]}>
                <h3 className={styles['grid-a']}>{t('raportit')}</h3>
                <h3 className={styles['grid-b']}>{t('yhteenvedot')}</h3>
                <h3 className={styles['grid-c']}>{t('arviointitulokset')}</h3>
            </GuardedComponentWrapper>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.TOTEUTTAJA]}>
                <h3 className={styles['grid-a-b']}>{t('raportit')}</h3>
                <h3 className={styles['grid-c']}>{t('yhteenvedot')}</h3>
            </GuardedComponentWrapper>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.TOTEUTTAJA]}>
                {raportit
                    .filter((raportti) => raportti.kyselykertas.length > 0)
                    .map((raportti) =>
                        raportti.kyselykertas.map(
                            (kk) =>
                                ({
                                    raportti,
                                    kyselykerta: kk,
                                    lang,
                                    t,
                                }) as RaporttiToteuttajaRowProps,
                        ),
                    )
                    .flat()
                    .sort((a, b) =>
                        a.kyselykerta.voimassa_alkupvm > b.kyselykerta.voimassa_alkupvm
                            ? -1
                            : 1,
                    )
                    .map((row) => raporttiToteuttajaRow(row))}
            </GuardedComponentWrapper>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.PAAKAYTTAJA]}>
                {raportit
                    .filter((raportti) => raportti.available_kyselykertas.length > 0)
                    .map((raportti) =>
                        raportti.available_kyselykertas.map(
                            (akk) =>
                                ({
                                    raportti,
                                    availableKyselykerta: akk,
                                    lang,
                                    t,
                                }) as RaporttiPaakayttajaRowProps,
                        ),
                    )
                    .flat()
                    .sort((a, b) =>
                        a.availableKyselykerta.kyselykerta_alkupvm >
                        b.availableKyselykerta.kyselykerta_alkupvm
                            ? -1
                            : 1,
                    )
                    .map((row) => raporttiPaakayttajaRow(row))}
            </GuardedComponentWrapper>
        </div>
    );
}

export default List;
