import {Trans, useTranslation} from 'react-i18next';
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
                    <Trans
                        i18nKey={textKey}
                        ns="yleiset"
                        defaultValue={t('error-tuntematon-text')}
                    >
                        My error text&nbsp;
                        <a href={link} target="_blank" rel="noreferrer">
                            link text
                        </a>
                    </Trans>
                ) : (
                    <>{t(textKey, t('error-tuntematon-text'))}</>
                )}
            </div>
        </div>
    );
}

export default SimpleError;
