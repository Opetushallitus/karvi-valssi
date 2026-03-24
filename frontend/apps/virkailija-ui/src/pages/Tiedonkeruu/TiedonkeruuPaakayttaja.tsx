import {useContext} from 'react';
import {useObservableState} from 'observable-hooks';
import {raportiointipalveluGetKyselyDataCollection$} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import UserContext from '../../Context';
import KyselyList from './KyselyList';

function TiedonkeruuPaakayttaja() {
    const userInfo = useContext(UserContext);
    const [kyselyt] = useObservableState(
        () =>
            raportiointipalveluGetKyselyDataCollection$(userInfo!)(
                userInfo!.rooli.kayttooikeus,
                userInfo!.rooli.organisaatio,
            ),
        null,
    );
    return (
        <div>
            <KyselyList kyselyt={kyselyt} />
        </div>
    );
}

export default TiedonkeruuPaakayttaja;
