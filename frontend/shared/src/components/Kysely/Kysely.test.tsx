import {render, screen} from '@testing-library/react';
import {describe, expect, vi, it} from 'vitest';
import {BrowserRouter} from 'react-router-dom';
import {of} from 'rxjs';
import {initI18n} from '../../test-utils';
import Kysely from './Kysely';
import {kyselyData, matrixScales} from '../../utils/mockData';

describe('<Kysely />', () => {
    vi.mock(
        '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service',
        () => ({
            virkailijapalveluGetMatrixScales$: () => of(matrixScales),
        }),
    );

    it('it should mount', async () => {
        initI18n({
            '': '',
        });
        render(<Kysely selectedKysely={kyselyData[0]} />, {wrapper: BrowserRouter});

        /* wait for matrix scales to be loaded (it prevents questions to be rendered) */
        await screen.findAllByTestId('kysymysid-', {exact: false});

        expect(screen.getByText(/kysymys1/i)).toBeInTheDocument();
        expect(screen.getByText(/kysymys2/i)).toBeInTheDocument();
        expect(screen.getByText(/kyllä/i)).toBeInTheDocument();
        expect(screen.getByText(/ei/i)).toBeInTheDocument();
        expect(screen.getByText(/valiotsikko/i)).toBeInTheDocument();
        expect(screen.getByText(/sisaltoteksti/i)).toBeInTheDocument();
    });

    // TODO: test for followup questions (VAL-1098)
});
