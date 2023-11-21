import {useContext} from 'react';
import {useObservable} from 'rxjs-hooks';
import {raportiointipalveluGetKyselyDataCollection$} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import UserContext from '../../Context';
import KyselyList from './KyselyList';

function TiedonkeruuToteuttaja() {
    const userInfo = useContext(UserContext);
    const kyselyt = useObservable(
        () =>
            raportiointipalveluGetKyselyDataCollection$(userInfo!)(
                userInfo!.rooli.kayttooikeus,
            ),
        null,
    );
    return (
        <div>
            <KyselyList kyselyt={kyselyt} />
        </div>
    );
}

export default TiedonkeruuToteuttaja;
