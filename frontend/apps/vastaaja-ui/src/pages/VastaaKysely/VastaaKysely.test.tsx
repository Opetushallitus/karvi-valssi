import {fireEvent, render} from '@testing-library/react';
import {describe, it, expect} from 'vitest';
import {MemoryRouter, Routes, Route} from 'react-router-dom';
import {
    kyselyData,
    kyselyKertaData,
    kysymysryhmaData,
} from '@cscfi/shared/utils/mockData';
import * as vastApi from '@cscfi/shared/services/Vastauspalvelu-api/Vastauspalvelu-api-service';
import {of} from 'rxjs';
import Kysely from '@cscfi/shared/components/Kysely/Kysely';
import {convertKysymyksetArvoToValssi} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {KyselyType} from '@cscfi/shared/services/Data/Data-service';
import VastaaKysely from './VastaaKysely';

describe('<VastaaKysely />', () => {
    (vastApi as any).vastauspalveluGetKyselykerta$ = () => of(kyselyKertaData);

    it('should mount VastaaKysely', () => {
        render(
            <MemoryRouter initialEntries={['?vastaajatunnus=ABCDF']}>
                <Routes>
                    <Route path="/" element={<VastaaKysely />} />
                </Routes>
            </MemoryRouter>,
        );

        const suomiBtn = document.querySelectorAll('button')[0];
        expect(suomiBtn.innerHTML).to.include('suomi');
    });

    it('should mount kysely', () => {
        const kys = (): KyselyType => {
            const kr = kysymysryhmaData;
            return {
                lomaketyyppi: kr.metatiedot.lomaketyyppi,
                paaIndikaattori: kr.metatiedot?.paaIndikaattori,
                status: kr.tila,
                id: 1234,
                topic: {
                    fi: kr.nimi_fi,
                    sv: kr.nimi_sv || '',
                },
                kysymykset: convertKysymyksetArvoToValssi(kr.kysymykset),
            };
        };

        render(
            <MemoryRouter initialEntries={['?vastaajatunnus=ABCDF']}>
                <Kysely
                    vastaajaUi
                    tempAnswersAllowed
                    vastaajatunnus="ABCDF"
                    selectedKysely={kys()}
                />
                ,
            </MemoryRouter>,
        );

        const tallennaButton = Array.from(document.querySelectorAll('*')).find((el) =>
            el.textContent?.includes('tallenna-valiaikaisesti'),
        );
        expect(tallennaButton?.innerHTML).to.include('tallenna');
    });

    it('should show questions on correct pages', async () => {
        render(
            <MemoryRouter initialEntries={['?vastaajatunnus=ABCDF']}>
                <Kysely
                    vastaajaUi
                    tempAnswersAllowed
                    vastaajatunnus="ABCDF"
                    selectedKysely={kyselyData[0]}
                />
                ,
            </MemoryRouter>,
        );

        /* wait for matrix scales to be loaded (it prevents questions to be rendered) */
        const content = await document.getElementsByClassName('form')[0];
        expect(content.innerHTML).to.contain('kysymys2');

        const kys966 = content.querySelectorAll(
            'div[data-testid="kysymysid-1234_966"]',
        )[0];
        const kys836 = content.querySelectorAll(
            'div[data-testid="kysymysid-1234_836"]',
        )[0];

        expect(kys836).to.have.property('hidden', false);
        expect(kys966).to.have.property('hidden', true);

        const nextPageButton = document
            .querySelector('div[class*="page-switch-container-lower"]')
            ?.children.item(1);
        fireEvent.click(nextPageButton as Element);

        expect(kys836).to.have.property('hidden', true);
        expect(kys966).to.have.property('hidden', false);
    });
});
