import {getI18n} from 'react-i18next';
import {
    MatrixQuestionScaleType,
    KysymysType,
} from '@cscfi/shared/services/Data/Data-service';
import BgColorStyles from '@cscfi/shared/components/Chart/styles.module.css';

import styles from './raportit.module.css';

interface RenderScaleProps {
    item: KysymysType;
    scale?: Array<MatrixQuestionScaleType>;
}

function RenderScales({item, scale}: RenderScaleProps) {
    const locale = getI18n().language;
    return (
        <ul className={styles['scale-list']} aria-hidden="true">
            {item.matrix_question_scale?.map((childItem, i: number) => {
                const langKey = locale as keyof MatrixQuestionScaleType;
                return (
                    <li key={`key_${Math.random()}`}>
                        <p>{childItem[langKey]?.toString()}</p>
                        <span
                            className={
                                BgColorStyles[
                                    `item-${i}-range-${scale && scale[0]?.value}-${
                                        scale && scale[scale.length - 1]?.value
                                    }`
                                ]
                            }
                        />
                    </li>
                );
            })}
        </ul>
    );
}

export default RenderScales;
