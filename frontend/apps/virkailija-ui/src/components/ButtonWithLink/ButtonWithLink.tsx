import {Link} from 'react-router-dom';
import {MouseEventHandler} from 'react';

interface ButtonWithLinkProps {
    linkTo: string;
    linkText: string;
    className?: string;
    prevPath?: string;
    disabled?: boolean;
    onClick?: MouseEventHandler;
}

/*
 * If you want a small button-looking link, use
 * className="small"
 */

function ButtonWithLink({
    linkTo = '/#',
    linkText,
    className,
    prevPath,
    disabled,
    onClick,
}: ButtonWithLinkProps) {
    let styleClasses = disabled ? 'button-alike disabled' : 'button-alike';
    if (className !== undefined) {
        styleClasses = `${styleClasses} ${className}`;
    }

    const state = {
        ...(prevPath && {prevPath}),
    };

    return disabled ? (
        <span className={styleClasses}>{linkText}</span>
    ) : (
        <Link
            to={linkTo}
            className={styleClasses}
            state={state}
            role="button"
            onClick={onClick}
        >
            {linkText}
        </Link>
    );
}

export default ButtonWithLink;
