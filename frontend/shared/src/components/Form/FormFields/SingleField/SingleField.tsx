import {useState} from 'react';
import {Control, Controller, FieldValues} from 'react-hook-form';
import WarningIcon from '@mui/icons-material/Warning';
import TextField from '@mui/material/TextField';
import Collapse from '@mui/material/Collapse';
import {useTranslation} from 'react-i18next';
import {isNumeric, isValidEmail} from '../../../../utils/validators';
import InputTypes from '../../../InputType/InputTypes';
import InfoToggle from '../../../InfoToggle/InfoToggle';
import styles from '../../Form.module.css';

interface SingleFieldProps {
    type: InputTypes;
    id: string;
    required: boolean;
    title?: string;
    descriptionDefaultOpen?: boolean;
    description?: string;
    fieldErrors?: FieldValues;
    control: Control;
}

/*
handle cases:
singletext -> normal TextField
multiline -> TextField with multiline and minRows props
numeric -> TextField with type=number.
 */
function SingleField({
    type,
    id,
    required,
    title,
    description,
    descriptionDefaultOpen = false,
    fieldErrors,
    control,
}: SingleFieldProps) {
    const [descOpen, setDescOpen] = useState<boolean>(descriptionDefaultOpen);
    const {t} = useTranslation(['error']);
    const {ref} = control.register(id);
    let labelStyles = 'label-for-inputfield';
    if (fieldErrors) {
        labelStyles += ' error';
    }
    return (
        <div className={styles['input-field']}>
            <label htmlFor={id} className={labelStyles}>
                {title && (
                    <>
                        {title} {required ? ' *' : ''}
                    </>
                )}
                {description && (
                    <InfoToggle
                        isOpen={descOpen}
                        onChange={() => {
                            setDescOpen(!descOpen);
                        }}
                    />
                )}
            </label>
            {description && (
                <Collapse in={descOpen}>
                    <p className="info">{description}</p>
                </Collapse>
            )}
            {type === InputTypes.singletext && (
                <Controller
                    name={id}
                    rules={{required}}
                    control={control}
                    render={({field: {onChange, value}}) => (
                        <TextField
                            className={fieldErrors ? 'error' : ''}
                            fullWidth
                            value={value || ''}
                            onChange={onChange} // send value to hook form
                            ref={ref}
                        />
                    )}
                />
            )}
            {type === InputTypes.multiline && (
                <Controller
                    name={id}
                    rules={{required}}
                    control={control}
                    render={({field: {onChange, value}}) => (
                        <TextField
                            className={fieldErrors ? 'error' : ''}
                            multiline
                            minRows={3}
                            fullWidth
                            value={value || ''}
                            onChange={onChange} // send value to hook form
                            ref={ref}
                        />
                    )}
                />
            )}
            {type === InputTypes.numeric && (
                <Controller
                    name={id}
                    rules={{
                        required,
                        pattern: isNumeric,
                    }}
                    control={control}
                    render={({field: {onChange, value}}) => (
                        <TextField
                            className={fieldErrors ? 'error' : ''}
                            value={value || ''}
                            onChange={onChange} // send value to hook form
                            ref={ref}
                        />
                    )}
                />
            )}
            {type === InputTypes.email && (
                <Controller
                    name={id}
                    rules={{
                        required,
                        pattern: isValidEmail,
                    }}
                    control={control}
                    render={({field: {onChange, value}}) => (
                        <TextField
                            className={fieldErrors ? 'error' : ''}
                            fullWidth
                            value={value || ''}
                            onChange={onChange} // send value to hook form
                            ref={ref}
                        />
                    )}
                />
            )}
            {fieldErrors && fieldErrors.type === 'required' && (
                <p className="error" role="alert">
                    <WarningIcon />
                    {t('pakollinen-kentta')}
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
        </div>
    );
}

export default SingleField;
