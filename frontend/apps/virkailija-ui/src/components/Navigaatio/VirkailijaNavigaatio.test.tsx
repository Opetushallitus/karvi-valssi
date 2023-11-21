import {render, screen} from '@testing-library/react';
import {BrowserRouter as Router} from 'react-router-dom';
import '@testing-library/jest-dom';
import VirkailijaNavigaatio from './VirkailijaNavigaatio';

describe('<Navigaatio />', () => {
    test('it should mount', () => {
        render(
            <Router>
                <VirkailijaNavigaatio />
            </Router>,
        );
        const navElement = screen.getByAltText('valssi-logo-alt-text');
        expect(navElement).toBeInTheDocument();
    });
});
