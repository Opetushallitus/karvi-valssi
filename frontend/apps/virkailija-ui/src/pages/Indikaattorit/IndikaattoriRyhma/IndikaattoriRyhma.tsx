import {useTranslation} from 'react-i18next';
import {KyselyType} from '@cscfi/shared/services/Data/Data-service';
import {ArvoKysely} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';

import {
    IndikaattoriType,
    IndikaattoriGroupType,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import ButtonWithLink from '../../../components/ButtonWithLink/ButtonWithLink';
import SinglePanelAccordion from '../../../components/SinglePanelAccordion/SinglePanelAccordion';
import IndikattoritKyselytList from '../IndikaattoriKyselytList/IndikattoritKyselytList';
import GuardedComponentWrapper, {
    ValssiUserLevel,
} from '../../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import styles from '../Indikaattorit.module.css';

interface IndikaattoriRyhmaProps {
    item: IndikaattoriGroupType;
    kyselyt: KyselyType[];
    currentUserRole: string;
    arvoKyselyt: ArvoKysely[];
}
/*
TODO
Arviointityökalut-sarakkeeseen lomakkeiden listaus oikean pääindikaattorin kohdalle.
Painikkeet näytetään vain ylläpitäjälle, lomakkeet ja tägit kaikille.
(Tägeissä eri tekstit eri käyttäjärooleille, kuten IndikaattoritKyselytList -komponentissa toteutettu,
alla olevassa esimerkissä ylläpitäjän tägit ja painikkeet)

julkaistuille:
<div className={styles['lomake-container']}>
    <div className={styles.lomake}>
        <a href="./">Moninaisuus</a>
        <span className={styles['tag-active']}>
            {t('tag-julkaistu')}
        </span>
    </div>
    <div className={styles.toiminnot}>
        <Button
            className="secondary verysmall"
            startIcon={<AssignmentIcon />}
        >
            {t('painike-katso-raportti')}
        </Button>
    </div>
</div>

julkaisemattomille:
<div className={styles['lomake-container']}>
    <div className={styles.lomake}>
        <a href="./">Lapsen kokemus</a>
        <span className={styles['tag-inactive']}>
            {t('tag-julkaisematon')}
        </span>
    </div>
    <div className={styles.toiminnot}>
        <Button
            className="secondary verysmall"
            startIcon={<EditIcon />}
        >
            {t('painike-muokkaa-lomaketta')}
        </Button>
    </div>
</div>
 */

function IndikaattoriRyhma({
    item,
    kyselyt,
    currentUserRole,
    arvoKyselyt,
}: IndikaattoriRyhmaProps) {
    const {t} = useTranslation(['indik']);
    const results: KyselyType[] = [];

    kyselyt.forEach((firstItem) => {
        item.indicators.forEach((secondItem) => {
            if (
                (firstItem.paaIndikaattori && firstItem.paaIndikaattori.key) ===
                (secondItem && secondItem.key)
            ) {
                results.push(firstItem);
            }
        });
    });
    return (
        <tr>
            <td className={styles.indikaattori}>
                <ul>
                    {item.indicators.map((indikaattori: IndikaattoriType) => (
                        <li key={indikaattori.key}>{t(indikaattori.key)}</li>
                    ))}
                </ul>
                <SinglePanelAccordion borders={false}>
                    <ul>
                        {item.indicators.map((indikaattori: IndikaattoriType) => (
                            <li key={`desc_${indikaattori.key}`}>
                                {t(`desc_${indikaattori.key}`)}
                            </li>
                        ))}
                    </ul>
                </SinglePanelAccordion>
            </td>
            <td>
                <div className={styles['right-container']}>
                    <IndikattoritKyselytList
                        kyselyt={results}
                        currentUserRole={currentUserRole}
                        arvoKyselyt={arvoKyselyt}
                    />
                    <GuardedComponentWrapper
                        allowedValssiRoles={[ValssiUserLevel.YLLAPITAJA]}
                    >
                        <div className={styles['button-container']}>
                            <ButtonWithLink
                                className="small"
                                linkTo={`/rakenna-kysely/?group=${item.group_id}`}
                                linkText={t('painike-luo-uusi-lomake', {ns: 'arvtyok'})}
                            />
                        </div>
                    </GuardedComponentWrapper>
                </div>
            </td>
        </tr>
    );
}

export default IndikaattoriRyhma;
