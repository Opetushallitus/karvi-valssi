import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import {MemoryRouter, Routes, Route} from 'react-router-dom';
import {kyselyKertaData, kysymysryhmaData} from '@cscfi/shared/utils/mockData';
import * as vastApi from '@cscfi/shared/services/Vastauspalvelu-api/Vastauspalvelu-api-service';
import {of} from 'rxjs';
import Kysely from '@cscfi/shared/components/Kysely/Kysely';
import {convertKysymyksetArvoToValssi} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {KyselyType} from '@cscfi/shared/services/Data/Data-service';
import VastaaKysely from './VastaaKysely';

describe('<VastaaKysely />', () => {
    (vastApi as any).vastauspalveluGetKyselykerta$ = () => of(kyselyKertaData);

    test('mount VastaaKysely', () => {
        render(
            <MemoryRouter initialEntries={['?vastaajatunnus=ABCDF']}>
                <Routes>
                    <Route path="/" element={<VastaaKysely />} />
                </Routes>
            </MemoryRouter>,
        );

        const suomiBtn = screen.getByText(/suomi/i);
        expect(suomiBtn).toBeInTheDocument();
    });

    test('mount kysely', () => {
        const kys = (): KyselyType => {
            const kr = kysymysryhmaData;
            return {
                lomaketyyppi: kr.metatiedot.lomaketyyppi,
                paaIndikaattori: {key: kr.metatiedot?.paaIndikaattori, group: 1},
                status: kr.tila,
                id: 1234,
                topic: {
                    fi: kr.nimi_fi,
                    sv: kr.nimi_sv || '',
                },
                // @ts-ignore
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

        const suomiBtn = screen.getByText(/tallenna-valiaikaisesti/i);
        expect(suomiBtn).toBeInTheDocument();
    });
});
