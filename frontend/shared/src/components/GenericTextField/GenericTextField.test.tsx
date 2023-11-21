import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import GenericTextField from './GenericTextField';

describe('<GenericTextField />', () => {
    test('it should mount', () => {
        const handleChangeMock = jest.fn();
        render(
            <GenericTextField
                value="kysymys1"
                label="Otsikko"
                showLabel
                onChange={handleChangeMock}
            />,
        );
        const teksti = screen.getByText(/Otsikko/i);
        expect(teksti).toBeInTheDocument();
        const title = screen.getByDisplayValue('kysymys1');
        expect(title).toBeInTheDocument();
    });
});
