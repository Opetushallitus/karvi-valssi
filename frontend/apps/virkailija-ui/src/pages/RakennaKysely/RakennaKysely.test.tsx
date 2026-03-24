import {of} from 'rxjs';
import {MemoryRouter} from 'react-router-dom';
import {render, screen} from '@testing-library/react';
import {test, describe, expect, vi} from 'vitest';
import {kysymysryhmaData} from '@cscfi/shared/utils/mockData';
import {convertKysymysRyhmaToValssi} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import RakennaKysely from './RakennaKysely';

describe('<RakennaKysely />', () => {
    test('it should open in creation mode', () => {
        render(
            <MemoryRouter initialEntries={['?group=1000']}>
                <RakennaKysely />
            </MemoryRouter>,
        );
        const rakennaKyselyTeksti = screen.getByText(/luouusi-otsikko/i);
        expect(rakennaKyselyTeksti).toBeInTheDocument();
    });
    test('it should open in editing mode', () => {
        vi.mock(
            '@cscfi/shared/services/Arvo-api/Arvo-api-service',
            async (importOriginal) => ({
                ...((await importOriginal()) as object),
                arvoGetKysymysryhma$: () =>
                    of(convertKysymysRyhmaToValssi(kysymysryhmaData)),
            }),
        );

        render(
            <MemoryRouter initialEntries={['?id=1234']}>
                <RakennaKysely />
            </MemoryRouter>,
        );
        const rakennaKyselyTeksti = screen.getByText(/sivun-otsikko-muokkaa/i);
        expect(rakennaKyselyTeksti).toBeInTheDocument();
    });
});
