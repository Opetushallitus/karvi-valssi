import React, {useContext, useState} from 'react';
import {useTranslation} from 'react-i18next';
import IconButton from '@mui/material/IconButton';
import PersonIcon from '@mui/icons-material/Person';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import SelectLanguage from '@cscfi/shared/components/Navigaatio/SelectLanguage';
import styles from '@cscfi/shared/components/Navigaatio/Navigaatio.module.css';
import {LanguageOptions} from '@cscfi/shared/i18n/config';
import LaunchIcon from '@mui/icons-material/Launch';
import {clearSession} from '@cscfi/shared/services/Http/Http-service';
import {
    casLogoutUrl,
    ArvoRoles,
    expireRefreshTokens,
} from '@cscfi/shared/services/Login/Login-service';
import {ArvoRooli} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import UserContext from '../../Context';
import GuardedComponentWrapper from '../GuardedComponentWrapper/GuardedComponentWrapper';
import ImpersonateStart from '../Impersonate/ImpersonateStart';
import ImpersonateEnd from '../Impersonate/ImpersonateEnd';
import ImpersonateRooli from '../Impersonate/ImpersonateRooli';

function VirkailijaMenu() {
    const {t, i18n} = useTranslation(['ulkoasu']);
    const userInfo = useContext(UserContext);

    const Logout = () => {
        expireRefreshTokens();
        clearSession();
        window.location.replace(casLogoutUrl);
    };

    const [menuVis, setMenuVis] = useState(false);
    const [languageMenuVis, setLanguageMenuVis] = useState(false);
    const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

    const handleLanguageSelect = (event: React.SyntheticEvent) => {
        const newLanguage = event.currentTarget.getAttribute('data-language');
        if (newLanguage !== null) {
            i18n.changeLanguage(newLanguage);
        }
        setLanguageMenuVis(false);
    };

    const rooliKoulutustoimija = `koulutustoimija_${i18n.language}` as keyof ArvoRooli;

    const isUserImp = userInfo?.impersonoitu_kayttaja !== '';
    const isOrgImp = userInfo?.vaihdettu_organisaatio !== '';

    return (
        <>
            <div className={styles.instructionsLink}>
                <a href={t('kayttoohjeet-url')} target="_blank" rel="noreferrer">
                    {/* Inline style for unique element */}
                    {t('kayttoohjeet')}
                    <LaunchIcon fontVariant="externalLaunch" />
                </a>
            </div>
            {!userInfo && <SelectLanguage />}
            {userInfo && (
                <div
                    className={`${styles['menu-wrapper']}${
                        isUserImp ? ` ${styles['imp-bg']}` : ''
                    }`}
                >
                    <IconButton
                        aria-haspopup="menu"
                        className={styles['user-button']}
                        onClick={(e) => {
                            // talleta ankkuri ja avaa päävalikko
                            setAnchorEl(e.currentTarget);
                            setMenuVis((prev) => !prev);
                        }}
                    >
                        <PersonIcon />
                        {userInfo.nimi}
                        <ArrowDropDownIcon />
                    </IconButton>

                    <Menu
                        anchorEl={anchorEl}
                        keepMounted
                        open={menuVis}
                        onClose={() => setMenuVis(false)}
                        onClick={() => setMenuVis(false)}
                    >
                        <MenuItem
                            onClick={() => {
                                // sulje päävalikko, avaa kielivalikko
                                setMenuVis(false);
                                setLanguageMenuVis(true);
                            }}
                        >
                            {t('vaihda-kieli')}
                        </MenuItem>

                        {!isUserImp && !isOrgImp && (
                            <GuardedComponentWrapper
                                roles={{arvo: [ArvoRoles.YLLAPITAJA]}}
                            >
                                <ImpersonateStart />
                            </GuardedComponentWrapper>
                        )}

                        {(isUserImp || isOrgImp) && <ImpersonateEnd />}

                        {userInfo.arvoRoolit.length > 1 && (
                            <ImpersonateRooli
                                aktiivinen={userInfo.arvoAktiivinenRooli}
                                roolit={userInfo.arvoRoolit}
                            />
                        )}
                        <MenuItem
                            onClick={() => {
                                Logout();
                            }}
                        >
                            {t('kirjaudu-ulos')}
                        </MenuItem>
                    </Menu>
                    <Menu
                        id="select-language"
                        anchorEl={anchorEl}
                        keepMounted
                        open={languageMenuVis}
                        onClose={() => setLanguageMenuVis(false)}
                    >
                        <MenuItem
                            data-language={LanguageOptions.fi}
                            onClick={handleLanguageSelect}
                        >
                            {t('suomi')}
                        </MenuItem>
                        <MenuItem
                            data-language={LanguageOptions.sv}
                            onClick={handleLanguageSelect}
                        >
                            {t('ruotsi')}
                        </MenuItem>
                    </Menu>
                    <div className={styles['user-info']}>
                        <span className={styles['user-uid']}>{userInfo.uid}</span>
                        <span className={styles['user-divider']}>|</span>
                        <span
                            className={`${styles['user-role']}${
                                isOrgImp ? ` ${styles['imp-bg']}` : ''
                            }`}
                        >
                            {t(userInfo.rooli.kayttooikeus.toLowerCase(), {
                                ns: 'login',
                            })}
                        </span>
                        <span
                            className={`${styles['user-divider']}${
                                isOrgImp ? ` ${styles['imp-bg']}` : ''
                            }`}
                        >
                            |
                        </span>
                        <span
                            className={`${styles['user-org']}${
                                isOrgImp ? ` ${styles['imp-bg']}` : ''
                            }`}
                        >
                            {userInfo.rooli[rooliKoulutustoimija] as string}
                        </span>
                    </div>
                </div>
            )}
        </>
    );
}

export default VirkailijaMenu;
