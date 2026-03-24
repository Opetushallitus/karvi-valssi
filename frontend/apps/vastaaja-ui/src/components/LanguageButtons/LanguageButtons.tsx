import {MouseEvent} from 'react';
import {useTranslation} from 'react-i18next';
import i18n, {LanguageOptions} from '@cscfi/shared/i18n/config';
import styles from './LanguageButtons.module.css';

function LanguageButtons({englishTopic}) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['ulkoasu']);

    const onClickChangeLanguage = (
        event: MouseEvent<HTMLButtonElement>,
        lng: LanguageOptions,
    ) => {
        i18n.changeLanguage(lng);
        event.currentTarget.blur(); // remove focus
    };

    return (
        <div className={`${styles.langButtons} button-container`}>
            <button
                aria-label={`${t('vaihda-kieli')}: ${t('suomi')}`}
                type="button"
                className={`${styles.button} ${styles.secondary}`}
                onClick={(event) => onClickChangeLanguage(event, LanguageOptions.fi)}
                disabled={lang === LanguageOptions.fi}
            >
                {t('suomi', {lng: LanguageOptions.fi})}
            </button>
            <button
                aria-label={`${t('vaihda-kieli')}: ${t('ruotsi')}`}
                type="button"
                className={`${styles.button} ${styles.secondary}`}
                onClick={(event) => onClickChangeLanguage(event, LanguageOptions.sv)}
                disabled={lang === LanguageOptions.sv}
            >
                {t('ruotsi', {lng: LanguageOptions.sv})}
            </button>
            {englishTopic?.length > 0 && (
                <button
                    aria-label={`${t('vaihda-kieli')}: ${t('englanti')}`}
                    type="button"
                    className={`${styles.button} ${styles.secondary}`}
                    onClick={(event) => onClickChangeLanguage(event, LanguageOptions.en)}
                    disabled={lang === LanguageOptions.en}
                >
                    {t('englanti', {lng: LanguageOptions.en})}
                </button>
            )}
        </div>
    );
}

export default LanguageButtons;
