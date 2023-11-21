import React, {useEffect, useState} from 'react';
import {Control, Controller, FieldValues} from 'react-hook-form';
import {useTranslation} from 'react-i18next';
import Grid from '@mui/material/Grid';
import Collapse from '@mui/material/Collapse';
import {
    KysymysType,
    MatrixType,
    TextType,
} from '@cscfi/shared/services/Data/Data-service';
import styles from '@cscfi/shared/components/Form/Form.module.css';
import {useObservable} from 'rxjs-hooks';
import WarningIcon from '@mui/icons-material/Warning';
import {vastauspalveluGetMatrixScales$} from '../../../../services/Vastauspalvelu-api/Vastauspalvelu-api-service';
import MatrixEosLabel from '../Matrix/MatrixEosLabel';
import {virkailijapalveluGetMatrixScales$} from '../../../../services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import RadioRowField from '../RadioRowField/RadioRowField';
import InfoToggle from '../../../InfoToggle/InfoToggle';
import InputTypes from '../../../InputType/InputTypes';
import SliderField from '../../../SliderField/SliderField';
import MatrixDesctopScale from '../Matrix/MatrixDesktopScale';

interface MatrixFieldProps {
    id: string;
    title: string;
    description?: string;
    hidden?: boolean;
    isSubmitting: boolean;
    questions: KysymysType[];
    type: InputTypes.matrix_radio | InputTypes.matrix_slider;
    fieldErrors?: FieldValues;
    ignoreRequired?: boolean; // To not block submit
    control: Control;
}

function MatrixField({
    id,
    title,
    description,
    hidden = false,
    isSubmitting = false,
    questions,
    type,
    fieldErrors,
    ignoreRequired = false,
    control,
}: MatrixFieldProps) {
    const {
        i18n: {language: lang},
    } = useTranslation(['form']);
    const langKey = lang as keyof TextType;
    const [descOpen, setDescOpen] = useState<boolean>(false);
    const [matrixType, setMatrixType] = useState<MatrixType>(null);
    const firstQuestion = questions.find((e) => e);
    const {t} = useTranslation(['error']);

    const matrixTypes = useObservable(() =>
        window.location.pathname.split('/')[1] === 'vastaaja-ui'
            ? vastauspalveluGetMatrixScales$()
            : virkailijapalveluGetMatrixScales$(),
    );

    useEffect(() => {
        if (matrixTypes) {
            const found = matrixTypes.find((ms) => ms.name === firstQuestion?.answerType);
            if (found) {
                setMatrixType(found);
            }
        }
    }, [firstQuestion?.answerType, matrixTypes]);

    if (!matrixType) {
        return null;
    }

    return (
        <fieldset className={styles['input-field']}>
            <Grid
                container
                direction={{xs: 'column', sm: 'row'}}
                columns={{xs: 1, sm: 2}}
            >
                <Grid item width={{xs: '100%', md: '25%'}}>
                    {title && (
                        <legend className="label-for-inputfield">
                            {title}
                            {description && (
                                <InfoToggle
                                    isOpen={descOpen}
                                    onChange={() => {
                                        setDescOpen(!descOpen);
                                    }}
                                />
                            )}
                        </legend>
                    )}
                    {description && (
                        <Collapse in={descOpen}>
                            <p>{description}</p>
                        </Collapse>
                    )}
                </Grid>
                <MatrixDesctopScale matrixType={matrixType} id={id} />
                {firstQuestion.allowEos && <MatrixEosLabel matrixType={matrixType} />}
            </Grid>

            {questions.map((question) => {
                const kyselyKysymysId = `${id}_${question.id}`;
                const errors = fieldErrors && fieldErrors[kyselyKysymysId];
                const firstError: string = fieldErrors && Object.keys(fieldErrors)[0];
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
                                onChange(Number(kyselyKysymysValue) || undefined);
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
                                        hidden={hidden}
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
                                        hidden={hidden}
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
