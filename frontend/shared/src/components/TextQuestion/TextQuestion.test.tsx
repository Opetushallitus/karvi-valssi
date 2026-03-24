import {render, screen} from '@testing-library/react';
import {describe, expect, vi, it} from 'vitest';
import TextQuestion from './TextQuestion';

describe('<TextQuestion />', () => {
    const handleChangeMock = vi.fn();
    it('it should mount', () => {
        render(
            <TextQuestion
                title={{fi: 'kysymys1', sv: 'fråga1'}}
                description={{fi: 'kuvausteksti1', sv: 'hjelppamej1'}}
                handleChange={handleChangeMock()}
                showEnglish={false}
                ruotsiVaiEnglantiValittu={'ruotsi'}
                setRuotsiVaiEnglantiValittu={null}
            />,
        );
        const title = screen.getByDisplayValue('kysymys1');
        expect(title).toBeInTheDocument();
    });
    it('it should contain description field', () => {
        render(
            <TextQuestion
                title={{fi: 'kysymys2', sv: 'fråga2'}}
                description={{fi: 'kuvausteksti2', sv: 'hjelppamej2'}}
                handleChange={handleChangeMock()}
                showEnglish={false}
                ruotsiVaiEnglantiValittu={'ruotsi'}
                setRuotsiVaiEnglantiValittu={null}
            />,
        );
        const title = screen.getByDisplayValue('kysymys2');
        expect(title).toBeInTheDocument();
        const desc = screen.getByDisplayValue('kuvausteksti2');
        expect(desc).toBeInTheDocument();
    });
});
