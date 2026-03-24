import {useTranslation} from 'react-i18next';
import {Select, SelectChangeEvent} from '@mui/material';
import MenuItem from '@mui/material/MenuItem';
import {CSSProperties} from 'react';
import styles from './DropDownField.module.css';

export interface DropDownItem {
    value: string;
    name: string;
    disabled?: boolean;
}

interface DropDownFieldProps {
    id: string;
    label?: string;
    labelStyles?: CSSProperties;
    onChange: (value: string) => void; // DropDownItem value
    options: DropDownItem[];
    value?: string; // DropDownItem value
    translationNs?: string;
    required?: boolean;
    disabled?: boolean;
    tightLabel?: boolean;
    className?: string;
}

function DropDownField({
    id,
    label,
    labelStyles,
    onChange,
    options,
    value,
    translationNs = null,
    required = false,
    disabled = false,
    tightLabel = false,
    className,
}: DropDownFieldProps) {
    const {t} = useTranslation([(translationNs || 'dropdown') as string]);
    const labelClass = `${
        tightLabel ? styles['label-tight'] : null
    } label-for-inputfield`;

    const elementStyles = className
        ? `${className} ${styles['drop-down-root']}`
        : styles['drop-down-root'];

    return (
        <>
            {label && (
                <label style={labelStyles} htmlFor={id} className={labelClass}>
                    {label}
                    {required ? ' *' : ''}
                </label>
            )}
            <Select
                id={id}
                className={elementStyles}
                onChange={(event: SelectChangeEvent) => onChange(event.target.value)}
                disabled={disabled}
                value={value || options[0]?.value}
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
