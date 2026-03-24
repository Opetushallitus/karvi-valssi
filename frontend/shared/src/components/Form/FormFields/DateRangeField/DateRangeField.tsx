import {notEmpty} from '@cscfi/shared/utils/helpers';
import {isDate, toDate} from 'date-fns';
import DateField, {CustomErrorMessages} from '../DateField/DateField';
import styles from '../../../DateRangePickerField/DateRangePickerField.module.css';

interface DateRangeFieldProps {
    idStartDate: string;
    idEndDate: string;
    rangeMin?: Date | number;
    rangeMax?: Date | number;
    labelStart?: string;
    labelEnd?: string;
    required?: boolean;
    disabled?: boolean;
    disableStartDate?: boolean;
    control: any; // Control<SomeFormType, any>
    customErrorMessagesStart?: CustomErrorMessages;
    customErrorMessagesEnd?: CustomErrorMessages;
}

function DateRangeField({
    idStartDate,
    idEndDate,
    rangeMin,
    rangeMax,
    labelStart,
    labelEnd,
    required = false,
    disabled = false,
    disableStartDate = false,
    customErrorMessagesStart,
    customErrorMessagesEnd,
    control,
}: DateRangeFieldProps) {
    return (
        <div className={styles['date-range-box']}>
            <div className={styles['date-range-item']}>
                <DateField
                    id={idStartDate}
                    control={control}
                    minDate={rangeMin}
                    maxDate={toDate(
                        Math.min(
                            ...[
                                // eslint-disable-next-line no-underscore-dangle
                                control._formValues[idEndDate]?.getTime(),
                                isDate(rangeMax)
                                    ? (rangeMax as Date).getTime()
                                    : rangeMax,
                            ].filter(notEmpty),
                        ) as number,
                    )}
                    label={labelStart}
                    required={required}
                    disabled={disabled || disableStartDate}
                    customErrorMessages={customErrorMessagesStart}
                />
            </div>
            <div className={styles['date-range-item']}>
                <DateField
                    id={idEndDate}
                    control={control}
                    minDate={toDate(
                        Math.max(
                            ...[
                                // eslint-disable-next-line no-underscore-dangle
                                control._formValues[idStartDate]?.getTime(),
                                isDate(rangeMax)
                                    ? (rangeMax as Date).getTime()
                                    : rangeMax,
                            ].filter(notEmpty),
                        ) as number,
                    )}
                    maxDate={rangeMax}
                    label={labelEnd}
                    required={required}
                    disabled={disabled}
                    customErrorMessages={customErrorMessagesEnd}
                />
            </div>
        </div>
    );
}

export default DateRangeField;
