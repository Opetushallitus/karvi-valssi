import {act, render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import DescriptionText from './DescriptionText';

describe('<DescriptionText />', () => {
    const onChangeMock = jest.fn();
    const emptyValue = {fi: '', sv: ''};
    const desc = {fi: 'some description text here', sv: 'jag heter en description'};

    test('it should mount closed', () => {
        render(<DescriptionText value={emptyValue} onChange={onChangeMock} />);
        expect(screen.getByText(/lisaa-ohjeteksti/i)).toBeInTheDocument();
    });
    test('it should be opened when clicked', () => {
        render(<DescriptionText value={emptyValue} onChange={onChangeMock} />);
        const openButton = screen.getByText(/lisaa-ohjeteksti/i);
        expect(openButton).toBeInTheDocument();
        act(() => {
            openButton.click();
        });
        expect(screen.getAllByText(/ohjeteksti/i)[0]).toBeInTheDocument();
        expect(screen.queryByText(/lisaa-ohjeteksti/i)).not.toBeInTheDocument();
    });
    test('it should mount opened when having description text', () => {
        render(<DescriptionText value={desc} onChange={onChangeMock} />);
        expect(screen.getByDisplayValue(desc.fi)).toBeInTheDocument();
    });
});
