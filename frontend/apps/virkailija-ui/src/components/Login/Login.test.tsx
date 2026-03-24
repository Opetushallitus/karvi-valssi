import {render, screen} from '@testing-library/react';
import {describe, expect, test, vi} from 'vitest';
import Login from './Login';

vi.mock('react-router-dom', async () => ({
    ...(await vi.importActual<Location>('react-router-dom')),
    useLocation: () => ({
        search: '?redirect=/',
    }),
}));

describe('<Login />', () => {
    test('it should mount', async () => {
        render(<Login />);
        const login = await screen.findByTestId('Login');
        expect(login).toBeInTheDocument();
    });
});
