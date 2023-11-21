import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import {MemoryRouter, Route, Routes} from 'react-router-dom';
import {allowedRoles} from '@cscfi/shared/services/Login/Login-service';
import {GuardedRoute} from './GuardedRoute';

describe('<GuardedRoute />', () => {
    test('it should mount', () => {
        render(
            <MemoryRouter>
                <Routes>
                    <Route
                        element={
                            <GuardedRoute roles={allowedRoles.etusivu}>
                                <h1>something</h1>
                            </GuardedRoute>
                        }
                    />
                </Routes>
            </MemoryRouter>,
        );

        const guardedRoute = screen.queryByText('something');

        expect(guardedRoute).not.toBeInTheDocument();
    });
});
