import {useTranslation} from 'react-i18next';
import {DatePicker, LocalizationProvider} from '@mui/x-date-pickers';
import {AdapterDateFns} from '@mui/x-date-pickers/AdapterDateFns';
import {isDate, toDate} from 'date-fns';
import {FieldError} from 'react-hook-form';
import {getDateFnsLocale} from '../../utils/helpers';
import styles from './DatePickerField.module.css';

interface DatePickerFieldProps {
    date?: Date | null | undefined;
    minDate?: Date | number;
    maxDate?: Date | number;
    onChange: (date: Date | null | undefined) => void;
    label?: string;
    required?: boolean;
    disabled?: boolean;
    error?: FieldError | boolean;
}

function DatePickerField({
    date = null,
    minDate,
    maxDate,
    onChange,
    label,
    required = false,
    disabled = false,
    error = false,
}: DatePickerFieldProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['datepicker']);

    const placeholderText = t('placeholder').split('.');

    const localePlaceholders = (): {} => {
        if (placeholderText.length === 3)
            return {
                fieldYearPlaceholder: (params) =>
                    placeholderText[2][0].charAt(0).repeat(params.digitAmount),
                fieldMonthPlaceholder: (params) =>
                    params.contentType === 'letter'
                        ? placeholderText[1].charAt(0).repeat(4)
                        : placeholderText[1].charAt(0).repeat(2),
                fieldDayPlaceholder: () => placeholderText[0].charAt(0).repeat(2),
            };
        // fallback:
        return {
            fieldYearPlaceholder: (params) => 'v'.repeat(params.digitAmount),
            fieldMonthPlaceholder: (params) =>
                params.contentType === 'letter' ? 'kkkk' : 'kk',
            fieldDayPlaceholder: () => 'pp',
        };
    };

    return (
        <>
            {label && (
                <label
                    htmlFor={`id_${label}`}
                    className={`label-for-inputfield${error ? ' error' : ''}`}
                >
                    {label}
                    {required ? ' *' : ''}
                </label>
            )}

            <LocalizationProvider
                dateAdapter={AdapterDateFns}
                adapterLocale={getDateFnsLocale(lang)}
                localeText={localePlaceholders()}
            >
                <DatePicker
                    className={styles['date-field']}
                    onChange={(newDate) =>
                        isDate(newDate) ? onChange(toDate(newDate!)) : onChange(null)
                    }
                    disabled={disabled}
                    format="dd.MM.yyyy"
                    value={date}
                    minDate={minDate}
                    maxDate={maxDate}
                    slotProps={{
                        textField: {
                            className: styles['date-field'],
                            type: 'none',
                        },
                    }}
                />
            </LocalizationProvider>
        </>
    );
}

export default DatePickerField;
