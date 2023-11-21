import {useContext} from 'react';
import {useTranslation} from 'react-i18next';
import {arvoLopetaImpersonointi$} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import MenuItem from '@mui/material/MenuItem';
import navistyles from '@cscfi/shared/components/Navigaatio/Navigaatio.module.css';
import UserContext from '../../Context';

function ImpersonateEnd() {
    const {t} = useTranslation(['ulkoasu']);
    const userInfo = useContext(UserContext);

    const refresh = () => {
        window.location.replace(`${window.location.origin}/virkailija-ui/`);
    };

    return (
        <MenuItem
            className={navistyles.impersonation}
            onClick={() => {
                arvoLopetaImpersonointi$.subscribe({
                    next: () => {
                        refresh();
                    },
                });
            }}
        >
            {t('menu-button-end', {
                ns:
                    userInfo?.impersonoitu_kayttaja !== ''
                        ? 'impersonointi-avustus'
                        : 'impersonointi-organisaatio',
            })}
        </MenuItem>
    );
}

export default ImpersonateEnd;
