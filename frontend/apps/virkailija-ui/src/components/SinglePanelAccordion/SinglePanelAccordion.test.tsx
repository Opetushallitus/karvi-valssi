import {act, render, screen} from '@testing-library/react';
import {describe, test, expect} from 'vitest';
import SinglePanelAccordion from './SinglePanelAccordion';

describe('<SinglePanelAccordion />', () => {
    test('it should mount', async () => {
        render(
            <SinglePanelAccordion title="Title">
                <div>Content</div>
            </SinglePanelAccordion>,
        );

        const title = await screen.findByText(/Title/i);
        expect(title).toBeInTheDocument();

        const openBtn = screen.getByTestId(/Avaa/i);
        expect(openBtn).toBeInTheDocument();

        act(() => {
            openBtn.click();
        });

        const content = await screen.findByText(/Content/i);
        expect(content).toBeInTheDocument();

        const closeBtn = screen.getByText(/Sulje/i);
        expect(closeBtn).toBeInTheDocument();
    });
});
