import {KeyboardEvent, useCallback, useEffect, useMemo, useState} from 'react';
import {useTranslation} from 'react-i18next';
import DropDownField from '@cscfi/shared/components/DropDownField/DropDownField';
import IconButton from '@mui/material/IconButton';
import RemoveIcon from '@mui/icons-material/Remove';
import {
    KysymysType,
    MatrixType,
    StatusType,
    TextType,
} from '@cscfi/shared/services/Data/Data-service';
import ArvoInputTypes from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {capitalize, uniqueNumber} from '@cscfi/shared/utils/helpers';
import Button from '@mui/material/Button';
import AddIcon from '@mui/icons-material/Add';
import {useObservable} from 'rxjs-hooks';
import {virkailijapalveluGetMatrixScales$} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import InputTypes from '@cscfi/shared/components/InputType/InputTypes';
import LanguageTitle from '../LanguageTitle/LanguageTitle';
import DescriptionText from '../DescriptionText/DescriptionText';
import GenericText from '../GenericText/GenericText';
import styles from './MatrixQuestion.module.css';

interface MatrixQuestionProps {
    title: TextType;
    description?: TextType;
    matrixQuestions: KysymysType[];
    handleChange: Function;
    handleScaleChange: Function;
    required: boolean;
    existingKysymys: boolean;
    published: StatusType;
    inputType: InputTypes.matrix_slider | InputTypes.matrix_radio;
}

