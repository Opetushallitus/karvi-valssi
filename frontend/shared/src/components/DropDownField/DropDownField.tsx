import {useTranslation} from 'react-i18next';
import {Select, SelectChangeEvent} from '@mui/material';
import MenuItem from '@mui/material/MenuItem';
import styles from './DropDownField.module.css';

export interface DropDownItem {
    value: string;
    name: string;
    disabled?: boolean;
}

interface DropDownFieldProps {
    id: string;
    label?: string;
    onChange: (value: string) => void; // DropDownItem value
    options: DropDownItem[];
    value?: string; // DropDownItem value
    translationNs?: string;
    required?: boolean;
    disabled?: boolean;
}

function DropDownField({
    id,
    label,
    onChange,
    options,
    value,
    translationNs = null,
    required = false,
    disabled = false,
}: DropDownFieldProps) {
    const {t} = useTranslation([(translationNs || 'dropdown') as string]);
    return (
        <>
            {label && (
                <label htmlFor={id} className="label-for-inputfield">
                    {label}
                    {required ? ' *' : ''}
                </label>
            )}
            <Select
                id={id}
                className={styles['drop-down-root']}
                onChange={(event: SelectChangeEvent) => onChange(event.target.value)}
                disabled={disabled}
                value={value || options[0].value}
                fullWidth
            >
                {options.map((option) => (
                    <MenuItem
                        value={option.value}
                        key={option.value}
                        disabled={option.disabled}
                    >
                        {translationNs ? t(option.name) : option.name}
                    </MenuItem>
                ))}
            </Select>
        </>
    );
}

export default DropDownField;
