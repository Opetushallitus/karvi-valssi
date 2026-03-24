import {useLocation} from 'react-router-dom';
import {useTranslation} from 'react-i18next';
import {getQueryParam} from '@cscfi/shared/utils/helpers';

function KiitosVastauksesta() {
    const {t} = useTranslation(['kiitos']);
    const location = useLocation();
    const isTemp = getQueryParam(location, 'temp');

    if (isTemp) {
        return (
            <div>
                <h1>{t('vastaukset-tallennettu-valiaikaisesti')}</h1>
                <p>{t('vastaukset-tallennettu-valiaikaisesti-teksti')}</p>
            </div>
        );
    }

    return <h1>{t('kiitos-vastauksesta')}</h1>;
}

export default KiitosVastauksesta;
