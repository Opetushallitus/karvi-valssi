import {ReactNode} from 'react';
import {useObservableState} from 'observable-hooks';
import {
    AllowedRole,
    hasRequiredRole,
    userKayttooikeudet$,
} from '@cscfi/shared/services/Login/Login-service';

interface GuardedComponentWrapperProps {
    roles: AllowedRole;
    children: ReactNode;
}

function GuardedComponentWrapper({roles, children}: GuardedComponentWrapperProps) {
    const [userRoles] = useObservableState(() => userKayttooikeudet$, null);
    if (hasRequiredRole(roles, userRoles)) {
        return children;
    }
    return null;
}

export default GuardedComponentWrapper;
