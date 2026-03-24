import {useTranslation} from 'react-i18next';
import {useParams} from 'react-router';
import styles from './SimpleError.module.css';

type SimpleErrorParams = {
    errorKey: string;
};

function SimpleError() {
    const {t, i18n} = useTranslation('yleiset');
    const {errorKey} = useParams<SimpleErrorParams>();
    const titleKey = `error-${errorKey}-title`;
    const textKey = `error-${errorKey}-text`;
    const linkKey = `error-${errorKey}-link`;
    const link = t(linkKey).startsWith('http') ? t(linkKey) : `http://${t(linkKey)}`;
    return (
        <div className={styles.SimpleError} data-testid="SimpleError">
            {i18n.exists(titleKey, {ns: 'yleiset'}) ? <h1>{t(titleKey)}</h1> : null}
            <div>
                {i18n.exists(linkKey, {ns: 'yleiset'}) ? (
                    <>
                        {t(textKey)}
                        {errorKey === 'ei-oikeuksia' && (
                            <a href={link} target="_blank" rel="noreferrer">
                                {t('error-ei-oikeuksia-link-text')}
                            </a>
                        )}
                        {errorKey === 'ei-oikeuksia' && (
                            <>
                                <div>&nbsp;</div>
                                <div>
                                    {t('error-ei-oikeuksia-extra')}
                                    <a
                                        href={'https://virkailija.opintopolku.fi'}
                                        target="_blank"
                                        rel=" noreferrer"
                                    >
                                        https://virkailija.opintopolku.fi
                                    </a>
                                </div>
                            </>
                        )}
                        <div>&nbsp;</div>
                        {errorKey !== 'ei-oikeuksia' && (
                            <a href={link} target="_blank" rel="noreferrer">
                                {t('avaa-ohje')}
                            </a>
                        )}
                    </>
                ) : (
                    <>{t(textKey, t('error-tuntematon-text'))}</>
                )}
            </div>
        </div>
    );
}

export default SimpleError;
