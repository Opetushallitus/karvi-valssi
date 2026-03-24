import {render, screen} from '@testing-library/react';
import {describe, test, expect} from 'vitest';
import {BrowserRouter as Router} from 'react-router-dom';
import ButtonWithLink from './ButtonWithLink';

describe('<ButtonWithLink />', () => {
    test('it should mount', () => {
        render(
            <Router>
                <ButtonWithLink linkTo="somewhere" linkText="Test Link" />
            </Router>,
        );
        const buttonWithLink = screen.getByText('Test Link');
        expect(buttonWithLink).toBeInTheDocument();
    });
});
