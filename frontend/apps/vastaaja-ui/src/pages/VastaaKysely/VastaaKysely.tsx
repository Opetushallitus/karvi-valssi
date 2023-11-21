import {useEffect, useState, useCallback} from 'react';
import {useTranslation} from 'react-i18next';
import {useLocation, useParams} from 'react-router-dom';
import {Box} from '@mui/material';
import {convertKysymyksetArvoToValssi} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import Kysely from '@cscfi/shared/components/Kysely/Kysely';
import {getQueryParam} from '@cscfi/shared/utils/helpers';
import vastauspalveluGetKyselykerta$ from '@cscfi/shared/services/Vastauspalvelu-api/Vastauspalvelu-api-service';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {AjaxError} from 'rxjs/internal/ajax/errors';
import LanguageButtons from '../../components/LanguageButtons/LanguageButtons';

function VastaaKysely() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['vastaa-kysely']);
    const location = useLocation();
    const {vastaajatunnus: vastaajatunnusParam} = useParams();
    const vastaajatunnusQueryParam = getQueryParam(location, 'vastaajatunnus');
    const vastaajatunnus = vastaajatunnusParam || vastaajatunnusQueryParam;
    const [kyselyData, setKyselyData] = useState<[KyselyType | null, boolean | false]>([
        null,
        false,
    ]);
    const [loadingError, setLoadingError] = useState<404 | 403 | -1 | null>(null);

    const getKyselyKerta = useCallback(() => {
        if (vastaajatunnus && vastaajatunnus.length > 0) {
            vastauspalveluGetKyselykerta$(vastaajatunnus!).subscribe({
                next: (kyselykerta) => {
                    // TODO: miksi vaati kysymysryhmaDouble? Kts. Vastauspalvelu-api-service.
                    const {kysymysryhma} = kyselykerta.kysely.kysymysryhmat[0];
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
                        lomaketyyppi: kysymysryhma.metatiedot.lomaketyyppi,
                        paaIndikaattori: kysymysryhma.metatiedot?.paaIndikaattori,
                    };
                    setKyselyData([
                        valssiKysely,
                        kyselykerta?.tempvastaus_allowed || false,
                    ]);
                },
                error: (err: AjaxError) => {
                    if (err.status === 403) {
                        const alert = {
                            body: {key: 'vastauspalvelu-ratelimit-body', ns: 'alert'},
                            severity: 'error',
                            title: {key: 'vastauspalvelu-failure-title', ns: 'alert'},
                        } as AlertType;
                        AlertService.showAlert(alert);
                        setLoadingError(403);
                    } else {
                        setLoadingError(404);
                    }
                },
            });
        } else {
            setLoadingError(-1);
        }
    }, [vastaajatunnus]);

    useEffect(() => {
        getKyselyKerta();
    }, [getKyselyKerta]);

    return (
        <>
            <LanguageButtons />
            {loadingError && (
                <h1>
                    {loadingError === 403
                        ? t('vastauspalvelu-ratelimit-body', {ns: 'alert'})
                        : t('ei-kyselya')}
                </h1>
            )}
            {kyselyData[0] && (
                <>
                    <h1>{kyselyData[0].topic[lang as keyof TextType]}</h1>
                    <Box sx={{maxWidth: 'md'}}>
                        <Kysely
                            vastaajaUi
                            selectedKysely={kyselyData[0]}
                            vastaajatunnus={vastaajatunnus!}
                            tempAnswersAllowed={kyselyData[1]}
                        />
                    </Box>
                </>
            )}
        </>
    );
}

export default VastaaKysely;
