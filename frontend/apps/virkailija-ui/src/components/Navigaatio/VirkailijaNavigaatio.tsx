import {NavLink} from 'react-router-dom';
import {useTranslation} from 'react-i18next';
import Logo from '@cscfi/shared/components/Navigaatio/Logo';
import styles from '@cscfi/shared/components/Navigaatio/Navigaatio.module.css';
import {allowedRoles} from '@cscfi/shared/services/Login/Login-service';
import GuardedNavigaatio from './GuardedNavigaatio';
import VirkailijaMenu from './VirkailijaMenu';

const isNavActive = ({isActive}: {isActive: boolean}) =>
    isActive ? styles.selected : undefined;

function VirkailijaNavigaatio() {
    const {t} = useTranslation(['ulkoasu']);

    return (
        <nav>
            <div className={styles.logo}>
                <Logo />
                <div className={styles.header_right}>
                    <VirkailijaMenu />
                </div>
            </div>
            <div className={styles.navlinks}>
                <GuardedNavigaatio roles={allowedRoles.etusivu}>
                    <NavLink end to={{pathname: '/'}} className={isNavActive}>
                        {t('etusivu')}
                    </NavLink>
                </GuardedNavigaatio>
                <GuardedNavigaatio roles={allowedRoles.indikaattorit}>
                    <NavLink to={{pathname: '/indikaattorit'}} className={isNavActive}>
                        {t('arviointityokalut')}
                    </NavLink>
                </GuardedNavigaatio>
                <GuardedNavigaatio roles={allowedRoles.tiedonkeruu}>
                    <NavLink to={{pathname: '/tiedonkeruu'}} className={isNavActive}>
                        {t('tiedonkeruun-seuranta')}
                    </NavLink>
                </GuardedNavigaatio>
                <GuardedNavigaatio roles={allowedRoles.raportointi}>
                    <NavLink to={{pathname: '/raportointi'}} className={isNavActive}>
                        {t('raportointi')}
                    </NavLink>
                </GuardedNavigaatio>
            </div>
        </nav>
    );
}

export default VirkailijaNavigaatio;
