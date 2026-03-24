import {
    KeyboardEvent,
    useCallback,
    useState,
    useEffect,
    Dispatch,
    SetStateAction,
} from 'react';
import RemoveIcon from '@mui/icons-material/Remove';
import AddIcon from '@mui/icons-material/Add';
import Button from '@mui/material/Button';
import {useTranslation} from 'react-i18next';
import FollowupQuestion from '@cscfi/shared/components/FollowupQuestion/FollowupQuestion';
import IconButton from '@mui/material/IconButton';
import InputTypes from '../InputType/InputTypes';
import {capitalize} from '../../utils/helpers';
import LanguageTitle from '../LanguageTitle/LanguageTitle';
import GenericText from '../GenericText/GenericText';
import {
    CheckBoxType,
    FollowupDataType,
    FollowupQuestionsType,
    KysymysType,
    StatusType,
    TextType,
} from '../../services/Data/Data-service';
import styles from './CheckboxQuestion.module.css';
import DescriptionText from '../DescriptionText/DescriptionText';

interface CheckboxQuestionProps {
    title: TextType;
    description: TextType;
    answerOptions: Array<CheckBoxType>;
    handleChange: (changeFromSubComponent: object) => void;
    existingKysymys: boolean;
    published: StatusType;
    inputType: InputTypes.checkbox | InputTypes.radio | InputTypes.dropdown;
    followUpData: FollowupQuestionsType;
    kysymykset: KysymysType[];
    showEnglish: boolean;
    ruotsiVaiEnglantiValittu: string;
    setRuotsiVaiEnglantiValittu: Dispatch<SetStateAction<string | null>>;
}

function CheckboxQuestion({
    title,
    description,
    answerOptions,
    handleChange,
    existingKysymys,
    published,
    inputType,
    followUpData,
    kysymykset,
    showEnglish,
    ruotsiVaiEnglantiValittu,
    setRuotsiVaiEnglantiValittu,
}: CheckboxQuestionProps) {
    const {t} = useTranslation(['kysely']);
    const [newAnswerOption, setNewAnswerOption] = useState(false); // to set focus when adding

    const emptyOptions = useCallback(
        (amount = 1) => {
            const nextId = answerOptions.length
                ? answerOptions[answerOptions.length - 1].id + 1
                : 1;
            const emptyOpts = [];
            const newOpt = (id: number) => ({
                id,
                title: showEnglish ? {fi: '', sv: '', en: ''} : {fi: '', sv: ''},
                description: showEnglish ? {fi: '', sv: '', en: ''} : {fi: '', sv: ''},
                checked: false,
            });
            for (let i = 0; i < amount; i += 1) {
                emptyOpts.push(newOpt(nextId + i));
            }
            return emptyOpts;
        },
        [answerOptions, showEnglish],
    );

    const addNewCheckbox = () => {
        const newList = [...answerOptions, ...emptyOptions()];
        handleChange({answerOptions: newList});
        setNewAnswerOption(true);
    };

    useEffect(() => {
        if (!existingKysymys && answerOptions.length === 0) {
            handleChange({
                answerOptions: emptyOptions(5),
            });
        }
    }, [answerOptions.length, emptyOptions, existingKysymys, handleChange, inputType]);

    const removeCheckbox = (index: number) => {
        const newList = answerOptions
            .filter((item, i) => index !== i)
            .map((item, i) => {
                item.id = i + 1; // To keep ID's starting from 1
                return item;
            });
        handleChange({answerOptions: newList});
    };

    const pressRemoveCheckbox = (
        event: KeyboardEvent<HTMLInputElement>,
        index: number,
    ) => {
        if (['Enter', ' '].includes(event.key)) {
            event.preventDefault();
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
                        [property]: showEnglish
                            ? {
                                  fi: valueFromInput.fi,
                                  sv: valueFromInput.sv,
                                  en: valueFromInput.en,
                              }
                            : {fi: valueFromInput.fi, sv: valueFromInput.sv},
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

    const onFollowUpDataChange = (idx: number, kysymys: FollowupDataType) => {
        if (kysymys.kysymysid !== null) {
            handleChange({
                followUpData: {
                    ...followUpData,
                    [idx]: {
                        ...([-1, -2].includes(kysymys.kysymysid)
                            ? {
                                  inputType: kysymys.inputType,
                              }
                            : {
                                  id: kysymys.kysymysid,
                                  inputType: kysymys.inputType,
                              }),
                    },
                },
            });
        } else {
            const {[idx]: _toBeDeleted, ...newData} = followUpData;
            handleChange({
                followUpData: newData,
            });
        }
    };

    return (
        <div>
            <LanguageTitle
                showEnglish={showEnglish}
                ruotsiVaiEnglantiValittu={ruotsiVaiEnglantiValittu}
                setRuotsiVaiEnglantiValittu={setRuotsiVaiEnglantiValittu}
            />

            <GenericText
                value={title}
                fullWidth
                autoComplete={false}
                autoFocus
                label={t('otsikko')}
                onChange={onTitleChange}
                required
                showEnglish={showEnglish}
                ruotsiVaiEnglantiValittu={ruotsiVaiEnglantiValittu}
            />

            <DescriptionText
                value={description}
                onChange={onDescriptionChange}
                showEnglish={showEnglish}
                ruotsiVaiEnglantiValittu={ruotsiVaiEnglantiValittu}
            />

            <div className={styles['answer-options-heading']}>
                {answerOptions.length !== 0 && t('vastausvaihtoehdot')}
            </div>

            <div className={styles['answer-options']}>
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
                                        showEnglish={showEnglish}
                                        ruotsiVaiEnglantiValittu={
                                            ruotsiVaiEnglantiValittu
                                        }
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
                            {[InputTypes.checkbox, InputTypes.radio].includes(
                                inputType,
                            ) && (
                                <div className={styles['answer-option-desc']}>
                                    <DescriptionText
                                        value={answerOption.description}
                                        onChange={onChangeAnswerOption(i, 'description')}
                                        showEnglish={showEnglish}
                                        ruotsiVaiEnglantiValittu={
                                            ruotsiVaiEnglantiValittu
                                        }
                                    />
                                    <FollowupQuestion
                                        followUpData={followUpData}
                                        onChange={onFollowUpDataChange}
                                        optionId={answerOption.id}
                                        kysymykset={kysymykset}
                                    />
                                </div>
                            )}
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
