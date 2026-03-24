import {Dispatch, SetStateAction, useRef} from 'react';
import {useTranslation} from 'react-i18next';
import styles from './LanguageTitle.module.css';

type Props = {
    showEnglish: boolean;
    ruotsiVaiEnglantiValittu: string;
    setRuotsiVaiEnglantiValittu: Dispatch<SetStateAction<string | null>>;
};

function LanguageTitle({
    showEnglish,
    ruotsiVaiEnglantiValittu,
    setRuotsiVaiEnglantiValittu,
}: Props) {
    const {t} = useTranslation(['kysely']);

    const ruotsiRef = useRef<HTMLDivElement | null>(null);

    const englantiRef = useRef<HTMLDivElement | null>(null);

    function ruotsiValittu() {
        setRuotsiVaiEnglantiValittu('ruotsi');
    }

    function englantiValittu() {
        setRuotsiVaiEnglantiValittu('englanti');
    }

    function handleRuotsiKeyDown(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            ruotsiRef.current?.click();
        }
    }

    function handleEnglantiKeyDown(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            englantiRef.current?.click();
        }
    }

    return (
        <div className="field-row ">
            <div className={styles['kieli-title-container']}>
                <div className={styles['kieli-title']}>{t('suomi')}</div>
            </div>

            {!showEnglish && (
                <div className={styles['kieli-title-container']}>
                    <div className={styles['kieli-title']}>{t('ruotsi')}</div>
                </div>
            )}

            {showEnglish && (
                <div
                    className={styles['kieli-title-container']}
                    style={{display: 'flex'}}
                >
                    <div
                        className={
                            ruotsiVaiEnglantiValittu === 'ruotsi'
                                ? styles['kieli-title']
                                : styles['kieli-title_not_selected']
                        }
                        onKeyDown={handleRuotsiKeyDown}
                        role="button"
                        tabIndex={0}
                        onClick={() => ruotsiValittu()}
                        ref={ruotsiRef}
                    >
                        {t('ruotsi')}
                    </div>
                    {showEnglish && (
                        <div
                            className={
                                ruotsiVaiEnglantiValittu === 'englanti'
                                    ? styles['kieli-title']
                                    : styles['kieli-title_not_selected']
                            }
                            onKeyDown={handleEnglantiKeyDown}
                            role="button"
                            tabIndex={0}
                            onClick={() => englantiValittu()}
                            ref={englantiRef}
                        >
                            {t('englanti')}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default LanguageTitle;
