import {useEffect, useMemo} from 'react';
import {Observable} from 'rxjs';
import {useNavigate} from 'react-router-dom';
import {SubmitHandler, useForm} from 'react-hook-form';
import {GenericFormValueType} from '@cscfi/shared/services/Data/Data-service';
import InputTypes from '@cscfi/shared/components/InputType/InputTypes';
import SingleField from '@cscfi/shared/components/Form/FormFields/SingleField/SingleField';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {SummaryType} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import GenericFormButtons from './GenericFormButtons';

interface PayloadGeneratorProps {
    formData: GenericFormValueType;
    formMetadata?: object;
    publish?: object;
}

function payloadGenerator({formData, formMetadata, publish}: PayloadGeneratorProps) {
    const payload = {
        ...formData,
        ...(!!formMetadata && formMetadata),
        ...(!!publish && publish),
    };
    return payload as SummaryType;
}

export interface GenericFormField {
    name: string;
    title: string;
    value: string;
    isLargeTxtField: boolean;
}

interface GenericFormProps {
    sourcePage?: string;
    fields: GenericFormField[];
    updateOrCreateFn: (data: any) => Observable<any>;
    formMetadata: object;
    publishFeature?: (publish: boolean) => object;
    maxInputLength: number;
    showButtons?: boolean;
    translationNameSpace?: string;
}

function GenericForm({
    sourcePage,
    fields,
    updateOrCreateFn,
    formMetadata,
    publishFeature,
    maxInputLength,
    showButtons = true,
    translationNameSpace = 'genericform',
}: GenericFormProps) {
    const navigate = useNavigate();

    function prevPage() {
        return sourcePage ? `/${sourcePage}` : '/';
    }

    const defaultValues = useMemo(() => {
        const df: GenericFormValueType = {};
        fields.forEach((field) => {
            df[field.name] = field.value;
        });
        return {
            ...df,
        };
    }, [fields]);

    const onSubmit: SubmitHandler<GenericFormValueType> = (formData, event) => {
        // @ts-expect-error submitter does not exist in type object
        const isPublishMethod = !!(event?.nativeEvent.submitter?.value === 'publish');

        updateOrCreateFn(
            payloadGenerator({
                formData,
                formMetadata,
                publish: !!publishFeature && publishFeature(isPublishMethod),
            }),
        ).subscribe({
            complete: () => {
                AlertService.showAlert({
                    title: {
                        key: `${isPublishMethod ? 'publish' : 'save'}-success-title`,
                        ns: translationNameSpace,
                    },
                    severity: 'success',
                } as AlertType);
                navigate(prevPage());
            },
            error: () => {
                AlertService.showAlert({
                    title: {
                        key: `${isPublishMethod ? 'publish' : 'save'}-error-title`,
                        ns: translationNameSpace,
                    },
                    severity: 'error',
                } as AlertType);
            },
        });
    };

    const {
        handleSubmit,
        reset,
        control,
        formState: {errors, isDirty},
    } = useForm<GenericFormValueType>({defaultValues});

    useEffect(() => {
        reset(defaultValues);
    }, [defaultValues, reset]);

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="form">
            {showButtons && (
                <GenericFormButtons
                    needsCancelConfirmation={isDirty}
                    sourcePage={sourcePage}
                    hasPublishBtn={!!publishFeature}
                    translationNameSpace={translationNameSpace}
                />
            )}
            {fields.map((field) => (
                <SingleField
                    key={field.name}
                    type={
                        field.isLargeTxtField
                            ? InputTypes.multiline
                            : InputTypes.singletext
                    }
                    id={field.name}
                    required={false}
                    title={field.title}
                    fieldErrors={errors[field.name]}
                    control={control}
                    maxLength={maxInputLength}
                />
            ))}

            {showButtons && (
                <GenericFormButtons
                    needsCancelConfirmation={isDirty}
                    sourcePage={sourcePage}
                    hasPublishBtn={!!publishFeature}
                    translationNameSpace={translationNameSpace}
                />
            )}
        </form>
    );
}

export default GenericForm;
