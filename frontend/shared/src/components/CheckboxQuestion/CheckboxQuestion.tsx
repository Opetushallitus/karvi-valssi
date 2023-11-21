import {KeyboardEvent, useState} from 'react';
import IconButton from '@mui/material/IconButton';
import RemoveIcon from '@mui/icons-material/Remove';
import AddIcon from '@mui/icons-material/Add';
import Button from '@mui/material/Button';
import {useTranslation} from 'react-i18next';
import {capitalize} from '../../utils/helpers';
import LanguageTitle from '../LanguageTitle/LanguageTitle';
import GenericText from '../GenericText/GenericText';
import {CheckBoxType, StatusType, TextType} from '../../services/Data/Data-service';
import DescriptionText from '../DescriptionText/DescriptionText';
import styles from './CheckboxQuestion.module.css';

interface CheckboxQuestionProps {
    title: TextType;
    description: TextType;
    answerOptions: Array<CheckBoxType>;
    handleChange: Function;
    published: StatusType;
}

function CheckboxQuestion({
    title,
    description,
    answerOptions,
    handleChange,
    published,
}: CheckboxQuestionProps) {
    const {t} = useTranslation(['kysely']);
    const [newAnswerOption, setNewAnswerOption] = useState(false); // to set focus when adding
    const addNewCheckbox = () => {
        const checkboxOptionId = answerOptions.length
            ? answerOptions[answerOptions.length - 1].id + 1
            : 1;
        const newList = [
            ...answerOptions,
            {
                id: checkboxOptionId,
                title: {fi: '', sv: ''},
                description: {fi: '', sv: ''},
                checked: false,
            },
        ];
        handleChange({answerOptions: newList});
        setNewAnswerOption(true);
    };

    const removeCheckbox = (index: number) => {
        const newList = answerOptions.filter((item, i) => index !== i);
        handleChange({answerOptions: newList});
    };

    const pressRemoveCheckbox = (
        event: KeyboardEvent<HTMLInputElement>,
        index: number,
    ) => {
        if (event.key === 'Enter') {
            removeCheckbox(index);
        }
    };

    const onChangeAnswerOption =
        (index: number, property: 'title' | 'description') =>
        (valueFromInput: TextType) => {
            const newList = answerOptions.map((item, i) => {
                if (index === i) {
                    return {
                        ...item,
                        [property]: {fi: valueFromInput.fi, sv: valueFromInput.sv},
                    };
                }
                return item;
            });
            handleChange({answerOptions: newList});
        };

    const onTitleChange = (valueFromInputField: TextType) => {
        handleChange({title: valueFromInputField});
    };
    const onDescriptionChange = (valueFromInputField: TextType) => {
        handleChange({description: valueFromInputField});
    };

    return (
        <div>
            <LanguageTitle />

            <GenericText
                value={title}
                fullWidth
                autoComplete={false}
                autoFocus
                label={t('otsikko')}
                onChange={onTitleChange}
                required
            />

            <DescriptionText value={description} onChange={onDescriptionChange} />

            <div className={styles['answer-options']}>
                {answerOptions.length !== 0 && t('vastausvaihtoehdot')}

                {answerOptions.map((answerOption, i) => {
                    const labeltext = `${capitalize(t('vastausvaihtoehto'))} ${i + 1}`;
                    return (
                        <div key={answerOption.id}>
                            <div className={styles['answer-option-row']}>
                                <div className={styles['answer-option-row__input']}>
                                    <GenericText
                                        label={labeltext}
                                        value={answerOption.title}
                                        fullWidth
                                        autoComplete={false}
                                        autoFocus={newAnswerOption}
                                        onChange={onChangeAnswerOption(i, 'title')}
                                        controls={published === StatusType.luonnos}
                                    />
                                </div>
                                {published === StatusType.luonnos && (
                                    <div className={styles['answer-option-row__remove']}>
                                        <div
                                            onClick={() => removeCheckbox(i)}
                                            onKeyDown={(
                                                event: KeyboardEvent<HTMLInputElement>,
                                            ) => pressRemoveCheckbox(event, i)}
                                            role="button"
                                            tabIndex={0}
                                        >
                                            <IconButton
                                                color="inherit"
                                                aria-label="remove answer option"
                                                component="span"
                                            >
                                                <RemoveIcon
                                                    className={styles['remove-icon']}
                                                />
                                            </IconButton>
                                        </div>
                                    </div>
                                )}
                            </div>
                            <div className={styles['answer-option-desc']}>
                                <DescriptionText
                                    value={answerOption.description}
                                    onChange={onChangeAnswerOption(i, 'description')}
                                />
                            </div>
                        </div>
                    );
                })}
                {published === StatusType.luonnos && (
                    <div>
                        <Button
                            className="link-alike"
                            onClick={addNewCheckbox}
                            startIcon={<AddIcon />}
                        >
                            {t('lisaa-uusi-vastausvaihtoehto')}
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default CheckboxQuestion;
