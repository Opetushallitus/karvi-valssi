import {useState} from 'react';
import {Controller, FieldPath, FieldValues} from 'react-hook-form';
import WarningIcon from '@mui/icons-material/Warning';
import TextField from '@mui/material/TextField';
import Collapse from '@mui/material/Collapse';
import {isEmpty} from 'lodash';
import {useTranslation} from 'react-i18next';
import Tooltip from '@mui/material/Tooltip';
import {isNumeric, isValidEmail, isValidEmailList} from '../../../../utils/validators';
import InputTypes from '../../../InputType/InputTypes';
import InfoToggle from '../../../InfoToggle/InfoToggle';
import styles from '../../Form.module.css';

interface CustomErrorMessages {
    required?: string;
    maxLength?: string;
}

interface SingleFieldProps {
    type: InputTypes;
    id: string;
    required: boolean;
    title?: string;
    autoFocus?: boolean;
    disabled?: boolean;
    blankOnDisabled?: boolean;
    descriptionDefaultOpen?: boolean;
    description?: string;
    multiLineResize?: boolean;
    maxLength: number;
    fieldErrors?: FieldValues;
    ariaLabel?: string;
    customErrorMessages?: CustomErrorMessages;
    control: any; // Control<SomeFormType, any>
}

/*
handle cases:
singletext -> normal TextField
multiline -> TextField with multiline and minRows props
numeric -> TextField with type=number.
 */

function ctrlPattern(inputType: InputTypes) {
    switch (inputType) {
        case InputTypes.numeric:
            return {pattern: isNumeric};
        case InputTypes.email:
            return {pattern: isValidEmail};
        case InputTypes.emailList:
            return {pattern: isValidEmailList};
        default:
            return {};
    }
}

