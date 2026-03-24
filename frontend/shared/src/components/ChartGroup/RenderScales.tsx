import {useEffect, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {
    MatrixQuestionScaleType,
    KysymysType,
} from '@cscfi/shared/services/Data/Data-service';
import BgColorStyles from '@cscfi/shared/components/Chart/styles.module.css';

import styles from './styles.module.css';

interface RenderScaleProps {
    item: KysymysType;
    scale?: Array<MatrixQuestionScaleType>;
    language?: string;
}

function RenderScales({item, scale, language}: RenderScaleProps) {
    const {i18n} = useTranslation();

    const [langKey, setLangKey] = useState<string>(language ?? i18n.language);

    useEffect(() => {
        setLangKey(language);
    }, [language]);

    useEffect(() => {
        setLangKey(i18n.language);
    }, [i18n.language]);

    return (
        <ul className={styles['scale-list']} aria-hidden="true">
            {item.matrix_question_scale?.map((childItem, i: number) => {
                return (
                    <li
                        key={`key_${
                            childItem.fi +
                            '_' +
                            childItem.sv +
                            '_' +
                            childItem.value +
                            '_' +
                            i
                        }`}
                    >
                        <span
                            className={
                                BgColorStyles[
                                    `item-${i}-range-${scale && scale[0]?.value}-${
                                        scale && scale[scale.length - 1]?.value
                                    }`
                                ]
                            }
                        />
                        <p>{childItem[langKey]?.toString()}</p>
                    </li>
                );
            })}
        </ul>
    );
}

export default RenderScales;
