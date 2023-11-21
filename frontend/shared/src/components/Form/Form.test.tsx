import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import {useForm} from 'react-hook-form';
import {initI18n} from '../../test-utils';
import Form from './Form';
import {GenericFormValueType} from '../../services/Data/Data-service';
import {kyselyData} from '../../utils/mockData';

/*
 * This mock component is needed for testing Form.
 * Form gets props from Kysely component that is using react-hook-form hook useForm.
 * Hooks can't be called outside a function-style component so we need a mock component
 * for calling the hook and passing the correct props to the component being tested.
 * */
function KyselyMockForForm() {
    const {
        control,
        formState: {errors},
    } = useForm<GenericFormValueType>();
    const kysely = kyselyData[0];

    return (
        <Form
            kysely={kysely}
            editable={false}
            errors={errors}
            control={control}
            vastaajaUi={false}
        />
    );
}

describe('<Form />', () => {
    test('it should mount', () => {
        initI18n({
            '': '',
        });
        render(<KyselyMockForForm />);
        expect(screen.getByRole('textbox')).toBeInTheDocument();
        const kysymys2 = screen.getByText('kysymys2');
        expect(kysymys2).toBeInTheDocument();
        expect(screen.getByText('kyllä')).toBeInTheDocument();
        expect(screen.getByText('ei')).toBeInTheDocument();
    });
});
