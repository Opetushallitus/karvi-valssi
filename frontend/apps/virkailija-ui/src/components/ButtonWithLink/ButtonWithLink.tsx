import {Link} from 'react-router-dom';
import {MouseEventHandler} from 'react';

interface ButtonWithLinkProps {
    linkTo: string;
    linkText: string;
    className?: string;
    prevPath?: string;
    disabled?: boolean;
    onClick?: MouseEventHandler;
    disabledExtraText?: string;
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
    disabledExtraText,
}: ButtonWithLinkProps) {
    let styleClasses = disabled ? 'button-alike forceInline disabled ' : 'button-alike';
    if (className !== undefined) {
        styleClasses = `${styleClasses} ${className}`;
    }

    const state = {
        ...(prevPath && {prevPath}),
    };

    return disabled ? (
        <div style={{display: 'ruby'}}>
            <span
                style={{border: 'solid 1px rgba(255, 255, 255, 0)'}}
                className={styleClasses}
            >
                {linkText}
            </span>{' '}
            <span>{disabledExtraText}</span>
        </div>
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
