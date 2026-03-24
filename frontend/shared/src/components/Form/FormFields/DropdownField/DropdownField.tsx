import {useState} from 'react';
import {Controller, FieldValues} from 'react-hook-form';
import FormControl from '@mui/material/FormControl';
import Collapse from '@mui/material/Collapse';
import WarningIcon from '@mui/icons-material/Warning';
import {useTranslation} from 'react-i18next';
import {Select, SelectChangeEvent} from '@mui/material';
import MenuItem from '@mui/material/MenuItem';
import {DropdownType, HiddenType, TextType} from '../../../../services/Data/Data-service';
import InfoToggle from '../../../InfoToggle/InfoToggle';
import styles from '../../Form.module.css';

interface DropdownFieldProps {
    id: string;
    required: boolean;
    title?: string;
    description?: string;
    answerOptions: DropdownType[];
    fieldErrors?: FieldValues;
    control: any; // Control<SomeFormType, any>
    hidden?: HiddenType;
}

function DropdownField({
    id,
    required,
    title,
    description,
    answerOptions,
    fieldErrors,
    control,
    hidden = HiddenType.notHidden,
}: DropdownFieldProps) {
    const [descOpen, setDescOpen] = useState<boolean>(false);
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['form']);

    const langKey = lang as keyof TextType;
    let labelStyles = 'label-for-inputfield';
    if (hidden) labelStyles += ' hidden';
    if (fieldErrors) labelStyles += ' error';

    return (
        <FormControl key={id} component="fieldset" className={styles['input-field']}>
            {title && (
                <label htmlFor={id} className={labelStyles}>
                    {title}
                    {required ? ' *' : ''}
                    {description && (
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
            )}
            {description && (
                <Collapse in={descOpen} id={`${id}_desc`}>
                    <p className="info">{description}</p>
                </Collapse>
            )}
            <div className={fieldErrors ? 'overall-error' : ''}>
                <Controller
                    name={id}
                    rules={{
                        validate: (value) => {
                            if (!required) {
                                return true;
                            }
                            const checkboxValues = Object.values(value);
                            return checkboxValues.includes(true);
                        },
                    }}
                    control={control}
                    render={({field: {onChange, value}}) => {
                        const ddOnChange = (e: SelectChangeEvent) => {
                            const nameParts = e.target.value.split('_');
                            const newValue = {...value};
                            for (let i = 0; i < answerOptions.length; i += 1) {
                                newValue[answerOptions[i].id] =
                                    parseInt(nameParts[2], 10) === answerOptions[i].id;
                            }
                            onChange(newValue);
                        };

                        const getValue = () => {
                            const selected = value
                                ? Object.keys(value).find((key) => value[key])
                                : 0;
                            return `${id}_${selected || 0}`;
                        };

                        return (
                            <Select
                                id={id}
                                className={styles['drop-down-root']}
                                onChange={ddOnChange}
                                value={getValue()}
                                fullWidth
                                displayEmpty
                            >
                                <MenuItem value={`${id}_0`} disabled={required}>
                                    {t('dropdown-placeholder-option', {ns: 'yleiset'})}
                                </MenuItem>

                                {answerOptions.map((option) => {
                                    const kysymysId = `${id}_${option.id}`;

                                    return (
                                        <MenuItem value={kysymysId} key={kysymysId}>
                                            {option.title?.[langKey]}
                                        </MenuItem>
                                    );
                                })}
                            </Select>
                        );
                    }}
                />
            </div>
            {fieldErrors && fieldErrors.type === 'validate' && (
                <p className="error" role="alert">
                    <WarningIcon />
                    {t('pakollinen-kentta', {ns: 'error'})}
                </p>
            )}
        </FormControl>
    );
}

export default DropdownField;
