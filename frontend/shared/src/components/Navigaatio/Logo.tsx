import {useTranslation} from 'react-i18next';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import valssilogo_fi from './Valssi_logo_ja_teksti_suomi_rgb.png';
import valssilogo_sv from './Valssi_logo_ja_teksti_svenska_rgb.png';
import styles from './Navigaatio.module.css';

function Logo() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['ulkoasu']);

    const valssilogo = (lang as keyof TextType) === 'sv' ? valssilogo_sv : valssilogo_fi;

    return (
        <div className={styles.header_title}>
            <img
                src={valssilogo}
                className={styles.logo_img}
                alt={t('valssi-logo-alt-text')}
                height="80"
            />
        </div>
    );
}

export default Logo;
