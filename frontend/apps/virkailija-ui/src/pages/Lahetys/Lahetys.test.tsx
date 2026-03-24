import {of} from 'rxjs';
import {MemoryRouter} from 'react-router-dom';
import {fireEvent, render, screen} from '@testing-library/react';
import {test, describe, expect, vi} from 'vitest';
import {kysymysryhmaData, paakayttajaUserData} from '@cscfi/shared/utils/mockData';
import {convertKysymysRyhmaToValssi} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import Lahetys from './Lahetys';
import UserContext from '../../Context';

describe('<Lähetys />', () => {
    vi.mock(
        '@cscfi/shared/services/Arvo-api/Arvo-api-service',
        async (importOriginal) => ({
            ...((await importOriginal()) as object),
            arvoGetKysymysryhma$: () => of(convertKysymysRyhmaToValssi(kysymysryhmaData)),
        }),
    );

    test('it should open for Pääkäyttäjä', () => {
        render(
            <UserContext.Provider value={paakayttajaUserData as any}>
                <MemoryRouter initialEntries={['?id=1234']}>
                    <Lahetys />
                </MemoryRouter>
            </UserContext.Provider>,
        );
        const rakennaKyselyTeksti = screen.getByText(/vastausaika/i);
        expect(rakennaKyselyTeksti).toBeInTheDocument();
    });

    test('back-button should change when form dirty', async () => {
        render(
            <UserContext.Provider value={paakayttajaUserData as any}>
                <MemoryRouter initialEntries={['?id=1234']}>
                    <Lahetys />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        expect(screen.getByText(/painike-poistu/i)).toBeInTheDocument();

        const textareas = screen.getAllByRole('textbox');

        // change text in the last textarea of the page
        fireEvent.change(textareas[textareas.length - 1], {
            target: {value: 'new value'},
        });

        expect(screen.queryByText(/painike-poistu/i)).not.toBeInTheDocument();
        expect(screen.getByText(/painike-peruuta/i)).toBeInTheDocument();
    });
});
