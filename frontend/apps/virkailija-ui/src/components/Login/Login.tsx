import {useEffect, useState} from 'react';
import {useObservable} from 'rxjs-hooks';
import {useLocation} from 'react-router-dom';
import {useTranslation} from 'react-i18next';
import {clearSession} from '@cscfi/shared/services/Http/Http-service';
import {
    casLoginUrl,
    casLogoutUrl,
    isLoggedIn$,
    userInfo$,
} from '@cscfi/shared/services/Login/Login-service';
import styles from './Login.module.css';

function Login() {
    const login = useObservable(() => isLoggedIn$());
    const userInfo = useObservable(() => userInfo$);
    const location = useLocation();
    const [loginUrl, setLoginUrl] = useState('');
    const {t} = useTranslation(['login']);

    useEffect(() => {
        const search = new URLSearchParams(location.search);
        const url = casLoginUrl(search.get('redirect'));
        setLoginUrl(url);
    }, [location]);

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
            <a href={casLogoutUrl} onClick={() => clearSession()}>
                {t('kirjaudu-ulos')}
            </a>
        </div>
    );
}

export default Login;
