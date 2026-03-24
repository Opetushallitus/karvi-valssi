import {useEffect, useMemo, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {notEmpty} from '../../utils/helpers';
import styles from './ViewIndicators.module.css';

type GenericIndikaattori = {
    key: string;
    group?: number;
    group_id?: number;
    laatutekija?: string;
};

export const strToIndicator = (
    indicatorStr?: string,
): GenericIndikaattori | undefined => {
    if (indicatorStr && indicatorStr !== '') {
        return {key: indicatorStr, group: undefined};
    }
    return undefined;
};

export const strArrToindicatorArr = (
    indicatorStrArr?: string[],
): GenericIndikaattori[] =>
    indicatorStrArr
        ? indicatorStrArr.map((ind) => strToIndicator(ind)).filter(notEmpty)
        : [];

interface ViewindicatorsProps {
    paaindikaattori?: GenericIndikaattori;
    muutIndikaattorit?: GenericIndikaattori[];
    language?: string;
}

function ViewIndicators({
    paaindikaattori,
    muutIndikaattorit,
    language,
}: ViewindicatorsProps) {
    const {i18n} = useTranslation('indik');

    const [langKey, setLangKey] = useState<string>(language ?? i18n.language);

    useEffect(() => {
        setLangKey(language);
    }, [language]);

    useEffect(() => {
        setLangKey(i18n.language);
    }, [i18n.language]);

    const fixedT = useMemo(() => i18n.getFixedT(langKey, 'indik'), [langKey, i18n]);

    if (!paaindikaattori) return null;

    return (
        <div className={styles['indicators-box']}>
            <p>{fixedT('otsikko')}</p>
            <ul>
                <li>{fixedT(`desc_${paaindikaattori.key}`)}</li>
                {muutIndikaattorit &&
                    muutIndikaattorit.map((mi) => (
                        <li key={mi.key}>{fixedT(`desc_${mi.key}`)}</li>
                    ))}
            </ul>
        </div>
    );
}

export default ViewIndicators;
