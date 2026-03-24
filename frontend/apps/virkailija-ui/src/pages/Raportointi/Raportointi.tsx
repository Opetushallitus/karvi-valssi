import {useLocation} from 'react-router-dom';
import {getQueryParam} from '@cscfi/shared/utils/helpers';
import {useTranslation} from 'react-i18next';
import {useContext} from 'react';
import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import List from './RaportitList';
import ViewRaportti from './ViewRaportti';
import FocusableHeader from '../../components/FocusableHeader/FocusableHeader';
import UserContext from '../../Context';
import YllapitajaList from './YllapitajaRaportitList';

function Raportointi() {
    const {t} = useTranslation(['raportointi']);

    const location = useLocation();
    const userInfo = useContext(UserContext);
    console.log(userInfo);
    const raportti = getQueryParam(location, 'raportti');
    const alkupvm = getQueryParam(location, 'alkupvm');
    return !raportti && !alkupvm ? (
        <div>
            <FocusableHeader>
                <>{t('arviointityokalujen-raportit')}</>
            </FocusableHeader>
            {userInfo && userInfo.rooli.kayttooikeus === ArvoRoles.YLLAPITAJA ? (
                <YllapitajaList />
            ) : (
                <List />
            )}
        </div>
    ) : (
        <ViewRaportti />
    );
}

export default Raportointi;
