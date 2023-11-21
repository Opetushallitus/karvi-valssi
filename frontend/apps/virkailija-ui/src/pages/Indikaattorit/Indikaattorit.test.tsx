import {render, screen} from '@testing-library/react';
import {BrowserRouter as Router} from 'react-router-dom';
import '@testing-library/jest-dom';
import {addI18nResources} from '@cscfi/shared/test-utils';
import Indikaattorit from './Indikaattorit';

describe('<Indikaattorit />', () => {
    test('it should mount', () => {
        addI18nResources({
            'sivun-otsikko': 'Arviointityökalut',
            'th-prosessitekijat': 'Prosessitekijöiden indikaattorit',
            'th-rakennetekijat': 'Rakennetekijöiden indikaattorit',
        });
        render(
            <Router>
                <Indikaattorit />
            </Router>,
        );
        const indikaattoritHeading = screen.getByRole('heading');
        expect(indikaattoritHeading).toHaveTextContent('sivun-otsikko');
        // expect(indikaattoritHeading).toHaveTextContent('Arviointityökalut'); TODO
        expect(screen.getByText('th-prosessitekijat')).toBeInTheDocument();
        // expect(screen.getByText('Prosessitekijöiden indikaattorit')).toBeInTheDocument();
        expect(screen.getByText('th-rakennetekijat')).toBeInTheDocument();
        // expect(screen.getByText('Rakennetekijöiden indikaattorit')).toBeInTheDocument();
    });
});
