import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import {useForm} from 'react-hook-form';
import SingleField from './SingleField';
import InputTypes from '../../../InputType/InputTypes';
import {GenericFormValueType} from '../../../../services/Data/Data-service';

// common variables for all tests
const kyselyKysymysIdMock = '123_45';
const titleMock = 'Väittämän nimi';
const descriptionMock = 'Väittämän tarkempi kuvaus';

describe('<SingleField />', () => {
    // ------------------------ checkbox
    /*
     * This mock component is needed for testing the actual component.
     * The actual component gets props from Kysely component that is using react-hook-form hook useForm.
     * Hooks can't be called outside a function-style component so we need a mock component
     * for calling the hook and passing the correct props to the component being tested.
     * */
    function KyselyMockForSingleField() {
        const {
            control,
            formState: {errors},
        } = useForm<GenericFormValueType>({
            defaultValues: {
                '123_45': 'kysymys1',
            },
        });
        return (
            <SingleField
                type={InputTypes.singletext}
                id={kyselyKysymysIdMock}
                required
                title={titleMock}
                description={descriptionMock}
                fieldErrors={errors}
                control={control}
            />
        );
    }

    test('it should mount single text field with description', async () => {
        render(<KyselyMockForSingleField />);
        const question = screen.getByText(/Väittämän nimi \*/i);
        expect(question).toBeInTheDocument();
        const description = screen.getByText(descriptionMock);
        expect(description).toBeInTheDocument();
        const value = screen.getByDisplayValue('kysymys1');
        expect(value).toBeInTheDocument();
    });

    // ------------------------ multiline text field / textarea
    function KyselyMockForMultilineField() {
        const {
            control,
            formState: {errors},
        } = useForm<GenericFormValueType>({
            defaultValues: {
                '123_45': 'pitkä teksti joka menee ehkä useammalle riville',
            },
        });
        return (
            <SingleField
                type={InputTypes.multiline}
                id={kyselyKysymysIdMock}
                required={false}
                title={titleMock}
                description={descriptionMock}
                fieldErrors={errors}
                control={control}
            />
        );
    }

    test('it should mount multiline text field', () => {
        render(<KyselyMockForMultilineField />);
        const requiredAsterisk = screen.queryByText(/Väittämän nimi \*/i);
        expect(requiredAsterisk).not.toBeInTheDocument();
        const otsikkoteksti = screen.getByText(/Väittämän nimi/i);
        expect(otsikkoteksti).toBeInTheDocument();
        const value = screen.getByDisplayValue(
            'pitkä teksti joka menee ehkä useammalle riville',
        );
        expect(value).toBeInTheDocument();
    });

    // ------------------------ number field
    function KyselyMockForNumberField() {
        const {
            control,
            formState: {errors},
        } = useForm<GenericFormValueType>({
            defaultValues: {'123_45': '3'},
        });
        return (
            <SingleField
                type={InputTypes.numeric}
                id={kyselyKysymysIdMock}
                required={false}
                title={titleMock}
                description={descriptionMock}
                fieldErrors={errors}
                control={control}
            />
        );
    }
    test('it should mount number field', () => {
        render(<KyselyMockForNumberField />);
        const value = screen.getByDisplayValue('3');
        expect(value).toBeInTheDocument();
    });
});
