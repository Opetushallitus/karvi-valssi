import React, {useRef, useEffect, ReactElement} from 'react';
import styles from './FocusableHeader.module.css';

interface FocusableHeaderProps {
    level?: 1 | 2 | 3 | 4 | 5 | 6;
    children: ReactElement;
    className?: string;
}

function FocusableHeader({children, level = 1, className = ''}: FocusableHeaderProps) {
    const titleHeaderRef = useRef<null | HTMLHeadingElement>(null);
    useEffect(() => {
        if (titleHeaderRef.current !== null) {
            titleHeaderRef.current?.setAttribute('tabIndex', '-1');
            titleHeaderRef.current?.focus();
            // titleHeaderRef.current?.blur();
            // titleHeaderRef.current?.removeAttribute('tabIndex');
        }
    }, []);

    return React.createElement(
        `h${level}`,
        {className: `${styles.focusableHeader} ${className}`},
        children,
    );
}

export default FocusableHeader;