function SingleField({
    type,
    id,
    required,
    title,
    autoFocus = false,
    disabled = false,
    blankOnDisabled = false,
    description,
    descriptionDefaultOpen = false,
    multiLineResize = false,
    maxLength,
    fieldErrors,
    ariaLabel = '',
    customErrorMessages,
    control,
}: SingleFieldProps) {
    const [descOpen, setDescOpen] = useState<boolean>(descriptionDefaultOpen);
    const [numericTooltip, setNumericTooltip] = useState<boolean>(false);
    const {t} = useTranslation(['error']);
    const {ref} = control.register(id as FieldPath<any>);
    const errorClass = fieldErrors ? ' error' : '';
    const resizeClass = multiLineResize ? ' input-resize' : '';

    // isEmpty(title) voisi käyttää muuallakin lomakkeen kentissä

    const inputPropsBase = {autoComplete: 'off', 'aria-required': required};

    return (
        <div className={styles['input-field']}>
            {/* TK teki tässä jonkun jutun, joka rikko testit. Varmaan tarkotuksena poistaa */}
            {/* label, jos tää on "muu, mikä" -kenttä. */}
            <label htmlFor={id} className={`label-for-inputfield ${errorClass}`}>
                {!isEmpty(title) && (
                    <>
                        {title} {required ? ' *' : ''}
                    </>
                )}
                {!isEmpty(description) && (
                    <InfoToggle
                        isOpen={descOpen}
                        onChange={() => {
                            setDescOpen(!descOpen);
                        }}
                        controlId={`${id}_desc`}
                        ariaLabelTxt={title}
                    />
                )}
            </label>
            {!isEmpty(description) && (
                <Collapse in={descOpen} id={`${id}_desc`}>
                    <p className="info">{description}</p>
                </Collapse>
            )}

            <Controller
                name={id}
                rules={{required, ...ctrlPattern(type), ...(maxLength && {maxLength})}}
                control={control}
                render={({field: {onChange, value}}) => {
                    switch (type) {
                        case InputTypes.singletext:
                            return (
                                <TextField
                                    id={id}
                                    value={
                                        (!(blankOnDisabled && disabled) && value) || ''
                                    }
                                    onChange={onChange}
                                    ref={ref}
                                    className={errorClass}
                                    disabled={disabled}
                                    autoFocus={autoFocus}
                                    inputProps={{
                                        ...inputPropsBase,
                                        'aria-label': ariaLabel,
                                    }}
                                    fullWidth
                                />
                            );
                        case InputTypes.multiline:
                            return (
                                <TextField
                                    id={id}
                                    value={
                                        (!(blankOnDisabled && disabled) && value) || ''
                                    }
                                    onChange={onChange}
                                    ref={ref}
                                    className={`${resizeClass}${errorClass}`}
                                    disabled={disabled}
                                    autoFocus={autoFocus}
                                    inputProps={inputPropsBase}
                                    fullWidth
                                    multiline
                                    minRows={3}
                                />
                            );
                        case InputTypes.numeric:
                            return (
                                <Tooltip
                                    title={numericTooltip && !disabled && t('syota-luku')}
                                    placement="top"
                                    disableHoverListener
                                >
                                    <TextField
                                        id={id}
                                        inputMode="numeric"
                                        value={
                                            (!(blankOnDisabled && disabled) && value) ||
                                            ''
                                        }
                                        onBlur={() => setNumericTooltip(false)}
                                        onChange={(e) => {
                                            const inputValue = e.target.value;
                                            // any number of digits + comma or dot + max 2 digits
                                            const numericPattern = /^\d*([.,]?\d{0,2})?$/;
                                            if (numericPattern.test(inputValue)) {
                                                onChange(inputValue);
                                                setNumericTooltip(false);
                                            } else {
                                                setNumericTooltip(true);
                                            }
                                        }}
                                        ref={ref}
                                        className={errorClass}
                                        disabled={disabled}
                                        autoFocus={autoFocus}
                                        inputProps={inputPropsBase}
                                    />
                                </Tooltip>
                            );
                        case InputTypes.email:
                            return (
                                <TextField
                                    id={id}
                                    value={value || ''}
                                    onChange={onChange}
                                    ref={ref}
                                    className={errorClass}
                                    disabled={disabled}
                                    autoFocus={autoFocus}
                                    inputProps={inputPropsBase}
                                    fullWidth
                                />
                            );
                        case InputTypes.emailList:
                            return (
                                <TextField
                                    id={id}
                                    value={value || ''}
                                    onChange={onChange}
                                    ref={ref}
                                    className={`${resizeClass}${errorClass}`}
                                    disabled={disabled}
                                    autoFocus={autoFocus}
                                    inputProps={inputPropsBase}
                                    fullWidth
                                    multiline
                                    minRows={3}
                                />
                            );
                        default:
                            return <p>invalid field type</p>;
                    }
                }}
            />

            {fieldErrors && fieldErrors.type === 'required' && (
                <p className="error" role="alert">
                    <WarningIcon />
                    {customErrorMessages?.required || t('pakollinen-kentta')}
                </p>
            )}
            {fieldErrors && fieldErrors.type === 'maxLength' && (
                <p className="error" role="alert">
                    <WarningIcon />
                    {customErrorMessages?.maxLength ||
                        t('invalid-maxLength', {maxLength})}
                </p>
            )}
            {fieldErrors &&
                fieldErrors.type === 'pattern' &&
                type === InputTypes.numeric && (
                    <p className="error" role="alert">
                        <WarningIcon />
                        {t('numeerinen-syote')}
                    </p>
                )}
            {fieldErrors &&
                fieldErrors.type === 'pattern' &&
                type === InputTypes.email && (
                    <p className="error" role="alert">
                        <WarningIcon />
                        {t('invalid-email')}
                    </p>
                )}
            {fieldErrors &&
                fieldErrors.type === 'pattern' &&
                type === InputTypes.emailList && (
                    <p className="error" role="alert">
                        <WarningIcon />
                        {t('invalid-email-list')}
                    </p>
                )}
        </div>
    );
}

export default SingleField;
