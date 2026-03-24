import {render, screen} from '@testing-library/react';
import {describe, expect, vi, it} from 'vitest';
import {useForm} from 'react-hook-form';
import {of} from 'rxjs';
import {initI18n} from '../../test-utils';
import Form from './Form';
import {GenericFormValueType} from '../../services/Data/Data-service';
import {kyselyData, matrixScales} from '../../utils/mockData';

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

    const mockSetLastPage = vi.fn();

    return (
        <Form
            kysely={kysely}
            editable={false}
            errors={errors}
            control={control}
            vastaajaUi={false}
            isSubmitting={false}
            onLastPage
            setLastPage={mockSetLastPage}
        />
    );
}

describe('<Form />', () => {
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
        render(<KyselyMockForForm />);

        /* wait for matrix scales to be loaded (it prevents questions to be rendered) */
        await screen.findAllByTestId('kysymysid-', {exact: false});

        expect(screen.getByRole('textbox')).toBeInTheDocument();
        const kysymys2 = screen.getByText('kysymys2');
        expect(kysymys2).toBeInTheDocument();
        expect(screen.getByText('kyllä')).toBeInTheDocument();
        expect(screen.getByText('ei')).toBeInTheDocument();
    });
});
