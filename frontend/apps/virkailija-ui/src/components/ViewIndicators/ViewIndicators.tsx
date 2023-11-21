import {useTranslation} from 'react-i18next';
import {Indikaattori} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {notEmpty} from '@cscfi/shared/utils/helpers';
import styles from './ViewIndicators.module.css';

export const strToIndicator = (indicatorStr?: string): Indikaattori | undefined => {
    if (indicatorStr && indicatorStr !== '') {
        return {key: indicatorStr, group: undefined};
    }
    return undefined;
};

export const strArrToindicatorArr = (indicatorStrArr?: string[]): Indikaattori[] =>
    indicatorStrArr
        ? indicatorStrArr.map((ind) => strToIndicator(ind)).filter(notEmpty)
        : [];

interface ViewindicatorsProps {
    paaindikaattori?: Indikaattori;
    muutIndikaattorit?: Indikaattori[];
}

function ViewIndicators({paaindikaattori, muutIndikaattorit}: ViewindicatorsProps) {
    const {t} = useTranslation(['kysely']);
    return paaindikaattori ? (
        <div className={styles['indicators-box']}>
            <ul>
                <li>{`${t('paa-indikaattori', {ns: 'indik'})}: ${t(
                    `desc_${paaindikaattori.key}`,
                    {
                        ns: 'indik',
                    },
                )}`}</li>
                {muutIndikaattorit && muutIndikaattorit.length > 0 && (
                    <li>
                        {`${t('muut-indikaattorit', {
                            ns: 'indik',
                        })}: ${muutIndikaattorit
                            .map((indikaattori) =>
                                t(`desc_${indikaattori.key}`, {ns: 'indik'}),
                            )
                            .join(', ')}`}
                    </li>
                )}
            </ul>
        </div>
    ) : null;
}

export default ViewIndicators;
