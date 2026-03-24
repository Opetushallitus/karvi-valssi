import React, {useMemo, useState} from 'react';
import {Controller, FieldValues} from 'react-hook-form';
import {useTranslation} from 'react-i18next';
import Grid from '@mui/material/Grid';
import Collapse from '@mui/material/Collapse';
import {
    KysymysType,
    MatrixType,
    TextType,
} from '@cscfi/shared/services/Data/Data-service';
import WarningIcon from '@mui/icons-material/Warning';
import styles from '../../Form.module.css';
import MatrixEosLabel from '../Matrix/MatrixEosLabel';
import RadioRowField from '../RadioRowField/RadioRowField';
import InfoToggle from '../../../InfoToggle/InfoToggle';
import InputTypes from '../../../InputType/InputTypes';
import SliderField from '../../../SliderField/SliderField';
import MatrixDesctopScale from '../Matrix/MatrixDesktopScale';

interface MatrixFieldProps {
    id: string;
    title: string;
    description?: string;
    isSubmitting: boolean;
    questions: KysymysType[];
    type: InputTypes.matrix_radio | InputTypes.matrix_slider;
    fieldErrors?: FieldValues;
    ignoreRequired?: boolean; // To not block submit
    control: any; // Control<SomeFormType, any>
    editable?: boolean;
    matrixTypes: MatrixType[];
    language?: string;
}

function MatrixField({
    id,
    title,
    description,
    isSubmitting = false,
    questions,
    type,
    fieldErrors,
    ignoreRequired = false,
    control,
    editable = false,
    matrixTypes,
    language,
}: MatrixFieldProps) {
    const {
        i18n: {language: lang},
    } = useTranslation(['form']);
    const langKey = language ? language : (lang as keyof TextType);

    const [descOpen, setDescOpen] = useState<boolean>(false);

    // Ensimmäinen rivikysymys (tarvitaan answerTypeen)
    const firstQuestion = questions.find((e) => e);

    const {t} = useTranslation(['error']);

    // Johdettu arvo renderiin (ei setStatea efektissä)
    const matrixType = useMemo(() => {
        if (!matrixTypes) return null;
        return matrixTypes.find((ms) => ms.name === firstQuestion?.answerType) ?? null;
    }, [matrixTypes, firstQuestion?.answerType]);

    if (!matrixType) {
        return null;
    }

    return (
        <fieldset id={id} className={styles['input-field']}>
            <Grid
                container
                direction={{xs: 'column', sm: 'row'}}
                columns={{xs: 1, sm: 2}}
            >
                <Grid width={{xs: '100%', md: '25%'}}>
                    {title && (
                        <legend className="label-for-inputfield">
                            {title}
                            {description && (
                                <InfoToggle
                                    isOpen={descOpen}
                                    onChange={() => {
                                        setDescOpen(!descOpen);
                                    }}
                                    controlId={`${id}_desc`}
                                    ariaLabelTxt={title}
                                />
                            )}
                        </legend>
                    )}
                    {description && (
                        <Collapse in={descOpen} id={`${id}_desc`}>
                            <p>{description}</p>
                        </Collapse>
                    )}
                </Grid>

                <MatrixDesctopScale matrixType={matrixType} id={id} language={language} />
                {firstQuestion?.allowEos && (
                    <MatrixEosLabel matrixType={matrixType} language={language} />
                )}
            </Grid>

            {questions.map((question) => {
                const kyselyKysymysId = `${id}_${question.id}`;
                const errors = fieldErrors && (fieldErrors as any)[kyselyKysymysId];
                const firstError: string =
                    fieldErrors && Object.keys(fieldErrors as any)[0];

                return (
                    <Controller
                        key={kyselyKysymysId}
                        name={kyselyKysymysId}
                        rules={{
                            validate: (value) => {
                                if (!question.required || ignoreRequired) {
                                    return true;
                                }
                                return !!value;
                            },
                        }}
                        control={control}
                        render={({field: {onChange, value}}) => {
                            const matrixOnChange = (
                                e: React.ChangeEvent<HTMLInputElement>,
                            ) => {
                                const kyselyKysymysValue = e.currentTarget.value;
                                onChange(Number(kyselyKysymysValue) ?? undefined);
                            };

                            const rowField =
                                type === InputTypes.matrix_radio ? (
                                    <RadioRowField
                                        key={kyselyKysymysId}
                                        id={kyselyKysymysId}
                                        label={question.title?.[langKey]}
                                        errors={errors}
                                        onChange={matrixOnChange}
                                        matrixType={matrixType}
                                        value={value}
                                        description={question.description?.[langKey]}
                                        required={question.required}
                                        allowEos={question.allowEos}
                                        hidden={question.hidden}
                                        editable={editable}
                                        // Huom: Controller käyttää omaa register-logiikkaansa; älä lue refiä renderissä
                                        register={control.register}
                                    />
                                ) : (
                                    <SliderField
                                        key={kyselyKysymysId}
                                        id={kyselyKysymysId}
                                        label={question.title?.[langKey]}
                                        errors={errors}
                                        isSubmitting={isSubmitting}
                                        firstError={firstError}
                                        onChange={matrixOnChange}
                                        matrixType={matrixType}
                                        value={value}
                                        description={question.description?.[langKey]}
                                        required={question.required}
                                        allowEos={question.allowEos}
                                        hidden={question.hidden}
                                        editable={editable}
                                    />
                                );

                            return (
                                <>
                                    {rowField}
                                    {errors && (
                                        <p className="error" role="alert">
                                            <WarningIcon />
                                            {t('pakollinen-vaittama')}
                                        </p>
                                    )}
                                </>
                            );
                        }}
                    />
                );
            })}
        </fieldset>
    );
}

export default MatrixField;
