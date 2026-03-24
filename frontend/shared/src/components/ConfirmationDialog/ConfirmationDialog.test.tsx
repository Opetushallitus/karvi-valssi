import {describe, test, expect} from 'vitest';
import {act, render, screen} from '@testing-library/react';
import ConfirmationDialog from './ConfirmationDialog';

describe('<ConfirmationDialog />', () => {
    test('it should mount', () => {
        render(
            <ConfirmationDialog confirm={() => 1 + 2} title="Confirm title">
                <button type="button">Needs to be confirmed</button>
            </ConfirmationDialog>,
        );

        const confirtmBtn = screen.getByText(/Needs to be confirmed/i);
        expect(confirtmBtn).toBeInTheDocument();

        act(() => {
            confirtmBtn.click();
        });

        const dialogcConfirmBtn = screen.getByText(/Confirm title/i, {
            selector: 'button',
        });
        expect(dialogcConfirmBtn).toBeInTheDocument();

        const dialogCancelBtn = screen.getByText(/Peruuta/i, {selector: 'button'});
        expect(dialogCancelBtn).toBeInTheDocument();
    });
});
