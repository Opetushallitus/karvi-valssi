import {of} from 'rxjs';
import {MemoryRouter} from 'react-router-dom';
import {render, fireEvent} from '@testing-library/react';
import {test, describe, expect, vi, it, beforeEach} from 'vitest';
import {addI18nResources} from '@cscfi/shared/test-utils';
import {
    arvoKyselytData,
    kysymysryhmaData,
    yllapitajaUserData,
    paakayttajaUserData,
    raporttiPohja1Data,
    raporttiPohja2Data,
    matrixScales,
} from '@cscfi/shared/utils/mockData';
import {StatusType} from '@cscfi/shared/services/Data/Data-service';
import * as raportointipalvelu from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import * as loginService from '@cscfi/shared/services/Login/Login-service';
import {convertKysymysRyhmaToValssi} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import Esikatselu from './Esikatselu';
import UserContext from '../../Context';

describe('<Esikatselu />', () => {
    vi.mock(
        '@cscfi/shared/services/Arvo-api/Arvo-api-service',
        async (importOriginal) => ({
            ...((await importOriginal()) as object),
            arvoGetKysymysryhma$: () => of(convertKysymysRyhmaToValssi(kysymysryhmaData)),
            arvoGetAllKyselyt$: () => of(arvoKyselytData),
        }),
    );

    vi.mock(
        '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service',
        async (importOriginal) => ({
            ...((await importOriginal()) as object),
        }),
    );

    vi.mock('@cscfi/shared/services/Login/Login-service', async (importOriginal) => ({
        ...((await importOriginal()) as object),
    }));

    beforeEach(() => {
        (raportointipalvelu as any).raportiointipalveluGetReportingBase$ = vi
            .fn()
            .mockReturnValue(() => of(raporttiPohja1Data));
    });

    it('it should mount for ylläpitäjä user 1', () => {
        (raportointipalvelu as any).raportiointipalveluGetReportingBase$ = vi
            .fn()
            .mockReturnValue(() => of(raporttiPohja2Data));

        vi.mock(
            '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service',
            async (importOriginal) => ({
                ...((await importOriginal()) as object),
                virkailijapalveluGetMatrixScales$: () => of(matrixScales),
                virkailijapalveluGetIsKysymysryhmaUsed$: () => of({is_used: 'not_used'}),
            }),
        );

        vi.mock('@cscfi/shared/services/Login/Login-service', async (importOriginal) => ({
            ...((await importOriginal()) as object),
            userKayttooikeudet$: of([
                {
                    kayttooikeus: 'YLLAPITAJA',
                    service: 'arvo',
                },
            ]),
        }));

        addI18nResources({
            'sivun-otsikko': 'Esikatselu',
            'lisaa-vaittama': 'Lisää väittämä',
        });

        render(
            <UserContext.Provider value={yllapitajaUserData}>
                <MemoryRouter initialEntries={['?id=1234']}>
                    <Esikatselu />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        expect(document.getElementsByTagName('h1')?.item(0)?.innerHTML).to.contain(
            'sivun-otsikko',
        );
        expect(document.getElementsByTagName('h2')?.item(0)?.innerHTML).to.contain(
            'Kyselylomakkeen nimi',
        );

        const buttons = document.querySelector('.button-container');
        expect(buttons?.innerHTML).to.contain('painike-julkaise');
        expect(buttons?.innerHTML).to.contain('luo-raporttipohja');
        expect(buttons?.innerHTML).to.not.contain('painike-aktivointi');
        expect(buttons?.innerHTML).to.not.contain('painike-arkistoi');

        expect(buttons?.children).to.have.lengthOf(5);
    });

    test('it should mount for pääkäyttäjä user 2', () => {
        (loginService as any).userKayttooikeudet$ = of([
            {
                kayttooikeus: 'PAAKAYTTAJA',
                service: 'arvo',
            },
        ]);

        render(
            <UserContext.Provider value={paakayttajaUserData as any}>
                <MemoryRouter initialEntries={['?id=1234']}>
                    <Esikatselu />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        const buttons = document.querySelector('.button-container');
        expect(buttons?.innerHTML).to.contain('painike-aktivointi');
        expect(buttons?.innerHTML).to.not.contain('painike-muokkaa');
        expect(buttons?.innerHTML).to.not.contain('painike-julkaise');

        expect(buttons?.children).to.have.lengthOf(3);
    });

    it('pääkäyttäjä user 2 should see "siirry lähetyssivulle" -button when appropriate', () => {
        kysymysryhmaData.metatiedot.lomaketyyppi =
            'asiantuntijalomake_paakayttaja_prosessitekijat';

        render(
            <UserContext.Provider value={paakayttajaUserData as any}>
                <MemoryRouter initialEntries={['?id=1234']}>
                    <Esikatselu />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        const buttons = document.querySelector('.button-container');
        expect(buttons?.innerHTML).to.contain('painike-lahetys');
        expect(buttons?.innerHTML).to.not.contain('painike-muokkaa');
        expect(buttons?.innerHTML).to.not.contain('painike-julkaise');
        expect(buttons?.innerHTML).to.not.contain('painike-aktivointi-lisaa');
    });

    it('it should show ylläpitäjä "Muokkaa raporttipohjaa" for used kysymysryhmä 1', () => {
        kysymysryhmaData.tila = StatusType.julkaistu;

        (loginService as any).userKayttooikeudet$ = of([
            {
                kayttooikeus: 'YLLAPITAJA',
                service: 'arvo',
            },
        ]);

        render(
            <UserContext.Provider value={yllapitajaUserData as any}>
                <MemoryRouter initialEntries={['?id=1234']}>
                    <Esikatselu />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        expect(document?.querySelector('body')?.innerHTML).to.contain(
            'muokkaa-raporttipohja',
        );
    });

    it('it should not show ylläpitäjä a hidden question', async () => {
        render(
            <UserContext.Provider value={yllapitajaUserData as any}>
                <MemoryRouter initialEntries={['?id=1234']}>
                    <Esikatselu />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        /* wait for matrix scales to be loaded (it prevents questions to be rendered) */
        const content = await document.getElementsByClassName('form')[0];
        expect(content.innerHTML).to.contain('kysymys1');
        expect(content.innerHTML).to.not.contain('hiddenKysymys3');
    });

    it('should only show questions in their appropriate pages', async () => {
        render(
            <UserContext.Provider value={yllapitajaUserData as any}>
                <MemoryRouter initialEntries={['?id=1234']}>
                    <Esikatselu />
                </MemoryRouter>
            </UserContext.Provider>,
        );

        /* wait for matrix scales to be loaded (it prevents questions to be rendered) */
        const content = await document.getElementsByClassName('form')[0];
        expect(content.innerHTML).to.contain('kysymys2');

        const kys965 = content.querySelectorAll(
            'div[data-testid="kysymysid-1234_965"]',
        )[0];
        const kys836 = content.querySelectorAll(
            'div[data-testid="kysymysid-1234_836"]',
        )[0];

        expect(kys836).to.have.property('hidden', false);
        expect(kys965).to.have.property('hidden', true);

        const nextPageButton = document
            .querySelector('div[class*="page-switch-container-lower"]')
            ?.children.item(1);
        fireEvent.click(nextPageButton as Element);

        expect(kys836).to.have.property('hidden', true);
        expect(kys965).to.have.property('hidden', false);
    });
});
