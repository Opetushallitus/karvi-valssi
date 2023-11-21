import Toteuttaja from './TiedonkeruuToteuttaja';
import Paakayttaja from './TiedonkeruuPaakayttaja';
import Yllapitaja from './TiedonkeruuYllapitaja';

import GuardedComponentWrapper, {
    ValssiUserLevel,
} from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';

function Tiedonkeruu() {
    return (
        <>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.TOTEUTTAJA]}>
                <Toteuttaja />
            </GuardedComponentWrapper>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.PAAKAYTTAJA]}>
                <Paakayttaja />
            </GuardedComponentWrapper>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.YLLAPITAJA]}>
                <Yllapitaja />
            </GuardedComponentWrapper>
        </>
    );
}
export default Tiedonkeruu;
