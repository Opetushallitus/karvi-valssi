import {MouseEvent} from 'react';
import {useTranslation} from 'react-i18next';
import i18n, {LanguageOptions} from '@cscfi/shared/i18n/config';

function LanguageButtons() {
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
        <div className="button-container">
            <button
                type="button"
                className="secondary"
                onClick={(event) => onClickChangeLanguage(event, LanguageOptions.fi)}
                disabled={lang === LanguageOptions.fi}
            >
                {t('suomi')}
            </button>
            <button
                type="button"
                className="secondary"
                onClick={(event) => onClickChangeLanguage(event, LanguageOptions.sv)}
                disabled={lang === LanguageOptions.sv}
            >
                {t('ruotsi')}
            </button>
        </div>
    );
}

export default LanguageButtons;
