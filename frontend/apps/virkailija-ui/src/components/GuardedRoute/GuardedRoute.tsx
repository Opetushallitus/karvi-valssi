import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {ReactElement} from 'react';
import {Navigate} from 'react-router';
import {useLocation} from 'react-router-dom';
import {useObservable} from 'rxjs-hooks';
import {
    AllowedRole,
    hasRequiredRole,
    isLoggedIn$,
    userKayttooikeudet$,
} from '@cscfi/shared/services/Login/Login-service';

interface GuardedRouteProps {
    roles: AllowedRole;
    children: ReactElement;
}

export function GuardedRoute({roles, children}: GuardedRouteProps) {
    const allowedRoles = roles;
    const {pathname} = useLocation();
    const loggedIn = useObservable(() => isLoggedIn$());
    const userRoles = useObservable(() => userKayttooikeudet$);
    if (loggedIn?.isLoggedIn === false) {
        const redirectPath = `/login?redirect=${pathname}`;
        return <Navigate to={redirectPath} replace />;
    }
    if (loggedIn?.isLoggedIn === true && userRoles) {
        if (hasRequiredRole(allowedRoles, userRoles)) {
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
