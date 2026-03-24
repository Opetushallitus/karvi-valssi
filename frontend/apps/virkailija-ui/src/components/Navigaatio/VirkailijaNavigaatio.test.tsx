import {render, screen} from '@testing-library/react';
import {BrowserRouter as Router} from 'react-router-dom';
import {describe, expect, test} from 'vitest';
import {yllapitajaUserData} from '@cscfi/shared/utils/mockData';
import VirkailijaNavigaatio from './VirkailijaNavigaatio';
import UserContext from '../../Context';

describe('<Navigaatio />', () => {
    test('it should mount', () => {
        render(
            <UserContext.Provider value={yllapitajaUserData}>
                <Router>
                    <VirkailijaNavigaatio />
                </Router>
            </UserContext.Provider>,
        );
        const navElement = screen.getByAltText('valssi-logo-alt-text');
        expect(navElement).toBeInTheDocument();
        expect(screen.getByText('Testi Käyttäjä')).toBeInTheDocument();
    });
});
