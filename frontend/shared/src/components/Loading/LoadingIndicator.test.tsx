import {describe, test, expect} from 'vitest';
import {render, screen} from '@testing-library/react';
import LoadingIndicator from './LoadingIndicator';

describe('<LoadingIndicator />', () => {
    test('it should mount', () => {
        render(<LoadingIndicator alwaysLoading />);
        const loading = screen.getByTestId('LoadingIndicator');

        expect(loading).toBeInTheDocument();
    });
});
