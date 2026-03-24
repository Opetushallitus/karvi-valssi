import {render, screen} from '@testing-library/react';
import {describe, test, expect} from 'vitest';
import TemplateName from './TemplateName';

describe('<TemplateName />', () => {
    test('it should mount', () => {
        render(<TemplateName />);

        const templateName = screen.getByTestId('TemplateName');

        expect(templateName).toBeInTheDocument();
    });
});
