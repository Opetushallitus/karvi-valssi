import React, {useContext, useEffect, useRef, useState} from 'react';
import {useLocation, useNavigate} from 'react-router-dom';
import {useTranslation} from 'react-i18next';
import {Box} from '@mui/material';
import {forkJoin, Observable} from 'rxjs';
import {KyselyType, StatusType, TextType} from '@cscfi/shared/services/Data/Data-service';
import Kysely from '@cscfi/shared/components/Kysely/Kysely';
import {
    BoxStyleOverrides,
    formatDate,
    getQueryParamAsNumber,
} from '@cscfi/shared/utils/helpers';
import {
    arvoGetAllKyselyt$,
    arvoGetKysymysryhma$,
    arvoGetKysymysryhmaKayttoraja$,
    ArvoKysely,
    ArvoKysymysryhma,
    Kayttoraja,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {
    raportiointipalveluGetReportingBase$,
    ReportingBase,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import IsUsedType, {
    KyselykertaIsUsedType,
    virkailijapalveluGetIsKysymysryhmaUsed$,
    virkailijapalveluSetKysymysryhmaLocked$,
    virkailijapalveluSetKysymysryhmaUnlocked$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {isBefore, isSameDay, parseISO} from 'date-fns';
import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {AjaxError} from 'rxjs/ajax';
import Lock from '@mui/icons-material/Lock';
import UserContext from '../../Context';
import EsikatseluButtons from './EsikatseluButtons';
import styles from './Esikatselu.module.css';
import GuardedComponentWrapper from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import {hasKayttoraja} from '../../utils/helpers';
import VirkailijaUILanguageButtons from '../../components/VirkailijaUILanguageButtons/VirkailijaUILanguageButtons';

function Esikatselu() {
    const [[kysely, lahdeKysely], setKyselyData] = useState<
        [KyselyType | undefined, ArvoKysely | undefined]
    >([undefined, undefined]);

    const [[kayttorajaYlitetty], setPaakayttajaData] = useState<[string | null]>([null]);

    const [
        [reportingBaseExists, hasActiveKyselys, kyselyActiveUntil],
        setYllapitajaData,
    ] = useState<[boolean, boolean, Date | false]>([false, false, false]);

    const [language, setLanguage] = useState<string | null>(null);

    const navigate = useNavigate();
    const location = useLocation();
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['esikatselu']);
    const userInfo = useContext(UserContext);

    const kysymysryhmaId = getQueryParamAsNumber(location, 'id');

    const mainRef = useRef<HTMLDivElement>();

    useEffect(() => {
        if (kysymysryhmaId) {
            const yllapitajaQueries = forkJoin([
                raportiointipalveluGetReportingBase$(userInfo!)(kysymysryhmaId!),
                virkailijapalveluGetIsKysymysryhmaUsed$(kysymysryhmaId!),
            ]);
            const paakayttajaQueries = forkJoin([
                arvoGetKysymysryhmaKayttoraja$(kysymysryhmaId),
            ]);
            const queries = forkJoin([
                arvoGetKysymysryhma$(kysymysryhmaId),
                arvoGetAllKyselyt$(),
            ]);

            if (userInfo?.rooli.kayttooikeus === ArvoRoles.YLLAPITAJA) {
                yllapitajaQueries.subscribe(
                    ([reportingBase, useStatus]: [
                        reportingBase: ReportingBase,
                        useStatus: KyselykertaIsUsedType,
                    ]) => {
                        setYllapitajaData([
                            !!reportingBase.reporting_template?.id,
                            useStatus.is_used === IsUsedType.active,
                            useStatus.is_active_until ? useStatus.is_active_until : false,
                        ]);
                    },
                );
            }
            if (userInfo?.rooli.kayttooikeus === ArvoRoles.PAAKAYTTAJA) {
                paakayttajaQueries.subscribe(
                    ([kayttoraja]: [kayttoraja: Kayttoraja[]]) => {
                        setPaakayttajaData([hasKayttoraja(kayttoraja, kysymysryhmaId!)]);
                    },
                );
            }
            queries.subscribe(
                ([valssiKysely, kyselyt]: [
                    valssiKysely: KyselyType,
                    kyselyt: ArvoKysely[],
                ]) => {
                    const existingKysely = kyselyt.find((ak: ArvoKysely) => {
                        const loppu = parseISO(ak.voimassa_loppupvm);
                        const nyt = new Date();

                        return (
                            ak.metatiedot.valssi_kysymysryhma === valssiKysely.id &&
                            (isSameDay(nyt, loppu) || isBefore(nyt, loppu))
                        );
                    });

                    setKyselyData([valssiKysely!, existingKysely]);
                },
            );
        }
    }, [kysymysryhmaId, location, userInfo, userInfo?.rooli.kayttooikeus]);

    const handleSetLockedStatus = (lock: boolean) => {
        let f = virkailijapalveluSetKysymysryhmaLocked$;
        if (!lock) f = virkailijapalveluSetKysymysryhmaUnlocked$;

        if (kysymysryhmaId) {
            f(userInfo!)(kysymysryhmaId).subscribe({
                complete: () => {
                    setKyselyData([
                        {
                            ...kysely,
                            status: lock ? StatusType.lukittu : StatusType.julkaistu,
                        } as KyselyType,
                        {...lahdeKysely!},
                    ]);
                    const alertTitle = lock
                        ? 'lock-success-title'
                        : 'unlock-success-title';
                    const alert = {
                        title: {key: alertTitle, ns: 'esikatselu'},
                        severity: 'success',
                    } as AlertType;
                    AlertService.showAlert(alert);
                },
                error: (error: AjaxError) => {
                    console.warn('error while locking or unlocking:', error);
                    const alertTitle = lock ? 'lock-error-title' : 'unlock-error-title';
                    const alert = {
                        title: {key: alertTitle, ns: 'esikatselu'},
                        severity: 'error',
                    } as AlertType;
                    AlertService.showAlert(alert);
                },
            });
        }
    };

    if (!kysely) {
        return null;
    }

    const onClickUpdateKysely = (
        updateKysely$: (int: number) => Observable<ArvoKysymysryhma>,
    ) => {
        updateKysely$(kysely.id).subscribe(() => {
            // currently api returns old version of kysymysryhma instance (bug in api)
            // so it's not worth to update it to state (so maybe later)
        });
        navigate('/indikaattorit');
    };

    const esikatseluButtons = (
        <EsikatseluButtons
            kysely={kysely}
            publishable={reportingBaseExists}
            onClickUpdateKysely={onClickUpdateKysely}
            hasActiveKyselys={hasActiveKyselys}
            activeKyselysUntil={kyselyActiveUntil}
            lahdeKysely={lahdeKysely}
            kysymysryhmaId={kysymysryhmaId}
            kayttorajaYlitetty={kayttorajaYlitetty}
            handleSetLockedStatus={handleSetLockedStatus}
            language={language ? language : lang}
        />
    );

    return (
        <div>
            <div ref={mainRef} tabIndex={-1}>
                <h1>{t('sivun-otsikko')}</h1>
            </div>
            {esikatseluButtons}
            {kysely?.topic?.en && kysely?.topic?.en?.trim().length > 0 && (
                <VirkailijaUILanguageButtons
                    englishTopic={kysely?.topic?.en}
                    setLanguage={setLanguage}
                    selectedLanguage={language ? language : lang}
                />
            )}
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.YLLAPITAJA]}}>
                {kysely.status === StatusType.lukittu && hasActiveKyselys && (
                    <p>
                        {[
                            t('lukitus-kysely-paattyy'),
                            formatDate(kyselyActiveUntil as Date),
                        ].join(' ')}
                    </p>
                )}
            </GuardedComponentWrapper>
            <h2 className={styles.header}>
                {kysely
                    ? kysely.topic[language ? language : (lang as keyof TextType)]
                    : ''}
                {kysely.status === StatusType.lukittu && <Lock />}
            </h2>
            <BoxStyleOverrides>
                <Box>
                    <Kysely
                        selectedKysely={kysely}
                        focusTitleRef={mainRef}
                        language={language}
                    />
                </Box>
            </BoxStyleOverrides>
            {esikatseluButtons}
        </div>
    );
}

export default Esikatselu;
