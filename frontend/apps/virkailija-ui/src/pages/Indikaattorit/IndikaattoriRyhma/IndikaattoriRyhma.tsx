import {useTranslation} from 'react-i18next';
import {
    KyselyType,
    PalauteKyselyIndikaattori,
    SekondaarinenIndikaattoriType,
} from '@cscfi/shared/services/Data/Data-service';
import {ArvoKysely} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import {IndikaattoriGroupType} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import LomakeTyyppi, {
    lomakeTyypitKansallisetList,
} from '@cscfi/shared/utils/LomakeTyypit';
import ButtonWithLink from '../../../components/ButtonWithLink/ButtonWithLink';
import SinglePanelAccordion from '../../../components/SinglePanelAccordion/SinglePanelAccordion';
import IndikattoritKyselytList from '../IndikaattoriKyselytList/IndikattoritKyselytList';
import GuardedComponentWrapper from '../../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import styles from '../Indikaattorit.module.css';

interface IndikaattoriRyhmaProps {
    item: IndikaattoriGroupType;
    kyselyt: KyselyType[];
    currentUserRole: string;
    arvoKyselyt: ArvoKysely[];
    emptyText?: boolean;
}

function IndikaattoriRyhma({
    item,
    kyselyt,
    currentUserRole,
    arvoKyselyt,
    emptyText = false,
}: IndikaattoriRyhmaProps) {
    const {t} = useTranslation(['indik']);
    const kansallinenRyhma = item.group_id === 3000;

    const results = kyselyt.filter((kysely) => {
        const kansallinenKysely = lomakeTyypitKansallisetList.includes(
            kysely.lomaketyyppi as LomakeTyyppi,
        );
        if (kansallinenKysely && kansallinenRyhma) return true;

        const groupKeyMatch = item.indicators
            .map((ind) => ind.key)
            .includes(kysely.paaIndikaattori.key);

        return kansallinenRyhma ? groupKeyMatch : groupKeyMatch && !kansallinenKysely;
    });

    return (
        <tr>
            <td className={styles.indikaattori}>
                <ul id={'firstList'}>
                    {!kansallinenRyhma ? (
                        item.indicators.map(
                            (indikaattori: SekondaarinenIndikaattoriType) => (
                                <li key={indikaattori.key}>{t(indikaattori.key)}</li>
                            ),
                        )
                    ) : (
                        <li key="vapaa-indikaattorivalinta">
                            {t('vapaa-indikaattorivalinta')}
                        </li>
                    )}
                </ul>
                <SinglePanelAccordion
                    borders={false}
                    specialHandlingIfChildHasNoChildren={true}
                >
                    <ul id={'secondList'}>
                        {item.indicators
                            .filter(
                                (indikaattori1) =>
                                    indikaattori1.key !== PalauteKyselyIndikaattori.key,
                            )
                            .map((indikaattori2) => (
                                <li key={`desc_${indikaattori2.key}`}>
                                    {t(`desc_${indikaattori2.key}`)}
                                </li>
                            ))}
                    </ul>
                </SinglePanelAccordion>
            </td>
            <td>
                <div className={styles['right-container']}>
                    {emptyText && results.length === 0 ? (
                        <p>{t(`ei-arviointityokaluja`)}</p>
                    ) : (
                        <IndikattoritKyselytList
                            kyselyt={results}
                            currentUserRole={currentUserRole}
                            arvoKyselyt={arvoKyselyt}
                        />
                    )}
                    <GuardedComponentWrapper roles={{arvo: [ArvoRoles.YLLAPITAJA]}}>
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
