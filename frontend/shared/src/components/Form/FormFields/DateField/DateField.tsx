import {useCallback} from 'react';
import {Controller} from 'react-hook-form';
import {isValid, isBefore, isSameDay, isAfter} from 'date-fns';
import WarningIcon from '@mui/icons-material/Warning';
import {useTranslation} from 'react-i18next';
import DatePickerField from '../../../DatePickerField/DatePickerField';

export interface CustomErrorMessages {
    required?: string;
    validate?: string;
}

interface DateFieldProps {
    id: string;
    minDate?: Date | number;
    maxDate?: Date | number;
    label?: string;
    required?: boolean;
    disabled?: boolean;
    customErrorMessages?: CustomErrorMessages;
    control: any; // Control<SomeFormType, any>
}

function DateField({
    id,
    minDate,
    maxDate,
    label,
    required = false,
    disabled = false,
    customErrorMessages,
    control,
}: DateFieldProps) {
    const {t} = useTranslation(['datepicker']);

    enum ValidationStates {
        BEFORE = 'before',
        AFTER = 'after',
        INVALID = 'invalid',
    }

    const validationMessage = useCallback(
        (errMsg: string) => {
            switch (errMsg) {
                case ValidationStates.BEFORE:
                    return t('paivamaara-ennen-sallitua');
                case ValidationStates.AFTER:
                    return t('paivamaara-sallitun-jalkeen');
                default:
                    return (
                        customErrorMessages?.validate || t('ei-kelvollinen-paivamaara')
                    );
            }
        },
        [
            ValidationStates.AFTER,
            ValidationStates.BEFORE,
            customErrorMessages?.validate,
            t,
        ],
    );

    return (
        <Controller
            name={id}
            rules={{
                required: !disabled && required,
                validate: (value) => {
                    if (value !== null && value !== undefined && !disabled) {
                        if (!isValid(value)) {
                            return ValidationStates.INVALID;
                        }
                        if (
                            minDate &&
                            !isSameDay(value, minDate) &&
                            isBefore(value, minDate)
                        ) {
                            return ValidationStates.BEFORE;
                        }
                        if (
                            maxDate &&
                            !isSameDay(value, maxDate) &&
                            isAfter(value, maxDate)
                        ) {
                            return ValidationStates.AFTER;
                        }
                    }
                    return true;
                },
            }}
            control={control}
            render={({field, fieldState}) => (
                <>
                    <DatePickerField
                        date={field.value}
                        onChange={field.onChange}
                        minDate={minDate}
                        maxDate={maxDate}
                        label={label}
                        disabled={disabled}
                        error={fieldState.error}
                        required={required}
                        // customErrorMessages={customErrorMessages}
                    />
                    {fieldState.error && fieldState.error.type === 'required' && (
                        <p className="error" role="alert">
                            <WarningIcon />
                            {customErrorMessages?.required || t('valitse-paivamaara')}
                        </p>
                    )}
                    {fieldState.error && fieldState.error.type === 'validate' && (
                        <p className="error" role="alert">
                            <WarningIcon />
                            {validationMessage(fieldState.error.message)}
                        </p>
                    )}
                </>
            )}
        />
    );
}

export default DateField;
