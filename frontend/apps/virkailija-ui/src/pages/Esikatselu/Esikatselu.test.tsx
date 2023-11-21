import {of} from 'rxjs';
import {MemoryRouter} from 'react-router-dom';
import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import * as arvoApi from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {addI18nResources} from '@cscfi/shared/test-utils';
import {
    arvoKyselytData,
    kysymysryhmaData,
    yllapitajaUserData,
    paakayttajaUserData,
    raporttiPohja1Data,
    raporttiPohja2Data,
} from '@cscfi/shared/utils/mockData';
import {StatusType} from '@cscfi/shared/services/Data/Data-service';
import * as virkailijapalveluApi from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import * as raportointipalveluApi from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import Esikatselu from './Esikatselu';
import UserContext from '../../Context';

describe('<Esikatselu />', () => {
    (arvoApi as any).arvoGetKysymysryhma$ = () => of(kysymysryhmaData);
    (arvoApi as any).arvoGetAllKyselyt$ = () => of(arvoKyselytData);

    test('it should mount for ylläpitäjä user 1', () => {
        (raportointipalveluApi as any).raportiointipalveluGetReportingBase$ = () => () =>
            of(raporttiPohja2Data);
        (virkailijapalveluApi as any).virkailijapalveluGetIsKysymysryhmaUsed$ = () =>
            of({is_used: 'not_used'});

        addI18nResources({
            'sivun-otsikko': 'Esikatselu',
            'lisaa-vaittama': 'Lisää väittämä',
        });

        render(
            <UserContext.Provider value={yllapitajaUserData as any}>
                <MemoryRouter initialEntries={['?id=1234']}>
                    <Esikatselu />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        expect(screen.getByText(/sivun-otsikko/i)).toBeInTheDocument();
        // expect(screen.getByText(/Esikatselu/i)).toBeInTheDocument(); TODO
        expect(screen.queryByText(/Kyselylomakkeen nimi/i)).toBeInTheDocument();
        // expect(screen.queryByText(/Lisää väittämä/i)).not.toBeInTheDocument();
        expect(screen.getAllByText(/painike-julkaise/i)[0]).toBeInTheDocument();
        expect(screen.queryByText(/painike-aktivointi/i)).not.toBeInTheDocument();
        expect(screen.getAllByText(/luo-raporttipohja/i)[0]).toBeInTheDocument();
        expect(screen.queryByText(/painike-arkistoi/i)).not.toBeInTheDocument();
        const allButtons = screen.getAllByRole('button');
        // Buttons: Julkaise, Lataa
        // Button-looking links, role="button": Poistu, Muokkaa, Täytä raporttipohja
        expect(allButtons).toHaveLength(10);
    });

    test('it should mount for pääkäyttäjä user 2', () => {
        render(
            <UserContext.Provider value={paakayttajaUserData as any}>
                <MemoryRouter initialEntries={['?id=1234']}>
                    <Esikatselu />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        expect(screen.queryByText(/painike-muokkaa/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/painike-julkaise/i)).not.toBeInTheDocument();
        expect(screen.getAllByText(/painike-aktivointi-lisaa/i)[0]).toBeInTheDocument();
        const allButtons = screen.getAllByRole('button');
        expect(allButtons).toHaveLength(6);
    });

    test('pääkäyttäjä user 2 should see "siirry lähetyssivulle" -button when appropriate', () => {
        kysymysryhmaData.metatiedot.lomaketyyppi =
            'asiantuntijalomake_paakayttaja_prosessitekijat';

        render(
            <UserContext.Provider value={paakayttajaUserData as any}>
                <MemoryRouter initialEntries={['?id=1234']}>
                    <Esikatselu />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        expect(screen.queryByText(/painike-muokkaa/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/painike-julkaise/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/painike-aktivointi-lisaa/i)).not.toBeInTheDocument();
        expect(screen.getAllByText(/painike-lahetys/i)[0]).toBeInTheDocument();
    });

    test('it should show ylläpitäjä "aseta takaisin luonnokseksi" for used kysymysryhmä 1', () => {
        kysymysryhmaData.tila = StatusType.julkaistu;
        (raportointipalveluApi as any).raportiointipalveluGetReportingBase$ = () => () =>
            of(raporttiPohja1Data);

        render(
            <UserContext.Provider value={yllapitajaUserData as any}>
                <MemoryRouter initialEntries={['?id=1234']}>
                    <Esikatselu />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        expect(screen.getAllByText(/muokkaa-raporttipohja/i)[0]).toBeInTheDocument();
    });

    test('it should not show ylläpitäjä a hidden question', () => {
        render(
            <UserContext.Provider value={yllapitajaUserData as any}>
                <MemoryRouter initialEntries={['?id=1234']}>
                    <Esikatselu />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        expect(screen.getAllByText(/kysymys1/i)[0]).toBeInTheDocument();
        expect(screen.queryByText(/hiddenKysymys3/i)).not.toBeInTheDocument();
    });
});
