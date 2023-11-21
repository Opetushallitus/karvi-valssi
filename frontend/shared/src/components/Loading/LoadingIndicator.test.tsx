import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import LoadingIndicator from './LoadingIndicator';

describe('<LoadingIndicator />', () => {
    test('it should mount', () => {
        render(<LoadingIndicator alwaysLoading />);
        const loading = screen.getByTestId('LoadingIndicator');

        expect(loading).toBeInTheDocument();
    });
});
