import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
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
