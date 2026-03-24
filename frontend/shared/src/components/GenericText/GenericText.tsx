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
    disabled?: boolean;
    required?: boolean;
    controls?: boolean;
    showEnglish?: boolean;
    ruotsiVaiEnglantiValittu?: string;
}

function GenericText({
    value,
    fullWidth,
    autoComplete,
    autoFocus,
    label,
    onChange,
    disabled = false,
    required,
    controls = false,
    showEnglish,
    ruotsiVaiEnglantiValittu,
}: GenericTextProps) {
    const labelAssociation = useId();

    const handleChange =
        (lang) => (event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
            if (lang === 'fi') {
                onChange(
                    showEnglish
                        ? {fi: event.target.value, sv: value.sv, en: value.en}
                        : {fi: event.target.value, sv: value.sv},
                );
            } else if (lang === 'sv') {
                onChange(
                    showEnglish
                        ? {fi: value.fi, sv: event.target.value, en: value.en}
                        : {fi: value.fi, sv: event.target.value},
                );
            } else {
                onChange({fi: value.fi, sv: value.sv, en: event.target.value});
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
                        } ${disabled ? 'hidden' : null}`}
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
                        } ${disabled ? 'hidden' : null}`}
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
                    disabled={disabled}
                />
                {!showEnglish && (
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
                        disabled={disabled}
                    />
                )}
                {showEnglish && ruotsiVaiEnglantiValittu === 'ruotsi' && (
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
                        disabled={disabled}
                    />
                )}
                {showEnglish && ruotsiVaiEnglantiValittu === 'englanti' && (
                    <TextField
                        className={
                            controls
                                ? 'field-row-second-column-with-controls'
                                : 'field-row-second-column'
                        }
                        value={value.en}
                        fullWidth={fullWidth}
                        autoComplete={autoComplete ? 'on' : 'off'}
                        onChange={handleChange('en')}
                        disabled={disabled}
                    />
                )}
            </div>
        </>
    );
}

export default GenericText;
