import {ReactElement} from 'react';
import styles from './button-without-styles.module.css';

interface ButtonWithoutStylesProps {
    children: ReactElement;
    onClick?: React.ButtonHTMLAttributes<HTMLButtonElement>['onClick'];
    style?: React.CSSProperties;
}

function ButtonWithoutStyles({children, onClick, style}: ButtonWithoutStylesProps) {
    return (
        <button
            onClick={onClick}
            type="button"
            className={styles['button-without-styles']}
            style={style}
        >
            {children}
        </button>
    );
}

export default ButtonWithoutStyles;
