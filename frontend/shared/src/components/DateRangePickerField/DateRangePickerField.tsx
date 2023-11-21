import WarningIcon from '@mui/icons-material/Warning';
import {FieldError} from 'react-hook-form';
import {toDate} from 'date-fns';
import DatePickerField from '../DatePickerField/DatePickerField';
import styles from './DateRangePickerField.module.css';

interface DateRangePickerFieldProps {
    dateStart?: Date | number;
    dateEnd?: Date | number;
    rangeMin?: Date | number;
    rangeMax?: Date | number;
    onChangeStart: (date: Date | null) => void;
    onChangeEnd: (date: Date | null) => void;
    labelStart?: string;
    labelEnd?: string;
    required?: boolean;
    disabled?: boolean;
    errorStartDate?: FieldError | boolean;
    errorEndDate?: FieldError | boolean;
    errorStartDateMessage?: string;
    errorEndDateMessage?: string;
    disableStartDate?: boolean;
}

function DateRangePickerField({
    dateStart,
    dateEnd,
    rangeMin,
    rangeMax,
    onChangeStart,
    onChangeEnd,
    labelStart,
    labelEnd,
    required = false,
    disabled = false,
    errorStartDate = false,
    errorEndDate = false,
    errorStartDateMessage = '',
    errorEndDateMessage = '',
    disableStartDate = false,
}: DateRangePickerFieldProps) {
    return (
        <>
            <div className={styles['date-range-box']}>
                <div className={styles['date-range-item']}>
                    <DatePickerField
                        label={labelStart}
                        date={
                            (typeof dateStart === 'number'
                                ? toDate(dateStart)
                                : dateStart) || undefined
                        }
                        onChange={onChangeStart}
                        minDate={rangeMin}
                        maxDate={dateEnd}
                        required={required}
                        disabled={disabled || disableStartDate}
                        error={errorStartDate}
                    />
                </div>

                <div>
                    <DatePickerField
                        label={labelEnd}
                        date={
                            (typeof dateEnd === 'number' ? toDate(dateEnd) : dateEnd) ||
                            undefined
                        }
                        onChange={onChangeEnd}
                        minDate={dateStart}
                        maxDate={rangeMax}
                        required={required}
                        disabled={disabled}
                        error={errorEndDate}
                    />
                </div>
            </div>

            {errorStartDate && (
                <p className="error" role="alert">
                    <WarningIcon />
                    {errorStartDateMessage}
                </p>
            )}

            {errorEndDate && (
                <p className="error" role="alert">
                    <WarningIcon />
                    {errorEndDateMessage}
                </p>
            )}
        </>
    );
}

export default DateRangePickerField;
