import {useTranslation} from 'react-i18next';
import styles from '@cscfi/shared/components/Navigaatio/Navigaatio.module.css';
import karviLogo_fi from '@cscfi/shared/components/Navigaatio/KARVI_long_logo.png';
import karviLogo_sv from '@cscfi/shared/components/Navigaatio/NCU_long_logo.png';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import AlatunnisteLink from '@cscfi/shared/components/Navigaatio/AlatunnisteLink';

export default function VirkailijaAlatunniste() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['ulkoasu']);
    const langKey = lang as keyof TextType;

    return (
        <footer>
            <div className={styles.footer}>
                <a
                    href="https://karvi.fi"
                    className={styles.footerLogo}
                    target="_blank"
                    rel="noreferrer"
                >
                    <img
                        src={langKey !== 'sv' ? karviLogo_fi : karviLogo_sv}
                        alt={t('karvi-logo-alt-text', {ns: 'yleiset'})}
                        height="75"
                    />
                </a>
                <div className={styles.footerLinks}>
                    <ul>
                        <li>
                            <AlatunnisteLink
                                urlKey="siirry-karvin-sivuille-url"
                                textKey="siirry-karvin-sivuille"
                            />
                        </li>
                        <li>
                            <AlatunnisteLink
                                urlKey="kayttoohjeet-ja-tuki-url"
                                textKey="kayttoohjeet-ja-tuki"
                            />
                        </li>
                    </ul>
                    <ul>
                        <li>
                            <AlatunnisteLink
                                urlKey="tietosuojaseloste-url"
                                textKey="tietosuojaseloste"
                            />
                        </li>
                        <li>
                            <AlatunnisteLink
                                urlKey="saavutettavuusseloste-url"
                                textKey="saavutettavuusseloste"
                            />
                        </li>
                    </ul>
                </div>
            </div>
        </footer>
    );
}
