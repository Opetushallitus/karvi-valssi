import {ChangeEvent, useId} from 'react';
import TextField from '@mui/material/TextField';
import {TextType} from '@cscfi/shared/services/Data/Data-service';

interface GenericTextProps {
    value: TextType;
    fullWidth?: boolean;
    autoComplete?: boolean;
    autoFocus?: boolean;
    label?: string;
    onChange: (valueFromInputField: TextType) => void;
    required?: boolean;
    controls?: boolean;
}

function GenericText({
    value,
    fullWidth,
    autoComplete,
    autoFocus,
    label,
    onChange,
    required,
    controls = false,
}: GenericTextProps) {
    const labelAssociation = useId();

    const handleChange =
        (lang) => (event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
            if (lang === 'fi') {
                onChange({fi: event.target.value, sv: value.sv});
            } else {
                onChange({fi: value.fi, sv: event.target.value});
            }
        };

    return (
        <>
            {label && (
                <div className="field-row">
                    <label
                        htmlFor={labelAssociation}
                        className={`label-for-inputfield ${
                            controls
                                ? 'field-row-first-column-with-controls'
                                : 'field-row-first-column'
                        }`}
                    >
                        {label}
                        {required ? ' *' : ''}
                    </label>
                    <label
                        htmlFor={labelAssociation}
                        className={`label-for-inputfield ${
                            controls
                                ? 'field-row-second-column-with-controls'
                                : 'field-row-second-column'
                        }`}
                    >
                        {label}
                        {required ? ' *' : ''}
                    </label>
                </div>
            )}
            <div className="field-row">
                <TextField
                    className={
                        controls
                            ? 'field-row-first-column-with-controls'
                            : 'field-row-first-column'
                    }
                    value={value.fi}
                    fullWidth={fullWidth}
                    autoComplete={autoComplete ? 'on' : 'off'}
                    autoFocus={autoFocus}
                    onChange={handleChange('fi')}
                />
                <TextField
                    className={
                        controls
                            ? 'field-row-second-column-with-controls'
                            : 'field-row-second-column'
                    }
                    value={value.sv}
                    fullWidth={fullWidth}
                    autoComplete={autoComplete ? 'on' : 'off'}
                    onChange={handleChange('sv')}
                />
            </div>
        </>
    );
}

export default GenericText;
