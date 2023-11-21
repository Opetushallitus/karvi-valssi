import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import {useForm} from 'react-hook-form';
import {initI18n} from '../../../../test-utils';
import MultiOptionField from './MultiOptionField';
import InputTypes from '../../../InputType/InputTypes';
import {GenericFormValueType} from '../../../../services/Data/Data-service';

// common variables for all tests
const kyselyKysymysIdMock = '123_45';
const titleMock = 'Väittämän nimi';
const answerOptions = [
    {
        id: 1,
        title: {fi: 'kyllä', sv: 'ja'},
        description: {fi: 'apua', sv: ''},
        checked: false,
    },
    {
        id: 2,
        title: {fi: 'ei', sv: 'nej'},
        description: {fi: 'ei en tarvitse apua', sv: ''},
        checked: false,
    },
];
describe('<MultilineTextQuestion />', () => {
    // ------------------------ checkbox
    /*
     * This mock component is needed for testing the actual component.
     * The actual component gets props from Kysely component that is using react-hook-form hook useForm.
     * Hooks can't be called outside a function-style component so we need a mock component
     * for calling the hook and passing the correct props to the component being tested.
     * */
    function KyselyMockForCheckboxMultiOptionField() {
        const defaultValues: GenericFormValueType = {
            '123_45': {1: true, 2: false},
        };
        const {
            control,
            formState: {errors},
        } = useForm<GenericFormValueType>({
            defaultValues,
        });
        return (
            <MultiOptionField
                type={InputTypes.checkbox}
                id={kyselyKysymysIdMock}
                required={false}
                title={titleMock}
                answerOptions={answerOptions}
                fieldErrors={errors}
                control={control}
            />
        );
    }

    test('it should mount', () => {
        initI18n({
            '': '',
        });
        render(<KyselyMockForCheckboxMultiOptionField />);
        const otsikko = screen.getByText(titleMock);
        expect(otsikko).toBeInTheDocument();
        expect(screen.getByText('kyllä')).toBeInTheDocument();
        expect(screen.getByText('ei')).toBeInTheDocument();
        expect(screen.getByRole('checkbox', {name: 'kyllä'})).toBeChecked();
        expect(screen.getByRole('checkbox', {name: 'ei'})).not.toBeChecked();
    });
});
