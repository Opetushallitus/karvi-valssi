import {ChangeEventHandler, useState} from 'react';
import {useTranslation} from 'react-i18next';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import Radio from '@mui/material/Radio';
import Collapse from '@mui/material/Collapse';
import FormGroup from '@mui/material/FormGroup';
import RadioGroup from '@mui/material/RadioGroup';
import {UseFormRegister} from 'react-hook-form';
import {
    CheckBoxType,
    GenericFormValueType,
    RadioButtonType,
    TextType,
} from '../../../../services/Data/Data-service';
import InfoToggle from '../../../InfoToggle/InfoToggle';
import InputTypes from '../../../InputType/InputTypes';
import styles from '../../Form.module.css';

interface OptionsProps {
    id: string;
    values: any;
    answerOptions: CheckBoxType[] | RadioButtonType[];
    type: string;
    onChange: ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>;
    register: UseFormRegister<GenericFormValueType>;
    hidden?: boolean;
}

function Options({
    id,
    values,
    answerOptions,
    type,
    onChange,
    register,
    hidden = false,
}: OptionsProps) {
    const {
        i18n: {language: lang},
    } = useTranslation(['form']);
    const langKey = lang as keyof TextType;
    const [descOpen, setDescOpen] = useState<string[]>([]);
    const {ref} = register(id);

    const options = answerOptions?.map(
        (multiSelectItem: CheckBoxType | RadioButtonType) => {
            const kysymysName = `${id}_${multiSelectItem.id}`;
            const singleCheckbox: string = multiSelectItem.id.toString();
            const value = values?.[singleCheckbox];
            return (
                <div key={multiSelectItem.id}>
                    <FormControlLabel
                        className={styles['checkbox-label']}
                        key={multiSelectItem.id}
                        control={
                            type === InputTypes.checkbox ? (
                                <Checkbox
                                    key={multiSelectItem.id}
                                    checked={value === true}
                                    onChange={onChange}
                                    name={kysymysName}
                                    className={hidden ? 'hidden' : ''}
                                />
                            ) : (
                                <Radio
                                    key={multiSelectItem.id}
                                    value={kysymysName}
                                    checked={value === true}
                                    onChange={onChange}
                                    className={hidden ? 'hidden' : ''}
                                />
                            )
                        }
                        label={multiSelectItem.title?.[langKey]}
                    />
                    {multiSelectItem.description?.[langKey] && (
                        <>
                            <InfoToggle
                                isOpen={descOpen.includes(singleCheckbox)}
                                onChange={() => {
                                    setDescOpen(
                                        descOpen.includes(singleCheckbox)
                                            ? descOpen.filter(
                                                  (item) => item !== singleCheckbox,
                                              )
                                            : [...descOpen, singleCheckbox],
                                    );
                                }}
                            />
                            <Collapse in={descOpen.includes(singleCheckbox)}>
                                <p className={styles['checkbox-desc']}>
                                    {multiSelectItem.description?.[langKey]}
                                </p>
                            </Collapse>
                        </>
                    )}
                </div>
            );
        },
    );

    return type === InputTypes.checkbox ? (
        <FormGroup ref={ref}>{options}</FormGroup>
    ) : (
        <RadioGroup ref={ref}>{options}</RadioGroup>
    );
}

export default Options;
