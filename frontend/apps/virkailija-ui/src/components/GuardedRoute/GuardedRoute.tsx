import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {ReactElement} from 'react';
import {Navigate} from 'react-router';
import {useLocation} from 'react-router-dom';
import {useObservableState} from 'observable-hooks';
import {
    AllowedRole,
    hasRequiredRole,
    isLoggedIn$,
    userKayttooikeudet$,
    virkailijaPermissionOk$,
} from '@cscfi/shared/services/Login/Login-service';

interface GuardedRouteProps {
    roles: AllowedRole;
    children: ReactElement;
}

export function GuardedRoute({roles, children}: GuardedRouteProps) {
    const {pathname} = useLocation();
    const [loggedIn] = useObservableState(() => isLoggedIn$());
    const [userRoles] = useObservableState(() => userKayttooikeudet$);

    const [permissionOk] = useObservableState(() => virkailijaPermissionOk$);

    if (loggedIn?.isLoggedIn === false) {
        const redirectPath = `/login?redirect=${pathname}`;
        return <Navigate to={redirectPath} replace />;
    }

    if (loggedIn?.isLoggedIn === true) {
        if (permissionOk === false) {
            return <Navigate to="/error/ei-oikeuksia" replace />;
        }
        if (permissionOk === undefined) {
            return null;
        }
    }

    if (loggedIn?.isLoggedIn === true && userRoles) {
        if (hasRequiredRole(roles, userRoles)) {
            return children;
        }
        const alert = {
            title: {key: 'invalid-permissions-title', ns: 'guard'},
            severity: 'error',
            body: {key: 'invalid-permissions-body', ns: 'guard'},
        } as AlertType;
        AlertService.showAlert(alert);
        return <Navigate to="/" replace />;
    }
    if (loggedIn?.error) {
        return <Navigate to={`/error/${loggedIn!.error}`} replace />;
    }
    return null;
}

export default GuardedRoute;
