import {render} from '@testing-library/react';
import {describe, expect, vi, it} from 'vitest';
import MultipleChoiceChart from './MultipleChoiceChart';
import {monivalintaRaporttiData} from '../../../utils/mockData';

describe('<MultipleChoiceChart />', async () => {
    // Mock the ResizeObserver
    const ResizeObserverMock = vi.fn(() => ({
        observe: vi.fn(),
        unobserve: vi.fn(),
        disconnect: vi.fn(),
    }));

    // Stub the global ResizeObserver
    vi.stubGlobal('ResizeObserver', ResizeObserverMock);

    it('it should render a chart of correct length', () => {
        const {container} = render(
            <MultipleChoiceChart
                questions={monivalintaRaporttiData.questions}
                answers={monivalintaRaporttiData.answers}
                multipleSelect={false}
            />,
        );
        const firstDiv = container.querySelector('div');
        // 1 span + 3 divs for each question + 1 div for x-axis labels
        expect(firstDiv?.parentElement?.children.length).toEqual(5);
    });
});
