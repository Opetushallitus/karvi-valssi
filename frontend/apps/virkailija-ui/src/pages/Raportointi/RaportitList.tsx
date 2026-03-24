import {Fragment, JSX, useContext, useState} from 'react';
import {NavLink} from 'react-router-dom';
import {useObservableState} from 'observable-hooks';
import {useTranslation} from 'react-i18next';
import {
    AvailableKyselykertaType,
    Laatutekija,
    raportiointipalveluGetRaportit$,
    RaportitKyselykertaType,
    RaportitKyselyType,
    RaportitType,
    raportointipalveluPostSetSkipped$,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import {Grid} from '@mui/material';
import {uniqueNumber} from '@cscfi/shared/utils/helpers';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import UserContext from '../../Context';
import GuardedComponentWrapper from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import ButtonWithLink from '../../components/ButtonWithLink/ButtonWithLink';
import styles from './raportit.module.css';

interface RaporttiToteuttajaRowProps {
    raportti: RaportitType;
    kyselykerta: RaportitKyselykertaType;
    oppilaitosOid: string;
    is_paakayttajan_lomake: boolean;
    userRole: string;
    lang: string;
    t: (key: string, options?: object) => string;
}

function RaporttiToteuttajaRow({
    raportti,
    kyselykerta,
    oppilaitosOid,
    is_paakayttajan_lomake,
    userRole,
    lang,
    t,
}: RaporttiToteuttajaRowProps): JSX.Element {
    const {kysely} = kyselykerta;
    const kyselyNimiKey = `nimi_${lang}` as keyof RaportitKyselyType;
    const kyselyNimi = kysely[kyselyNimiKey] as string;
    const [showConfirmationDialog, setShowConfirmationDialog] = useState(false);
    const userInfo = useContext(UserContext);

    const arviointiTulosUrlParams = new URLSearchParams({
        id: raportti.kysymysryhmaid.toString(),
        koulutustoimija_oid: raportti.koulutustoimija_oid as string,
        alkupvm: kyselykerta.voimassa_alkupvm,
        oppilaitos: oppilaitosOid,
        role: userRole,
    }).toString();

    const updateShowConfirmationDialog = (value: boolean) => {
        setShowConfirmationDialog(value);
    };

    const updateOhitaKysely = (
        kyselyid: number,
        name: string,
        hiddenElementId: string,
        taytaYhteenvetoId: string,
    ) => {
        const element = document.getElementById(name);
        if (element) {
            element.style.display = 'none';
        }
        const hiddenElement = document.getElementById(hiddenElementId);
        if (hiddenElement) {
            hiddenElement.style.display = 'block';
        }
        const taytaYhteenvetoElement = document.getElementById(taytaYhteenvetoId);
        if (taytaYhteenvetoElement) {
            taytaYhteenvetoElement.style.display = 'none';
        }

        raportointipalveluPostSetSkipped$(userInfo!)(kyselyid).subscribe((value) => {
            if (value === 'OK') {
                // do nothing
            } else {
                console.log('updateOhitaKysely returned an error: ' + value);
                const alert = {
                    bodyPlain:
                        t('taustajarjestelma-error-body', {ns: 'alert'}) + ' ' + value,
                    severity: 'error',
                    title: {key: 'taustajarjestelma-error-title', ns: 'alert'},
                    sticky: true,
                    disabled: false,
                } as AlertType;
                AlertService.showAlert(alert);
            }
        });
    };

    return (
        <Fragment key={kyselyNimi || `kyselyNimi_${uniqueNumber()}`}>
            <Grid container item className={styles['grid-row']} size={12}>
                <Grid item size={4} className={styles['report-link']}>
                    {!is_paakayttajan_lomake && kyselykerta.display_report ? (
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
                </Grid>
                <Grid item size={3}>
                    {!is_paakayttajan_lomake && !kyselykerta.display_report && (
                        <p>{t('alle-6-vastausta')}</p>
                    )}
                </Grid>
                <Grid item size={2.5} className={styles['grid-center-column']}>
                    {!is_paakayttajan_lomake &&
                        raportti.laatutekija !== Laatutekija.kansallinen &&
                        (kyselykerta.is_summary_skipped ? (
                            <span id={kyselykerta.nimi + '_visible'}>
                                {t('yhteenveto-ohitettu')}
                            </span>
                        ) : (
                            !is_paakayttajan_lomake &&
                            raportti.laatutekija !== Laatutekija.kansallinen &&
                            (kyselykerta.show_summary ? (
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
                                <>
                                    <div
                                        id={kyselykerta.nimi + '_tayta_yhteenveto_button'}
                                    >
                                        <ButtonWithLink
                                            linkTo={`/yhteenveto?id=${kysely.kyselyid}`}
                                            linkText={t('tayta-yhteenveto')}
                                            className="small"
                                        />
                                    </div>
                                    <ConfirmationDialog
                                        title={t('ohita-yhteenveto-kysymys')}
                                        content={t('ohita-yhteenveto-sisalto')}
                                        confirmBtnText={t('ohita-yhteenveto')}
                                        cancelBtnText={t('painike-peruuta', {
                                            ns: 'yleiset',
                                        })}
                                        confirm={() => {
                                            updateOhitaKysely(
                                                kysely.kyselyid,
                                                kyselykerta.nimi,
                                                kyselykerta.nimi + '_hidden',
                                                kyselykerta.nimi +
                                                    '_tayta_yhteenveto_button',
                                            );
                                            updateShowConfirmationDialog(false);
                                        }}
                                        cancel={() => updateShowConfirmationDialog(false)}
                                        showDialogBoolean={showConfirmationDialog}
                                    >
                                        <div id={kyselykerta.nimi}>
                                            <button
                                                style={{
                                                    marginLeft: '0.5rem',
                                                    whiteSpace: 'normal',
                                                }}
                                                className="small secondary"
                                                onClick={() => {
                                                    updateShowConfirmationDialog(true);
                                                }}
                                            >
                                                {t('ohita-yhteenveto')}
                                            </button>
                                        </div>
                                    </ConfirmationDialog>
                                    <span
                                        style={{display: 'none'}}
                                        id={kyselykerta.nimi + '_hidden'}
                                    >
                                        {t('yhteenveto-ohitettu')}
                                    </span>
                                </>
                            ))
                        ))}
                </Grid>
                <Grid item size={2.5} className={styles['grid-right-column']}>
                    {raportti.laatutekija !== Laatutekija.kansallinen &&
                        (kyselykerta.show_result ? (
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
                            <p>{t('ei-arviointituloksia')}</p>
                        ))}
                </Grid>
            </Grid>
        </Fragment>
    );
}

interface RaporttiPaakayttajaRowProps {
    raportti: RaportitType;
    availableKyselykerta: AvailableKyselykertaType;
    lang: string;
    t: (key: string, options?: object) => string;
}

function RaporttiPaakayttajaRow({
    raportti,
    availableKyselykerta,
    lang,
    t,
}: RaporttiPaakayttajaRowProps) {
    const kyselyNimiKey = `nimi_${lang}` as keyof AvailableKyselykertaType;
    const kyselyNimi = availableKyselykerta[kyselyNimiKey] as string;

    const arviointiTulosUrlParams = new URLSearchParams({
        id: raportti.kysymysryhmaid.toString(),
        koulutustoimija_oid: raportti.koulutustoimija_oid as string,
        alkupvm: availableKyselykerta.kyselykerta_alkupvm,
    }).toString();

    return (
        <Fragment key={kyselyNimi || `kyselyNimi_${uniqueNumber()}`}>
            <Grid container item className={styles['grid-row']} size={12}>
                <Grid item size={5} className={styles['report-link']}>
                    {availableKyselykerta.display_report ? (
                        <NavLink
                            end
                            to={{
                                pathname: `/raportointi`,
                                search: `?raportti=${raportti.kysymysryhmaid}&alkupvm=${availableKyselykerta.kyselykerta_alkupvm}`,
                            }}
                        >
                            {kyselyNimi}
                        </NavLink>
                    ) : (
                        <>
                            <span className={styles['no-link']}>{kyselyNimi}</span>
                            <span>({t('alle-6-vastausta')})</span>
                        </>
                    )}
                </Grid>

                <Grid item size={4}>
                    {raportti.laatutekija !== Laatutekija.kansallinen &&
                        (availableKyselykerta.show_summary ? (
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
                        ))}
                </Grid>
                <Grid item size={3} className={styles['grid-right-column']}>
                    {raportti.laatutekija !== Laatutekija.kansallinen &&
                        (availableKyselykerta.show_result ? (
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
                        ))}
                </Grid>
            </Grid>
        </Fragment>
    );
}

function List() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['raportointi']);
    const userInfo = useContext(UserContext);
    const [raportit] = useObservableState(
        () =>
            raportiointipalveluGetRaportit$(userInfo!)(
                userInfo!.rooli.organisaatio,
                userInfo!.rooli.kayttooikeus,
            ),
        [],
    );

    return (
        <>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.TOTEUTTAJA]}}>
                <Grid container item size={12} className={styles['grid-header']}>
                    <Grid item size={7}>
                        <h3>{t('raportit')}</h3>
                    </Grid>
                    <Grid item className={styles['grid-center-column']} size={2.5}>
                        <h3>{t('yhteenvedot')}</h3>
                    </Grid>
                    <Grid item className={styles['grid-right-column']} size={2.5}>
                        <h3>{t('arviointitulokset')}</h3>
                    </Grid>
                </Grid>
                {raportit
                    .filter(
                        (raportti) =>
                            raportti.kyselykertas.length > 0 ||
                            raportti.is_paakayttaja_lomake,
                    )
                    .map((raportti) => {
                        if (raportti.is_paakayttaja_lomake) {
                            return raportti.available_kyselykertas.map(
                                (akk) =>
                                    ({
                                        raportti,
                                        kyselykerta: {
                                            kysely: {
                                                nimi_fi: akk.nimi_fi,
                                                nimi_sv: akk.nimi_sv,
                                            } as RaportitKyselyType,
                                            voimassa_alkupvm: akk.kyselykerta_alkupvm,
                                            show_result: akk.show_result,
                                        } as RaportitKyselykertaType,
                                        oppilaitosOid:
                                            userInfo?.arvoAktiivinenRooli
                                                .oppilaitokset?.[0].oppilaitos_oid,
                                        userRole:
                                            userInfo?.arvoAktiivinenRooli.kayttooikeus,
                                        is_paakayttajan_lomake: true,
                                        lang,
                                        t,
                                    }) as RaporttiToteuttajaRowProps,
                            );
                        }
                        return raportti.kyselykertas
                            .filter((kk) => !kk.is_active)
                            .map((kk) => {
                                const showResult = raportti.available_kyselykertas.find(
                                    (akk) =>
                                        akk.kyselykerta_alkupvm === kk.voimassa_alkupvm,
                                )?.show_result;
                                return {
                                    raportti,
                                    kyselykerta: {...kk, show_result: showResult},
                                    oppilaitosOid:
                                        userInfo?.arvoAktiivinenRooli.oppilaitokset[0]
                                            .oppilaitos_oid,
                                    userRole: userInfo?.arvoAktiivinenRooli.kayttooikeus,
                                    is_paakayttajan_lomake: false,
                                    lang,
                                    t,
                                } as RaporttiToteuttajaRowProps;
                            });
                    })
                    .flat()
                    .sort((a, b) =>
                        a.kyselykerta.voimassa_alkupvm > b.kyselykerta.voimassa_alkupvm
                            ? -1
                            : 1,
                    )
                    .map((row, index) => (
                        <RaporttiToteuttajaRow key={index} {...row} />
                    ))}
            </GuardedComponentWrapper>

            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.PAAKAYTTAJA]}}>
                <Grid container item size={12} className={styles['grid-header']}>
                    <Grid item size={5}>
                        <h3>{t('raportit')}</h3>
                    </Grid>
                    <Grid item size={4}>
                        <h3>{t('yhteenvedot')}</h3>
                    </Grid>
                    <Grid item className={styles['grid-right-column']} size={3}>
                        <h3>{t('arviointitulokset')}</h3>
                    </Grid>
                </Grid>
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
                    .map((row, index) => (
                        <RaporttiPaakayttajaRow key={index} {...row} />
                    ))}
            </GuardedComponentWrapper>
        </>
    );
}

export default List;
