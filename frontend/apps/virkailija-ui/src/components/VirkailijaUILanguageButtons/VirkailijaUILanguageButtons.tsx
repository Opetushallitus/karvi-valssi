import {JSX, MouseEvent, useEffect, useState, useMemo} from 'react';
import {useTranslation} from 'react-i18next';
import {LanguageOptions} from '@cscfi/shared/i18n/config';
import styles from './VirkailijaUILanguageButtons.module.css';

function VirkailijaUILanguageButtons({
    englishTopic,
    setLanguage,
    selectedLanguage,
}): JSX.Element {
    const {i18n} = useTranslation('ulkoasu');

    const [localLanguage, setLocalLanguage] = useState(i18n.language);

    useEffect(() => {
        setLocalLanguage(i18n.language);
    }, [i18n.language]);

    useEffect(() => {
        setLocalLanguage(selectedLanguage);
    }, [selectedLanguage]);

    const tFi = useMemo(() => i18n.getFixedT('fi', 'ulkoasu'), [i18n]);
    const tSv = useMemo(() => i18n.getFixedT('sv', 'ulkoasu'), [i18n]);
    const tEn = useMemo(() => i18n.getFixedT('en', 'ulkoasu'), [i18n]);

    const onClickChangeLanguage = (
        event: MouseEvent<HTMLButtonElement>,
        lng: LanguageOptions,
    ) => {
        setLocalLanguage(lng);
        setLanguage(lng);
        event.currentTarget.blur(); // remove focus
    };

    return (
        <div className={`${styles.langButtons} button-container`}>
            <button
                aria-label={`${tFi('vaihda-kieli')}: ${tFi('suomi')}`}
                type="button"
                className={`${styles.secondary}`}
                onClick={(event) => onClickChangeLanguage(event, LanguageOptions.fi)}
                disabled={localLanguage === LanguageOptions.fi}
            >
                {tFi('suomi')}
            </button>
            <button
                aria-label={`${tSv('vaihda-kieli')}: ${tSv('ruotsi')}`}
                type="button"
                className={`${styles.secondary}`}
                onClick={(event) => onClickChangeLanguage(event, LanguageOptions.sv)}
                disabled={localLanguage === LanguageOptions.sv}
            >
                {tSv('ruotsi')}
            </button>
            {englishTopic?.length > 0 && (
                <button
                    aria-label={`${tEn('vaihda-kieli')}: ${tEn('englanti')}`}
                    type="button"
                    className={`${styles.secondary}`}
                    onClick={(event) => onClickChangeLanguage(event, LanguageOptions.en)}
                    disabled={localLanguage === LanguageOptions.en}
                >
                    {tEn('englanti')}
                </button>
            )}
        </div>
    );
}

export default VirkailijaUILanguageButtons;
