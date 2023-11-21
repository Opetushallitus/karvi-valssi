import {useTranslation} from 'react-i18next';
import styles from './LanguageTitle.module.css';

function LanguageTitle() {
    const {t} = useTranslation(['kysely']);

    return (
        <div className="field-row ">
            <div className={styles['kieli-title-container']}>
                <div className={styles['kieli-title']}>{t('suomi')}</div>
            </div>

            <div className={styles['kieli-title-container']}>
                <div className={styles['kieli-title']}>{t('ruotsi')}</div>
            </div>
        </div>
    );
}

export default LanguageTitle;
