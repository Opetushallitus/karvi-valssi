import {ReactElement, useMemo} from 'react';
import {useObservable} from 'rxjs-hooks';
import {NavLinkProps} from 'react-router-dom';
import {
    AllowedRole,
    hasRequiredRole,
    userKayttooikeudet$,
} from '@cscfi/shared/services/Login/Login-service';

interface GuardedNavigationProps {
    roles: AllowedRole;
    children: ReactElement<NavLinkProps>;
}

function GuardedNavigaatio({roles, children}: GuardedNavigationProps) {
    const userKayttooikeudet = useObservable(() => userKayttooikeudet$);
    const isRole = useMemo(
        () => hasRequiredRole(roles, userKayttooikeudet),
        [roles, userKayttooikeudet],
    );
    return isRole ? children : null;
}

export default GuardedNavigaatio;
