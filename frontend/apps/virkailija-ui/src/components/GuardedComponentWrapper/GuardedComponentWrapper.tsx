import {ReactNode, useContext} from 'react';
import UserContext from '../../Context';

export enum ValssiUserLevel {
    YLLAPITAJA = 'YLLAPITAJA',
    PAAKAYTTAJA = 'PAAKAYTTAJA',
    TOTEUTTAJA = 'TOTEUTTAJA',
}

interface GuardedComponentWrapperProps {
    allowedValssiRoles: Array<String>;
    children: ReactNode;
}

/*
 * Simply check that the current user is allowed to see the component, e.g. a button for publishing
 * */
function GuardedComponentWrapper({
    allowedValssiRoles,
    children,
}: GuardedComponentWrapperProps) {
    const userInfo = useContext(UserContext);
    const currentUserRole = userInfo?.rooli.kayttooikeus;

    if (currentUserRole && allowedValssiRoles.includes(currentUserRole)) {
        // eslint-disable-next-line react/jsx-no-useless-fragment
        return <>{children}</>;
    }
    return null;
}

export default GuardedComponentWrapper;
