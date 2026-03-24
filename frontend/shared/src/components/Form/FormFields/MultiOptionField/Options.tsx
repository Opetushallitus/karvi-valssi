import {ChangeEventHandler, useState} from 'react';
import {useTranslation} from 'react-i18next';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import Radio from '@mui/material/Radio';
import Collapse from '@mui/material/Collapse';
import FormGroup from '@mui/material/FormGroup';
import RadioGroup from '@mui/material/RadioGroup';
import WarningIcon from '@mui/icons-material/Warning';
import {Control, useFormState} from 'react-hook-form';
import {MaxLengths} from '@cscfi/shared/utils/validators';
import SingleField from '../SingleField/SingleField';
import {
    CheckBoxType,
    FollowupQuestionsType,
    HiddenType,
    RadioButtonType,
    TextType,
} from '../../../../services/Data/Data-service';
import InfoToggle from '../../../InfoToggle/InfoToggle';
import InputTypes from '../../../InputType/InputTypes';
import styles from '../../Form.module.css';

interface OptionsProps {
    id: string;
    values: any;
    followupQuestions: FollowupQuestionsType;
    answerOptions: CheckBoxType[] | RadioButtonType[];
    type: string;
    onChange: ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>;
    control: Control;
    hidden?: HiddenType;
    language?: string;
}

function Options({
    id,
    values,
    followupQuestions,
    answerOptions,
    type,
    onChange,
    control,
    hidden = HiddenType.notHidden,
    language,
}: OptionsProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['form']);
    const langKey = language ? language : (lang as keyof TextType);
    const [descOpen, setDescOpen] = useState<string[]>([]);
    const {ref} = control.register(id);
    const [kyselyId] = id.split('_');
    const {errors} = useFormState({control});

    const options = answerOptions?.map(
        (multiSelectItem: CheckBoxType | RadioButtonType) => {
            const kysymysId = `${id}_${multiSelectItem.id}`;
            const singleCheckbox: string = multiSelectItem.id.toString();
            const value = values?.[singleCheckbox];

            const followupquestionId = `${kyselyId}_${followupQuestions?.[multiSelectItem?.id]?.id}`;
            const optionFieldErrors = errors[followupquestionId];

            return (
                <div key={multiSelectItem.id}>
                    <div className={styles['option-label-wrapper']}>
                        <FormControlLabel
                            htmlFor={kysymysId}
                            className={styles['checkbox-label']}
                            key={multiSelectItem.id}
                            control={
                                type === InputTypes.checkbox ? (
                                    <Checkbox
                                        id={kysymysId}
                                        key={multiSelectItem.id}
                                        checked={value === true}
                                        onChange={onChange}
                                        name={kysymysId}
                                        className={hidden ? 'hidden' : ''}
                                    />
                                ) : (
                                    <Radio
                                        id={kysymysId}
                                        key={multiSelectItem.id}
                                        value={kysymysId}
                                        checked={value === true}
                                        onChange={onChange}
                                        className={hidden ? 'hidden' : ''}
                                    />
                                )
                            }
                            label={multiSelectItem.title?.[langKey]}
                        />

                        {followupQuestions?.[multiSelectItem.id] &&
                            followupQuestions[multiSelectItem.id]?.insta && (
                                <>
                                    <div className={styles['instant-followup']}>
                                        <SingleField
                                            type={
                                                (followupQuestions[multiSelectItem.id]
                                                    .inputType as unknown as InputTypes) ||
                                                InputTypes.singletext
                                            }
                                            id={followupquestionId}
                                            control={control}
                                            ariaLabel={multiSelectItem.title?.[langKey]}
                                            disabled={value === false}
                                            required={value !== false}
                                            autoFocus
                                            blankOnDisabled
                                            maxLength={MaxLengths.vastausJatkokysymys}
                                        />
                                    </div>
                                    {optionFieldErrors &&
                                        optionFieldErrors.type === 'required' && (
                                            <p className="error" role="alert">
                                                <WarningIcon />
                                                {t('pakollinen-kentta', {
                                                    lng: langKey,
                                                    ns: 'error',
                                                })}
                                            </p>
                                        )}
                                    {optionFieldErrors &&
                                        optionFieldErrors.type === 'maxLength' && (
                                            <p className="error" role="alert">
                                                <WarningIcon />
                                                {t('invalid-maxLength', {
                                                    ns: 'error',
                                                    lng: langKey,
                                                    maxLength:
                                                        MaxLengths.vastausJatkokysymys,
                                                })}
                                            </p>
                                        )}
                                </>
                            )}
                        {multiSelectItem.description?.[langKey] && (
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
                                controlId={`${multiSelectItem.id}_desc`}
                                ariaLabelTxt={multiSelectItem.description?.[langKey]}
                            />
                        )}
                    </div>

                    <Collapse
                        in={descOpen.includes(singleCheckbox)}
                        id={`${multiSelectItem.id}_desc`}
                    >
                        <p className={styles['checkbox-desc']}>
                            {multiSelectItem.description?.[langKey]}
                        </p>
                    </Collapse>
                </div>
            );
        },
    );

    return type === InputTypes.checkbox ? (
        <FormGroup ref={ref} aria-labelledby={id} role="group">
            {options}
        </FormGroup>
    ) : (
        <RadioGroup ref={ref} aria-labelledby={id}>
            {options}
        </RadioGroup>
    );
}

export default Options;
