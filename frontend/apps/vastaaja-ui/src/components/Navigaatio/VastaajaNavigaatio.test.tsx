import {describe, test, expect} from 'vitest';
import {render, screen} from '@testing-library/react';
import {BrowserRouter as Router} from 'react-router-dom';
import VastaajaNavigaatio from './VastaajaNavigaatio';

describe('<Navigaatio />', () => {
    test('it should mount', () => {
        render(
            <Router>
                <VastaajaNavigaatio />
            </Router>,
        );
        const navElement = screen.getByAltText('valssi-logo-alt-text');
        expect(navElement).toBeInTheDocument();
    });
});
