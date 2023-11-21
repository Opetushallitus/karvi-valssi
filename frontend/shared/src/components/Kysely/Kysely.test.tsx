import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import {BrowserRouter} from 'react-router-dom';
import {initI18n} from '../../test-utils';
import Kysely from './Kysely';
import {kyselyData} from '../../utils/mockData';

describe('<Kysely />', () => {
    test('it should mount', () => {
        initI18n({
            '': '',
        });
        render(<Kysely selectedKysely={kyselyData[0]} />, {wrapper: BrowserRouter});
        expect(screen.getByText(/kysymys1/i)).toBeInTheDocument();
        expect(screen.getByText(/kysymys2/i)).toBeInTheDocument();
        expect(screen.getByText(/kyllä/i)).toBeInTheDocument();
        expect(screen.getByText(/ei/i)).toBeInTheDocument();
        expect(screen.getByText(/valiotsikko/i)).toBeInTheDocument();
        expect(screen.getByText(/sisaltoteksti/i)).toBeInTheDocument();
    });
});
