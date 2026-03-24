import {useEffect, useState, useRef} from 'react';
import {useTranslation} from 'react-i18next';
import {useLocation, useParams} from 'react-router-dom';
import Box from '@mui/material/Box';
import {convertKysymysRyhmaToValssi} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import Kysely from '@cscfi/shared/components/Kysely/Kysely';
import {BoxStyleOverrides, getQueryParam} from '@cscfi/shared/utils/helpers';
import vastauspalveluGetKyselykerta$ from '@cscfi/shared/services/Vastauspalvelu-api/Vastauspalvelu-api-service';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {AjaxError} from 'rxjs/internal/ajax/errors';
import i18n from '@cscfi/shared/i18n/config';
import LanguageButtons from '../../components/LanguageButtons/LanguageButtons';

type ErrorResponse = {
    error_code?: string;
    description?: string;
};

function VastaaKysely() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['vastaa-kysely']);
    const location = useLocation();
    const {vastaajatunnus: vastaajatunnusParam} = useParams();
    const vastaajatunnusQueryParam = getQueryParam(location, 'vastaajatunnus');
    const vastaajatunnus = vastaajatunnusParam || vastaajatunnusQueryParam;
    const [kyselyData, setKyselyData] = useState<[KyselyType | null, boolean]>([
        null,
        false,
    ]);
    // Jos vastaajatunnusta ei ole, merkitse virhe heti *ilman efektiä* (lazy initializer)
    const [loadingError, setLoadingError] = useState<
        404 | 403 | 400 | 'AR002' | 'AR004' | 'AR005' | -1 | null
    >(() => (!vastaajatunnus ? -1 : null));

    useEffect(() => {
        // Ei tunnusta → ei efektiä (tila alustettiin jo -1:ksi yllä)
        if (!vastaajatunnus) return;

        const sub = vastauspalveluGetKyselykerta$(vastaajatunnus).subscribe({
            next: (kyselykerta) => {
                const {kysymysryhma} = kyselykerta.kysely.kysymysryhmat[0];
                const valssiKysely = convertKysymysRyhmaToValssi(kysymysryhma);
                setKyselyData([valssiKysely, Boolean(kyselykerta?.tempvastaus_allowed)]);
                // huom. tämä tapahtuu *asynkronisesti* → sallittua efektissä
            },
            error: (err: AjaxError) => {
                // --- pidetään sama virhekartoitus kuin aiemmin ---
                try {
                    const errorMessage = JSON.parse(err.response)[0] as ErrorResponse;
                    if (err.status === 400) {
                        if (errorMessage.error_code === 'AR002') setLoadingError('AR002');
                        else if (errorMessage.error_code === 'AR005')
                            setLoadingError('AR005');
                        else if (errorMessage.error_code === 'AR004')
                            setLoadingError('AR004');
                        else setLoadingError(400);
                    } else if (err.status === 403) {
                        const alert: AlertType = {
                            body: {key: 'vastauspalvelu-ratelimit-body', ns: 'alert'},
                            severity: 'error',
                            title: {key: 'vastauspalvelu-failure-title', ns: 'alert'},
                        };
                        AlertService.showAlert(alert);
                        setLoadingError(403);
                    } else {
                        setLoadingError(404);
                    }
                } catch {
                    setLoadingError(404);
                }
            },
        });

        return () => sub.unsubscribe();
    }, [vastaajatunnus]);

    if (
        lang !== 'fi' &&
        lang !== 'sv' &&
        (kyselyData[0]?.topic?.en == null || kyselyData[0]?.topic?.en?.length === 0)
    ) {
        i18n.changeLanguage('fi');
    }

    const errorText = () => {
        if (loadingError === 403)
            return t('vastauspalvelu-ratelimit-body', {ns: 'alert'});
        if (loadingError === 'AR002') return t('vastaajatunnus-kaytetty');
        if (loadingError === 'AR004') return t('kysely-ei-alkanut');
        if (loadingError === 'AR005') return t('kysely-paattynyt');
        return t('ei-kyselya');
    };

    const mainRef = useRef<HTMLDivElement>(null);

    return (
        <div>
            <div ref={mainRef} tabIndex={-1}></div>

            {loadingError && <h1>{errorText()}</h1>}
            {kyselyData[0] && (
                <div>
                    <LanguageButtons englishTopic={kyselyData[0]?.topic?.en} />
                    <h1>{kyselyData[0]?.topic[lang as keyof TextType]}</h1>
                    <BoxStyleOverrides>
                        <Box sx={{maxWidth: 'md'}}>
                            <Kysely
                                vastaajaUi
                                selectedKysely={kyselyData[0]}
                                vastaajatunnus={vastaajatunnus!}
                                tempAnswersAllowed={kyselyData[1]}
                                focusTitleRef={mainRef}
                            />
                        </Box>
                    </BoxStyleOverrides>
                </div>
            )}
        </div>
    );
}

export default VastaaKysely;
