import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import Login from './Login';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual<Location>('react-router-dom'),
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
