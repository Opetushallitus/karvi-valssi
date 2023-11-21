import {useLocation} from 'react-router-dom';
import {getQueryParam} from '@cscfi/shared/utils/helpers';
import {useTranslation} from 'react-i18next';

import List from './RaportitList';
import ViewRaportti from './ViewRaportti';

function Raportointi() {
    const {t} = useTranslation(['raportointi']);

    const location = useLocation();
    const raportti = getQueryParam(location, 'raportti');
    const alkupvm = getQueryParam(location, 'alkupvm');
    return !raportti && !alkupvm ? (
        <div>
            <h1>{t('arviointityokalujen-raportit')}</h1>
            <List />
        </div>
    ) : (
        <ViewRaportti />
    );
}

export default Raportointi;
