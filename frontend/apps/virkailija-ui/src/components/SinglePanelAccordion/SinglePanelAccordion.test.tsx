import {act, render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import SinglePanelAccordion from './SinglePanelAccordion';

describe('<SinglePanelAccordion />', () => {
    test('it should mount', () => {
        render(
            <SinglePanelAccordion title="Title">
                <div>Content</div>
            </SinglePanelAccordion>,
        );

        const openBtn = screen.getByText(/Avaa/i);
        expect(openBtn).toBeInTheDocument();

        act(() => {
            openBtn.click();
        });

        const closeBtn = screen.getByText(/Sulje/i);
        expect(closeBtn).toBeInTheDocument();
    });
});
