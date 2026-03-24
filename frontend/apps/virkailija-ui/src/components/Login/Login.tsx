import {useObservableState} from 'observable-hooks';
import {useLocation} from 'react-router-dom';
import {useTranslation} from 'react-i18next';
import {clearSession} from '@cscfi/shared/services/Http/Http-service';
import {
    casLoginUrl,
    casLogoutUrl,
    expireRefreshTokens,
    isLoggedIn$,
    userInfo$,
} from '@cscfi/shared/services/Login/Login-service';
import styles from './Login.module.css';

function Login() {
    const [login] = useObservableState(() => isLoggedIn$());
    const [userInfo] = useObservableState(() => userInfo$);
    const location = useLocation();
    const {t} = useTranslation(['login']);

    // johda arvo suoraan renderissä
    const search = new URLSearchParams(location.search);
    const loginUrl = casLoginUrl(search.get('redirect'));

    const handleLogout = () => {
        expireRefreshTokens();
        clearSession();
    };

    if (!login?.isLoggedIn) {
        return (
            <div className={styles.Login} data-testid="Login">
                <h1>{t('ei-kirjauduttu')}</h1>
                <a href={loginUrl}>{t('kirjaudu-sisaan')}</a>
            </div>
        );
    }

    return (
        <div className={styles.Login} data-testid="Login">
            <h1>
                {t('olet-kirjautunut-kayttajana')} {userInfo?.nimi}
            </h1>
            <a href={casLogoutUrl} onClick={handleLogout}>
                {t('kirjaudu-ulos')}
            </a>
        </div>
    );
}

export default Login;
