import {ReactElement, useMemo} from 'react';
import {useObservableState} from 'observable-hooks';
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
    const [userKayttooikeudet] = useObservableState(() => userKayttooikeudet$, null);
    const isRole = useMemo(
        () => hasRequiredRole(roles, userKayttooikeudet),
        [roles, userKayttooikeudet],
    );
    return isRole ? children : null;
}

export default GuardedNavigaatio;
