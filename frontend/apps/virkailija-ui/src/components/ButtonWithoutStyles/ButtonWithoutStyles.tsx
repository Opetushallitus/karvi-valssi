import {CSSProperties, ReactElement} from 'react';
import styles from './button-without-styles.module.css';

interface ButtonWithoutStylesProps {
    children: ReactElement;
    onClick: () => void;
    style?: CSSProperties;
    isExpanded?: boolean;
    ariaControls: string;
}

function ButtonWithoutStyles({
    children,
    onClick,
    style,
    isExpanded = false,
    ariaControls,
}: ButtonWithoutStylesProps): ReactElement {
    return (
        <button
            onClick={() => onClick()}
            type="button"
            className={styles['button-without-styles']}
            style={style}
            aria-expanded={isExpanded ? 'true' : 'false'}
            aria-controls={ariaControls}
        >
            {children}
        </button>
    );
}

export default ButtonWithoutStyles;
