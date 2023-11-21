import {useTranslation} from 'react-i18next';
import GuardedComponentWrapper, {
    ValssiUserLevel,
} from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import EtusivuKyselytList from './EtusivuKyselytList/EtusivuKyselytList';
import EtusivuKyselytListPaakayttaja from './EtusivuKyselytList/EtusivuKyselytListPaakayttaja';
import EtusivuKyselytListToteuttaja from './EtusivuKyselytList/EtusivuKyselytListToteuttaja';

function Etusivu() {
    const {t} = useTranslation(['etusivu']);
    return (
        <>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.YLLAPITAJA]}>
                <h1>{t('yllapitaja_otsikko')}</h1>
                <EtusivuKyselytList />
            </GuardedComponentWrapper>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.PAAKAYTTAJA]}>
                <h1>{t('paakayttaja_otsikko')}</h1>
                <EtusivuKyselytListPaakayttaja />
            </GuardedComponentWrapper>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.TOTEUTTAJA]}>
                <h1>{t('toteuttaja_otsikko')}</h1>
                <EtusivuKyselytListToteuttaja />
            </GuardedComponentWrapper>
        </>
    );
}

export default Etusivu;
