import {of} from 'rxjs';
import {describe, expect, vi, it, beforeEach} from 'vitest';
import {render} from '@testing-library/react';
import {paakayttajaUserData} from '@cscfi/shared/utils/mockData';
import {MemoryRouter} from 'react-router-dom';
import UserContext from '../../Context';
import {aluejakoData} from '../../utils/mockData';
import Aluejako from './Aluejako';

describe('<Aluejako />', () => {
    beforeEach(() => {
        vi.mock(
            '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service',
            async (importOriginal) => ({
                ...((await importOriginal()) as object),
                virkailijapalveluGetAluejako$: () => () => of(aluejakoData),
            }),
        );
    });

    it('Groups should render separate lists', () => {
        render(
            <UserContext.Provider value={paakayttajaUserData}>
                <MemoryRouter>
                    <Aluejako />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        const groupLabels = document.getElementsByTagName('legend');

        // Check group names from labels
        expect(groupLabels.item(0)?.innerHTML).to.equal(aluejakoData.grouped[0].name.fi);
        expect(groupLabels.item(1)?.innerHTML).to.equal(aluejakoData.grouped[1].name.fi);

        const fieldSets = document.getElementsByTagName('fieldset');

        // Check oppilaitos names
        expect(
            fieldSets[0].children[1].getElementsByTagName('span')[2].innerHTML,
        ).to.equal(aluejakoData.grouped[0].oppilaitokset[1].name.fi);
        expect(
            fieldSets[1].children[1].getElementsByTagName('span')[2].innerHTML,
        ).to.equal(aluejakoData.grouped[1].oppilaitokset[1].name.fi);
    });
});