function MatrixQuestion({
    title,
    description,
    matrixQuestions,
    handleChange,
    handleScaleChange,
    required,
    existingKysymys,
    published,
    inputType,
}: MatrixQuestionProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['kysely']);
    const [newQuestion, setNewQuestion] = useState(false);
    const firstQuestion = matrixQuestions.find((e) => !!e);
    const [answerType, setAnswerType] = useState<string>(firstQuestion?.answerType);
    const matrixScales = useObservable(() => virkailijapalveluGetMatrixScales$());

    const emptyQuestion = useCallback(
        () => ({
            id: uniqueNumber(),
            title: {fi: '', sv: ''},
            description: {fi: '', sv: ''},
            inputType,
            answerType,
            required,
        }),
        [answerType, inputType, required],
    );

    useEffect(() => {
        if (matrixScales?.length > 0 && !answerType) {
            const firstByOrder = matrixScales
                .sort((msa, msb) => msa.order_no - msb.order_no)
                .find((ms) => !!ms);
            setAnswerType(firstByOrder!.name);
        }
    }, [answerType, matrixScales]);

    useEffect(() => {
        if (!existingKysymys && matrixQuestions.length === 0 && answerType) {
            handleChange({
                matrixQuestions: [emptyQuestion(), emptyQuestion(), emptyQuestion()],
            });
        }
    }, [
        answerType,
        matrixScales,
        emptyQuestion,
        existingKysymys,
        handleChange,
        matrixQuestions.length,
    ]);

    useEffect(() => {
        if (existingKysymys) {
            handleScaleChange(answerType);
        }
    }, [answerType, existingKysymys, handleScaleChange]);

    const onTitleChange = (valueFromInputField: TextType) => {
        handleChange({title: valueFromInputField});
    };
    const onDescriptionChange = (valueFromInputField: TextType) => {
        handleChange({description: valueFromInputField});
    };

    const onAsteikkoChange = (val: string) => {
        setAnswerType(val as ArvoInputTypes);
        const newList = matrixQuestions.map((item) => ({
            ...item,
            answerType: val,
        }));
        handleScaleChange(val);
        handleChange({matrixQuestions: newList});
    };

    const addNewQuestion = () => {
        const newList = [...matrixQuestions, emptyQuestion()];
        handleChange({matrixQuestions: newList});
        setNewQuestion(true);
    };

    const onChangeQuestion =
        (index: number, property: 'title' | 'description') =>
        (valueFromInput: TextType) => {
            const newList = matrixQuestions.map((item, i) => {
                if (index === i) {
                    return {
                        ...item,
                        [property]: {fi: valueFromInput.fi, sv: valueFromInput.sv},
                    };
                }
                return item;
            });
            handleChange({matrixQuestions: newList});
        };

    const removeQuestion = (index: number) => {
        const newList = matrixQuestions.filter((item, i) => index !== i);
        handleChange({matrixQuestions: newList});
    };

    const pressRemoveQuestion = (
        event: KeyboardEvent<HTMLInputElement>,
        index: number,
    ) => {
        if (event.key === 'Enter') {
            removeQuestion(index);
        }
    };

    const scaleOptions = (sc: MatrixType) => {
        const scales = sc?.scale.map((s) => s[lang]).join(' - ');
        const eos = capitalize(sc?.eos_value[lang]);
        return [scales, eos].join(' + ');
    };

    const scale = useMemo(
        () => matrixScales && matrixScales.find((ms) => ms.name === answerType),
        [answerType, matrixScales],
    );

    if (scale === null) {
        return null;
    }

    return (
        <>
            <div className={styles['matrix-scale-options']}>
                {existingKysymys ? (
                    <>
                        <label
                            htmlFor="matriisin-asteikko"
                            className="label-for-inputfield"
                        >
                            {t('matriisin-asteikko')}
                        </label>
                        <div id="matriisin-asteikko">
                            {scale ? scaleOptions(scale) : t('asteikkoa-ei-loydy')}
                        </div>
                    </>
                ) : (
                    <DropDownField
                        id="matriisin-asteikko"
                        value={answerType}
                        label={t('matriisin-asteikko')}
                        options={matrixScales.map((option) => ({
                            value: option.name,
                            name: `${scaleOptions(option)}`,
                        }))}
                        onChange={onAsteikkoChange}
                    />
                )}
            </div>

            <LanguageTitle />

            <GenericText
                value={title}
                fullWidth
                autoComplete={false}
                autoFocus
                label={t<string>('otsikko-label', {ns: 'yleiset'})}
                onChange={onTitleChange}
                required
            />

            <DescriptionText value={description} onChange={onDescriptionChange} />

            <div className={styles['answer-options']}>
                {matrixQuestions.length !== 0 && t('vaittamat')}
                <br />
                {matrixQuestions.map((matrixQuestion, i) => {
                    const labeltext = `${capitalize(t('kysymys'))} ${i + 1}`;
                    return (
                        <div key={matrixQuestion.id}>
                            <div className={styles['answer-option-row']}>
                                <div className={styles['answer-option-row__input']}>
                                    <GenericText
                                        label={labeltext}
                                        value={matrixQuestion.title}
                                        fullWidth
                                        autoComplete={false}
                                        autoFocus={newQuestion}
                                        onChange={onChangeQuestion(i, 'title')}
                                        controls={published === StatusType.luonnos}
                                    />
                                </div>
                                {published === StatusType.luonnos && (
                                    <div className={styles['answer-option-row__remove']}>
                                        <div
                                            onClick={() => removeQuestion(i)}
                                            onKeyDown={(
                                                event: KeyboardEvent<HTMLInputElement>,
                                            ) => pressRemoveQuestion(event, i)}
                                            role="button"
                                            tabIndex={0}
                                        >
                                            <IconButton
                                                color="inherit"
                                                aria-label="remove question"
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
                                    value={matrixQuestion.description}
                                    onChange={onChangeQuestion(i, 'description')}
                                />
                            </div>
                        </div>
                    );
                })}
                {published === StatusType.luonnos && (
                    <div>
                        <Button
                            className="link-alike"
                            onClick={addNewQuestion}
                            startIcon={<AddIcon />}
                        >
                            {t('lisaa-uusi-vaittama')}
                        </Button>
                    </div>
                )}
            </div>
        </>
    );
}

export default MatrixQuestion;
