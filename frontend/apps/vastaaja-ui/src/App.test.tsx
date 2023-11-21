import {render, screen} from '@testing-library/react';
import App from './App';

test('renders Vastaaja App with Valssi header', async () => {
    render(<App />);
    // Inside <Logo />
    const navElement = await screen.findByAltText(/valssi-logo-alt-text/i);
    expect(navElement).toBeInTheDocument();
});
