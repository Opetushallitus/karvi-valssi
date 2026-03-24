import {of} from 'rxjs';
import {describe, expect, vi, it, beforeEach} from 'vitest';
import {render, screen} from '@testing-library/react';
import {paakayttajaUserData} from '@cscfi/shared/utils/mockData';
import {MemoryRouter, Route, Routes} from 'react-router-dom';
import UserContext from '../../../Context';
import {aluejakoData} from '../../../utils/mockData';
import MuokkaaAluetta from './MuokkaaAluetta';

describe('<MuokkaaAluetta />', () => {
    beforeEach(() => {
        vi.mock(
            '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service',
            async (importOriginal) => ({
                ...((await importOriginal()) as object),
                virkailijapalveluGetAluejako$: () => () => of(aluejakoData),
            }),
        );
    });

    it('should render appropriate items when creating a new group', () => {
        render(
            <UserContext.Provider value={paakayttajaUserData}>
                <MemoryRouter>
                    <MuokkaaAluetta />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        expect(screen.queryByText('ol5')).not.toBeNull();
        expect(screen.queryByText('ol2')).toBeNull();
        expect(screen.queryByText('ol4')).toBeNull();
    });

    it('should render appropriate items when modifying an existing group', () => {
        render(
            <UserContext.Provider value={paakayttajaUserData}>
                <MemoryRouter initialEntries={['/muokkaa/11']}>
                    <Routes>
                        <Route path="muokkaa/:alueId" element={<MuokkaaAluetta />} />
                    </Routes>
                </MemoryRouter>
            </UserContext.Provider>,
        );

        expect(screen.queryByText('ol5')).not.toBeNull();
        expect(screen.queryByText('ol2')).not.toBeNull();
        expect(screen.queryByText('ol4')).not.toBeNull();
    });
});
