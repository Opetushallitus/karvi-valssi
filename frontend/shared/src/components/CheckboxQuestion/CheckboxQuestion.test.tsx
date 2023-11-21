import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import {StatusType} from '../../services/Data/Data-service';
import {addI18nResources} from '../../test-utils';
import CheckboxQuestion from './CheckboxQuestion';

describe('<CheckboxQuestion />', () => {
    const handleChangeMock = jest.fn();
    test('it should mount', () => {
        addI18nResources({
            otsikko: 'Otsikko',
            'lisaa-uusi-vastausvaihtoehto': 'Lisää uusi vastausvaihtoehto',
            vastausvaihtoehdot: 'Vastausvaihtoehdot',
        });
        render(
            <CheckboxQuestion
                title={{fi: 'otsikkoteksti1', sv: ''}}
                description={{fi: 'apua1', sv: ''}}
                published={StatusType.julkaistu}
                answerOptions={[]}
                handleChange={handleChangeMock}
            />,
        );
        const checkbox = screen.getAllByText(/Otsikko/i)[0];
        const checkboxTitleText = screen.getByDisplayValue('otsikkoteksti1');
        expect(checkbox).toBeInTheDocument();
        expect(checkboxTitleText).toBeInTheDocument();
    });
    test('it should mount with options', () => {
        render(
            <CheckboxQuestion
                title={{fi: 'otsikkoteksti2', sv: ''}}
                description={{fi: 'apua2', sv: ''}}
                published={StatusType.julkaistu}
                answerOptions={[
                    {
                        id: 1,
                        title: {fi: 'yes', sv: ''},
                        description: {fi: '', sv: ''},
                        checked: false,
                    },
                    {
                        id: 2,
                        title: {fi: 'no', sv: ''},
                        description: {fi: '', sv: ''},
                        checked: false,
                    },
                ]}
                handleChange={handleChangeMock}
            />,
        );
        const checkboxYes = screen.getByDisplayValue('yes');
        const checkboxNo = screen.getByDisplayValue('no');
        expect(checkboxYes).toBeInTheDocument();
        expect(checkboxNo).toBeInTheDocument();
    });
    test('it should mount with options containing descriptions', () => {
        render(
            <CheckboxQuestion
                title={{fi: 'otsikkoteksti3', sv: ''}}
                description={{fi: 'apuva3', sv: ''}}
                published={StatusType.julkaistu}
                answerOptions={[
                    {
                        id: 1,
                        title: {fi: 'y', sv: ''},
                        checked: false,
                        description: {fi: 'y is for yes', sv: ''},
                    },
                    {
                        id: 2,
                        title: {fi: 'n', sv: ''},
                        checked: false,
                        description: {fi: 'n is for no', sv: ''},
                    },
                ]}
                handleChange={handleChangeMock}
            />,
        );
        const checkboxYes = screen.getByDisplayValue('y is for yes');
        const checkboxNo = screen.getByDisplayValue('n is for no');
        expect(checkboxYes).toBeInTheDocument();
        expect(checkboxNo).toBeInTheDocument();
    });
});
