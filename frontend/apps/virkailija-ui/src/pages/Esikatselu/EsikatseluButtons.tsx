import {useContext} from 'react';
import {useTranslation} from 'react-i18next';
import {Observable} from 'rxjs';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import {KyselyType, StatusType} from '@cscfi/shared/services/Data/Data-service';
import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import {
    ArvoKysely,
    ArvoKysymysryhma,
    arvoPublishKysymysryhma$,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';

import {useLocation, useNavigate} from 'react-router-dom';
import {
    virkailijapalveluGetPdfKysymysryhma$,
    virkailijapalveluSetKysymysryhmaArchived$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {AjaxError} from 'rxjs/ajax';
import LomakeTyyppi, {paakayttajaLomakkeet} from '@cscfi/shared/utils/LomakeTyypit';
import {downloadPdf, formatDate} from '@cscfi/shared/utils/helpers';
import UserContext from '../../Context';
import ButtonWithLink from '../../components/ButtonWithLink/ButtonWithLink';
import GuardedComponentWrapper from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';

interface EsikatseluButtonsProps {
    kysely: KyselyType;
    onClickUpdateKysely: (
        updateKysely$: (int: number) => Observable<ArvoKysymysryhma>,
    ) => void;
    publishable: boolean;
    hasActiveKyselys: boolean;
    activeKyselysUntil: Date | false;
    lahdeKysely: ArvoKysely | undefined;
    kysymysryhmaId: number | null;
    kayttorajaYlitetty: string | null;
    handleSetLockedStatus: (lock: boolean) => void;
    language?: string;
}
function EsikatseluButtons({
    kysely,
    onClickUpdateKysely,
    publishable, // "reporting base exists"
    hasActiveKyselys,
    activeKyselysUntil,
    lahdeKysely,
    kysymysryhmaId,
    kayttorajaYlitetty = null,
    handleSetLockedStatus,
    language,
}: EsikatseluButtonsProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['esikatselu']);
    const usedLanguage = language ? language : lang;

    const userInfo = useContext(UserContext);
    const location = useLocation();
    const navigate = useNavigate();

    const prevPath = (location.state as any)?.prevPath;
    const paakayttajaLomake = paakayttajaLomakkeet.includes(
        kysely.lomaketyyppi as LomakeTyyppi,
    );

    const handlePrint = () => {
        const name = `${usedLanguage.toUpperCase()}_${kysely.topic[usedLanguage]}.pdf`;
        downloadPdf(
            virkailijapalveluGetPdfKysymysryhma$(userInfo!)(kysely.id, usedLanguage),
            name,
        );
    };

    function prevPage() {
        return prevPath === 'indikaattorit' ? '/indikaattorit' : '/';
    }

    const archiveKysymysryhma = () => {
        if (kysymysryhmaId) {
            virkailijapalveluSetKysymysryhmaArchived$(userInfo!)(
                kysymysryhmaId,
            ).subscribe({
                complete: () => {
                    const alert = {
                        title: {key: 'archive-success-title', ns: 'esikatselu'},
                        severity: 'success',
                    } as AlertType;
                    AlertService.showAlert(alert);
                    navigate('/indikaattorit');
                },
                error: (error: AjaxError) => {
                    console.warn('error while archiving:', error);
                    const alert = {
                        title: {key: 'archive-error-title', ns: 'esikatselu'},
                        severity: 'error',
                    } as AlertType;
                    AlertService.showAlert(alert);
                },
            });
        }
    };

    const lahetaAktivoiTxt = () => {
        const aktivoiTxt = t(
            lahdeKysely ? 'painike-aktivointi-lisaa' : 'painike-aktivointi',
        );
        return paakayttajaLomake ? t('painike-lahetys') : aktivoiTxt;
    };

    const lahetaAktivoiBtn = () => (
        <ButtonWithLink
            linkTo={`/${paakayttajaLomake ? 'lahetys' : 'aktivointi'}?id=${kysely.id}`}
            linkText={lahetaAktivoiTxt()}
        />
    );

    return (
        <div className="button-container" data-testid="btn-row">
            <ButtonWithLink
                linkTo={prevPage()}
                className="secondary"
                linkText={t('painike-takaisin', {ns: 'yleiset'})}
            />
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.YLLAPITAJA]}}>
                {[StatusType.julkaistu, StatusType.lukittu].includes(kysely?.status) &&
                    kysymysryhmaId &&
                    (hasActiveKyselys ? (
                        <ConfirmationDialog
                            title={t('aktiivisia-kyselyja-otsikko')}
                            confirmBtnText={t('painike-tiedonkeruu-sivulle')}
                            confirm={() => navigate('/tiedonkeruu')}
                            content={t('aktiivisia-kyselyja-content')}
                        >
                            <button type="button" className="warning">
                                {t('painike-arkistoi')}
                            </button>
                        </ConfirmationDialog>
                    ) : (
                        <ConfirmationDialog
                            title={t('arkistoi-otsikko')}
                            confirmBtnText={t('arkistoi-varmistus')}
                            confirm={archiveKysymysryhma}
                            confirmBtnWarning
                            content={t('arkistoi-content')}
                        >
                            <button type="button" className="warning">
                                {t('painike-arkistoi')}
                            </button>
                        </ConfirmationDialog>
                    ))}
                {kysely?.status === StatusType.julkaistu &&
                    kysymysryhmaId &&
                    (hasActiveKyselys ? (
                        <ConfirmationDialog
                            title={t('aktiivisia-kyselyja-otsikko')}
                            content={`${t('lukitus-aktiivisia-content-1')} ${formatDate(
                                activeKyselysUntil as Date,
                            )}${t('lukitus-aktiivisia-content-2')}`}
                            confirmBtnText={t('painike-lukitse')}
                            confirm={() => handleSetLockedStatus(true)}
                        >
                            <button type="button" className="secondary">
                                {t('painike-lukitse')}
                            </button>
                        </ConfirmationDialog>
                    ) : (
                        <button
                            type="button"
                            className="secondary"
                            onClick={() => handleSetLockedStatus(true)}
                        >
                            {t('painike-lukitse')}
                        </button>
                    ))}
                {kysely?.status === StatusType.lukittu && kysymysryhmaId && (
                    <button
                        type="button"
                        className="secondary"
                        onClick={() => handleSetLockedStatus(false)}
                    >
                        {t('painike-poista-lukitus')}
                    </button>
                )}
            </GuardedComponentWrapper>
            <GuardedComponentWrapper
                roles={{
                    arvo: [ArvoRoles.YLLAPITAJA, ArvoRoles.PAAKAYTTAJA],
                }}
            >
                <button type="button" onClick={handlePrint} className="secondary">
                    {t('tulosta-kysely')}
                </button>
            </GuardedComponentWrapper>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.TOTEUTTAJA]}}>
                <button type="button" onClick={handlePrint}>
                    {t('tulosta-kysely')}
                </button>
            </GuardedComponentWrapper>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.YLLAPITAJA]}}>
                <ButtonWithLink
                    linkTo={`/rakenna-kysely?id=${kysely.id}`}
                    className="secondary"
                    linkText={t('painike-muokkaa')}
                />
            </GuardedComponentWrapper>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.PAAKAYTTAJA]}}>
                {!(kysely?.status === StatusType.lukittu && !lahdeKysely) &&
                    (kayttorajaYlitetty ? (
                        <ConfirmationDialog
                            title={t('raja-ylitetty-otsikko')}
                            confirm={() => navigate('/indikaattorit')}
                            confirmBtnText={t('raja-ylitetty-confirm')}
                            cancelBtnHidden
                            content={
                                <p>
                                    {t('raja-ylitetty-teksti', {
                                        pvm: formatDate(kayttorajaYlitetty),
                                    })}
                                </p>
                            }
                        >
                            <button type="button">{lahetaAktivoiTxt()}</button>
                        </ConfirmationDialog>
                    ) : (
                        lahetaAktivoiBtn()
                    ))}
            </GuardedComponentWrapper>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.YLLAPITAJA]}}>
                <ButtonWithLink
                    linkTo={`/raportointipohja?id=${kysely.id}`}
                    onClick={() =>
                        sessionStorage.removeItem(`reportPreviewData_${kysymysryhmaId}`)
                    }
                    className={
                        kysely?.status === StatusType.luonnos && publishable
                            ? 'secondary'
                            : ''
                    }
                    linkText={t(
                        publishable ? 'muokkaa-raporttipohja' : 'luo-raporttipohja',
                    )}
                />
                {kysely?.status === StatusType.luonnos ? (
                    <ConfirmationDialog
                        title={t('dialogi-otsikko')}
                        confirm={() => onClickUpdateKysely(arvoPublishKysymysryhma$)}
                        content={
                            <>
                                <p>{t('dialogi-teksti-1')}</p>
                                <p>{t('dialogi-teksti-2')}</p>
                            </>
                        }
                    >
                        <button disabled={!publishable} type="button">
                            {t('painike-julkaise')}
                        </button>
                    </ConfirmationDialog>
                ) : null}
            </GuardedComponentWrapper>
        </div>
    );
}
export default EsikatseluButtons;
