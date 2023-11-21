import {useContext, useEffect, useState} from 'react';
import {useLocation, useNavigate} from 'react-router-dom';
import {useTranslation} from 'react-i18next';
import {Box} from '@mui/material';
import {forkJoin, Observable} from 'rxjs';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import Kysely from '@cscfi/shared/components/Kysely/Kysely';
import {getQueryParamAsNumber} from '@cscfi/shared/utils/helpers';
import {
    arvoGetAllKyselyt$,
    arvoGetKysymysryhma$,
    ArvoKysely,
    ArvoKysymysryhma,
    convertKysymyksetArvoToValssi,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {
    raportiointipalveluGetReportingBase$,
    ReportingBase,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import IsUsedType, {
    virkailijapalveluGetIsKysymysryhmaUsed$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import UserContext from '../../Context';
import EsikatseluButtons from './EsikatseluButtons';

function Esikatselu() {
    const [kysely, setKysely] = useState<KyselyType | null>(null);
    const [lahdeKysely, setLahdeKysely] = useState<ArvoKysely>();
    const [reportingBaseExists, setReportingBaseExists] = useState<boolean>(false);
    const [hasActiveKyselys, setHasActiveKyselys] = useState<boolean>(true);

    const navigate = useNavigate();
    const location = useLocation();
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['esikatselu']);
    const userInfo = useContext(UserContext);
    const currentUserRole = userInfo?.rooli.kayttooikeus;

    const kysymysryhmaId = getQueryParamAsNumber(location, 'id');

    useEffect(() => {
        if (kysymysryhmaId) {
            const yllapitajaQueries = forkJoin([
                raportiointipalveluGetReportingBase$(userInfo!)(kysymysryhmaId!),
            ]);
            const queries = forkJoin([
                arvoGetKysymysryhma$(kysymysryhmaId),
                arvoGetAllKyselyt$(),
            ]);

            if (userInfo?.rooli.kayttooikeus === 'YLLAPITAJA') {
                yllapitajaQueries.subscribe(
                    ([reportingBase]: [reportingBase: ReportingBase]) => {
                        setReportingBaseExists(!!reportingBase.reporting_template?.id);
                    },
                );
                virkailijapalveluGetIsKysymysryhmaUsed$(kysymysryhmaId!).subscribe(
                    (res) => {
                        setHasActiveKyselys(
                            ![IsUsedType.used, IsUsedType.not_used].includes(res.is_used),
                        );
                    },
                );
            }

            queries.subscribe(
                ([kysymysryhma, kyselyt]: [
                    kysymysryhma: ArvoKysymysryhma,
                    kyselyt: ArvoKysely[],
                ]) => {
                    const valssiKysely: KyselyType = {
                        id: kysymysryhma.kysymysryhmaid,
                        topic: {
                            fi: kysymysryhma.nimi_fi,
                            sv: kysymysryhma?.nimi_sv || '',
                        },
                        kysymykset: convertKysymyksetArvoToValssi(
                            kysymysryhma.kysymykset,
                        ),
                        status: kysymysryhma.tila,
                        lomaketyyppi: kysymysryhma.metatiedot?.lomaketyyppi,
                        paaIndikaattori: kysymysryhma.metatiedot?.paaIndikaattori,
                    };
                    setKysely(valssiKysely);
                    const filteredKyselyt = kyselyt.filter(
                        (ak: ArvoKysely) =>
                            ak.metatiedot.valssi_kysymysryhma === valssiKysely.id,
                    );
                    const existingKysely = filteredKyselyt.find((e) => !!e);
                    if (existingKysely) {
                        setLahdeKysely(existingKysely);
                    }
                },
            );
        }
    }, [
        currentUserRole,
        kysymysryhmaId,
        location,
        userInfo,
        userInfo?.rooli.kayttooikeus,
    ]);

    if (kysely === null) {
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
            lahdeKysely={lahdeKysely}
            kysymysryhmaId={kysymysryhmaId}
        />
    );

    return (
        <>
            <h1>{t('sivun-otsikko')}</h1>
            {esikatseluButtons}
            <h2>{kysely ? kysely.topic[lang as keyof TextType] : ''}</h2>
            <Box>
                <Kysely selectedKysely={kysely} />
            </Box>
            {esikatseluButtons}
        </>
    );
}

export default Esikatselu;
