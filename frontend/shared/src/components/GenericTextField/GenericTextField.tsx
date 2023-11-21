import {ChangeEvent, useId, Dispatch, SetStateAction} from 'react';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';
import {FieldError} from 'react-hook-form';
import WarningIcon from '@mui/icons-material/Warning';

interface GenericTextFieldProps {
    value: string;
    label: string;
    required?: boolean;
    showLabel?: boolean;
    autoComplete?: boolean;
    autoFocus?: boolean;
    fullWidth?: boolean;
    multiLine?: boolean;
    multiLineResize?: boolean;
    placeholder?: string;
    searchIcon?: boolean;
    clearButton?: boolean;
    disabled?: boolean;
    onChange: ((event: string) => void) | Dispatch<SetStateAction<string>>;
    error?: FieldError | Boolean;
    errorMessage?: string;
}

function GenericTextField({
    value = '',
    label,
    required,
    showLabel = true,
    autoComplete = true,
    autoFocus,
    fullWidth,
    multiLine,
    multiLineResize,
    placeholder,
    searchIcon,
    clearButton = false,
    disabled = false,
    onChange,
    error = false,
    errorMessage = '',
}: GenericTextFieldProps) {
    const labelAssociation = useId();

    const errorClass = error ? 'error' : '';

    return (
        <>
            <label
                htmlFor={labelAssociation}
                className={showLabel ? 'label-for-inputfield' : 'label-visually-hidden'}
            >
                {label}
                {required ? ' *' : ''}
            </label>

            <div>
                <TextField
                    placeholder={placeholder}
                    id={labelAssociation}
                    required={required}
                    fullWidth={fullWidth}
                    autoComplete={autoComplete ? 'on' : 'off'}
                    autoFocus={autoFocus}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => {
                        onChange(e.target.value);
                    }}
                    value={value}
                    multiline={multiLine}
                    minRows={multiLine ? 3 : 1}
                    className={
                        multiLineResize ? `input-resize ${errorClass}` : `${errorClass}`
                    }
                    disabled={disabled}
                    InputProps={{
                        startAdornment: searchIcon && (
                            <InputAdornment position="start">
                                <SearchIcon />
                            </InputAdornment>
                        ),
                        endAdornment: clearButton && value && (
                            <IconButton
                                className="textfield-button icon-button"
                                onClick={() => {
                                    onChange('');
                                }}
                            >
                                <CloseIcon />
                            </IconButton>
                        ),
                    }}
                />
                {error && (
                    <p className="error" role="alert">
                        <WarningIcon />
                        {errorMessage}
                    </p>
                )}
            </div>
        </>
    );
}

export default GenericTextField;
