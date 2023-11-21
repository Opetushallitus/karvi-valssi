import {of} from 'rxjs';
import {MemoryRouter} from 'react-router-dom';
import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import * as arvoApi from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {kysymysryhmaData} from '@cscfi/shared/utils/mockData';
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
        (arvoApi as any).arvoGetKysymysryhma$ = () => of(kysymysryhmaData);

        render(
            <MemoryRouter initialEntries={['?id=1234']}>
                <RakennaKysely />
            </MemoryRouter>,
        );
        const rakennaKyselyTeksti = screen.getByText(/sivun-otsikko-muokkaa/i);
        expect(rakennaKyselyTeksti).toBeInTheDocument();
    });
});
