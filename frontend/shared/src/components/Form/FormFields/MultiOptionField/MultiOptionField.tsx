import React, {useState} from 'react';
import {Control, Controller, FieldValues} from 'react-hook-form';
import FormControl from '@mui/material/FormControl';
import Collapse from '@mui/material/Collapse';
import WarningIcon from '@mui/icons-material/Warning';
import {useTranslation} from 'react-i18next';
import {CheckBoxType, RadioButtonType} from '../../../../services/Data/Data-service';
import InputTypes from '../../../InputType/InputTypes';
import Options from './Options';
import InfoToggle from '../../../InfoToggle/InfoToggle';
import styles from '../../Form.module.css';

interface MultiOptionFieldProps {
    id: string;
    required: boolean;
    title?: string;
    description?: string;
    answerOptions: CheckBoxType[] | RadioButtonType[];
    type?: InputTypes.checkbox | InputTypes.radio;
    fieldErrors?: FieldValues;
    control: Control;
    hidden?: boolean;
}

// values are key-value pairs like {1: true, 2: false}
function MultiOptionField({
    id,
    required,
    title,
    description,
    answerOptions,
    type = InputTypes.checkbox,
    fieldErrors,
    control,
    hidden = false,
}: MultiOptionFieldProps) {
    const [descOpen, setDescOpen] = useState<boolean>(false);
    const {t} = useTranslation(['error']);
    let labelStyles = 'label-for-inputfield';
    if (hidden) labelStyles += ' hidden';
    if (fieldErrors) labelStyles += ' error';

    return (
        <FormControl key={id} component="fieldset" className={styles['input-field']}>
            {title && (
                <label htmlFor={id} className={labelStyles}>
                    {title}
                    {required ? ' *' : ''}
                    {description && (
                        <InfoToggle
                            isOpen={descOpen}
                            onChange={() => {
                                setDescOpen(!descOpen);
                            }}
                        />
                    )}
                </label>
            )}
            {description && (
                <Collapse in={descOpen}>
                    <p className="info">{description}</p>
                </Collapse>
            )}
            <div className={fieldErrors ? 'overall-error' : ''}>
                {(() => {
                    switch (type) {
                        case InputTypes.checkbox:
                            return (
                                <Controller
                                    name={id}
                                    rules={{
                                        validate: (value) => {
                                            if (!required) {
                                                return true;
                                            }
                                            const checkboxValues = Object.values(value);
                                            return checkboxValues.includes(true);
                                        },
                                    }}
                                    control={control}
                                    render={({field: {onChange, value}}) => {
                                        const checkboxOnChange = (
                                            e: React.ChangeEvent<HTMLInputElement>,
                                        ) => {
                                            const nameParts = e.target.name.split('_');
                                            const newValue = {...value};
                                            for (
                                                let i = 0;
                                                i < answerOptions.length;
                                                i += 1
                                            ) {
                                                if (
                                                    parseInt(nameParts[2], 10) ===
                                                    answerOptions[i].id
                                                ) {
                                                    newValue[answerOptions[i].id] =
                                                        !value[answerOptions[i].id];
                                                }
                                            }
                                            onChange(newValue);
                                        };
                                        return (
                                            <Options
                                                id={id}
                                                values={value || []}
                                                answerOptions={answerOptions}
                                                type={type}
                                                onChange={checkboxOnChange}
                                                register={control.register}
                                                hidden={hidden}
                                            />
                                        );
                                    }}
                                />
                            );
                        case InputTypes.radio:
                            return (
                                <Controller
                                    name={id}
                                    rules={{
                                        validate: (value) => {
                                            if (!required) {
                                                return true;
                                            }
                                            const radioValues = Object.values(value);
                                            return radioValues.includes(true);
                                        },
                                    }}
                                    control={control}
                                    render={({field: {onChange, value}}) => {
                                        const radioOnChange = (
                                            e: React.ChangeEvent<HTMLInputElement>,
                                        ) => {
                                            const nameParts = e.target.value.split('_');
                                            const newValue = {...value};
                                            for (
                                                let i = 0;
                                                i < answerOptions.length;
                                                i += 1
                                            ) {
                                                newValue[answerOptions[i].id] =
                                                    parseInt(nameParts[2], 10) ===
                                                    answerOptions[i].id;
                                            }
                                            onChange(newValue);
                                        };
                                        return (
                                            <Options
                                                id={id}
                                                values={value}
                                                answerOptions={answerOptions}
                                                type={type}
                                                onChange={radioOnChange}
                                                register={control.register}
                                                hidden={hidden}
                                            />
                                        );
                                    }}
                                />
                            );
                        default:
                            console.log(`Error: Invalid MultiOptionField type: ${type}`);
                            return (
                                <div>
                                    <span>{`${t(
                                        'invalid-multioptionfield-type',
                                    )}: (${type})`}</span>
                                </div>
                            );
                    }
                })()}
            </div>
            {fieldErrors && fieldErrors.type === 'validate' && (
                <p className="error" role="alert">
                    <WarningIcon />
                    {t('pakollinen-kentta')}
                </p>
            )}
        </FormControl>
    );
}

export default MultiOptionField;
