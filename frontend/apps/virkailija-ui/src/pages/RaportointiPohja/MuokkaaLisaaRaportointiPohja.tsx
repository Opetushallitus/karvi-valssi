import {useContext} from 'react';
import {useTranslation} from 'react-i18next';
import {useLocation} from 'react-router-dom';
import {getQueryParamAsNumber} from '@cscfi/shared/utils/helpers';
import {useObservable} from 'rxjs-hooks';
// eslint-disable-next-line max-len
import {raportiointipalveluGetReportingBase$} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import RaporttiPohja from './RaporttiPohja';
import UserContext from '../../Context';

function MuokkaaLisaaRaportointiPohja() {
    const {t} = useTranslation(['raporttipohja']);
    const location = useLocation();
    const kysymysryhmaId = getQueryParamAsNumber(location, 'id');
    const userInfo = useContext(UserContext);

    const reportingBase = useObservable(
        () => raportiointipalveluGetReportingBase$(userInfo!)(kysymysryhmaId!),
        null,
    );
    return (
        <>
            <h1>{t('sivun-otsikko')}</h1>
            {reportingBase && (
                <RaporttiPohja
                    raporttipohja={reportingBase}
                    sourcePage={`esikatselu?id=${reportingBase.kysymysryhmaid}`}
                />
            )}
        </>
    );
}

export default MuokkaaLisaaRaportointiPohja;
