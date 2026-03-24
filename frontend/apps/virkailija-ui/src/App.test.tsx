import {render, screen} from '@testing-library/react';
import {test, expect} from 'vitest';
import App from './App';

test('renders Virkailija App with Valssi header', async () => {
    render(<App />);
    // Inside <Logo />
    const navElement = await screen.findByAltText(/valssi-logo-alt-text/i);
    expect(navElement).toBeInTheDocument();
});
