import {useTranslation} from 'react-i18next';
import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import GuardedComponentWrapper from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import EtusivuKyselytList from './EtusivuKyselytList/EtusivuKyselytList';
import EtusivuKyselytListPaakayttaja from './EtusivuKyselytList/EtusivuKyselytListPaakayttaja';
import EtusivuKyselytListToteuttaja from './EtusivuKyselytList/EtusivuKyselytListToteuttaja';
import FocusableHeader from '../../components/FocusableHeader/FocusableHeader';

function Etusivu() {
    const {t} = useTranslation(['etusivu']);
    return (
        <>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.YLLAPITAJA]}}>
                <FocusableHeader>
                    <>{t('yllapitaja_otsikko')}</>
                </FocusableHeader>
                <EtusivuKyselytList />
            </GuardedComponentWrapper>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.PAAKAYTTAJA]}}>
                <FocusableHeader>
                    <>{t('paakayttaja_otsikko')}</>
                </FocusableHeader>
                <EtusivuKyselytListPaakayttaja />
            </GuardedComponentWrapper>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.TOTEUTTAJA]}}>
                <FocusableHeader>
                    <>{t('toteuttaja_otsikko')}</>
                </FocusableHeader>
                <EtusivuKyselytListToteuttaja />
            </GuardedComponentWrapper>
        </>
    );
}

export default Etusivu;
