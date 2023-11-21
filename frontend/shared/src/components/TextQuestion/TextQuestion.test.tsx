import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import TextQuestion from './TextQuestion';

describe('<TextQuestion />', () => {
    const handleChangeMock = jest.fn();
    test('it should mount', () => {
        render(
            <TextQuestion
                title={{fi: 'kysymys1', sv: 'fråga1'}}
                description={{fi: 'kuvausteksti1', sv: 'hjelppamej1'}}
                handleChange={handleChangeMock}
            />,
        );
        const title = screen.getByDisplayValue('kysymys1');
        expect(title).toBeInTheDocument();
    });
    test('it should contain description field', () => {
        render(
            <TextQuestion
                title={{fi: 'kysymys2', sv: 'fråga2'}}
                description={{fi: 'kuvausteksti2', sv: 'hjelppamej2'}}
                handleChange={handleChangeMock}
            />,
        );
        const title = screen.getByDisplayValue('kysymys2');
        expect(title).toBeInTheDocument();
        const desc = screen.getByDisplayValue('kuvausteksti2');
        expect(desc).toBeInTheDocument();
    });
});
