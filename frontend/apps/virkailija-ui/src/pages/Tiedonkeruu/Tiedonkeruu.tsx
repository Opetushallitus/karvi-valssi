import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import Toteuttaja from './TiedonkeruuToteuttaja';
import Paakayttaja from './TiedonkeruuPaakayttaja';
import Yllapitaja from './TiedonkeruuYllapitaja';
import GuardedComponentWrapper from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';

function Tiedonkeruu() {
    return (
        <>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.TOTEUTTAJA]}}>
                <Toteuttaja />
            </GuardedComponentWrapper>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.PAAKAYTTAJA]}}>
                <Paakayttaja />
            </GuardedComponentWrapper>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.YLLAPITAJA]}}>
                <Yllapitaja />
            </GuardedComponentWrapper>
        </>
    );
}
export default Tiedonkeruu;
