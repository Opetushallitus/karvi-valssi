import {useContext, useRef} from 'react';
import {useTranslation} from 'react-i18next';
import {Observable} from 'rxjs';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import {KyselyType, StatusType, TextType} from '@cscfi/shared/services/Data/Data-service';
import {
    ArvoKysely,
    ArvoKysymysryhma,
    arvoPublishKysymysryhma$,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';

import {useLocation, useNavigate} from 'react-router-dom';
import {
    base64ToArrayBuffer,
    virkailijapalveluGetPdfKysymysryhma$,
    virkailijapalveluSetKysymysryhmaArchived$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {AjaxError} from 'rxjs/ajax';
import UserContext from '../../Context';
import LomakeTyyppi, {paakayttajaLomakkeet} from '../../utils/LomakeTyypit';
import ButtonWithLink from '../../components/ButtonWithLink/ButtonWithLink';
import GuardedComponentWrapper, {
    ValssiUserLevel,
} from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';

interface EsikatseluButtonsProps {
    kysely: KyselyType;
    onClickUpdateKysely: (
        updateKysely$: (int: number) => Observable<ArvoKysymysryhma>,
    ) => void;
    publishable: boolean;
    hasActiveKyselys: boolean;
    lahdeKysely: ArvoKysely | undefined;
    kysymysryhmaId: number | null;
}
function EsikatseluButtons({
    kysely,
    onClickUpdateKysely,
    publishable, // "reporting base exists"
    hasActiveKyselys,
    lahdeKysely,
    kysymysryhmaId,
}: EsikatseluButtonsProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['esikatselu']);
    const userInfo = useContext(UserContext);
    const location = useLocation();
    const navigate = useNavigate();

    const prevPath = (location.state as any)?.prevPath;
    const paakayttajaLomake = paakayttajaLomakkeet.includes(
        kysely.lomaketyyppi as LomakeTyyppi,
    );

    const aRef = useRef<any | null>(null);

    const handlePrint = () => {
        virkailijapalveluGetPdfKysymysryhma$(userInfo!)(kysely.id, lang).subscribe(
            (resp) => {
                const arrBuff = base64ToArrayBuffer(resp);
                const blob = new Blob([arrBuff], {type: 'application/pdf'});
                aRef.current.href = window.URL.createObjectURL(blob);
                aRef.current.download = `${lang.toUpperCase()}_${
                    kysely.topic[lang as keyof TextType]
                }.pdf`;
                aRef.current.click();
                return null;
            },
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
                    console.log('error while archiving:', error);
                    const alert = {
                        title: {key: 'archive-error-title', ns: 'esikatselu'},
                        severity: 'error',
                    } as AlertType;
                    AlertService.showAlert(alert);
                },
            });
        }
    };

    return (
        <div className="button-container">
            <ButtonWithLink
                linkTo={prevPage()}
                className="secondary"
                linkText={t('painike-takaisin', {ns: 'yleiset'})}
            />
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.YLLAPITAJA]}>
                {kysely?.status === StatusType.julkaistu &&
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
            </GuardedComponentWrapper>
            <GuardedComponentWrapper
                allowedValssiRoles={[
                    ValssiUserLevel.YLLAPITAJA,
                    ValssiUserLevel.PAAKAYTTAJA,
                ]}
            >
                <button type="button" onClick={handlePrint} className="secondary">
                    {t('tulosta-kysely')}
                </button>
            </GuardedComponentWrapper>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.TOTEUTTAJA]}>
                <button type="button" onClick={handlePrint}>
                    {t('tulosta-kysely')}
                </button>
            </GuardedComponentWrapper>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.YLLAPITAJA]}>
                <ButtonWithLink
                    linkTo={`/rakenna-kysely?id=${kysely.id}`}
                    className="secondary"
                    linkText={t('painike-muokkaa')}
                />
            </GuardedComponentWrapper>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.PAAKAYTTAJA]}>
                {paakayttajaLomake ? (
                    <ButtonWithLink
                        linkTo={`/lahetys?id=${kysely.id}`}
                        linkText={t('painike-lahetys')}
                    />
                ) : (
                    <ButtonWithLink
                        linkTo={`/aktivointi?id=${kysely.id}`}
                        linkText={t(
                            lahdeKysely
                                ? 'painike-aktivointi-lisaa'
                                : 'painike-aktivointi',
                        )}
                    />
                )}
            </GuardedComponentWrapper>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.YLLAPITAJA]}>
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
            <a ref={aRef} href="/#" style={{display: 'none'}}>
                {/* This element requires content */}
                Placeholder label
            </a>
        </div>
    );
}
export default EsikatseluButtons;
