import {
    Dispatch,
    KeyboardEvent,
    SetStateAction,
    useCallback,
    useEffect,
    useMemo,
    useState,
} from 'react';
import {useTranslation} from 'react-i18next';
import DropDownField from '@cscfi/shared/components/DropDownField/DropDownField';
import IconButton from '@mui/material/IconButton';
import RemoveIcon from '@mui/icons-material/Remove';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import ArvoInputTypes, {
    KysymysType,
    MatrixType,
    StatusType,
    TextType,
} from '@cscfi/shared/services/Data/Data-service';
import {capitalize, uniqueNumber} from '@cscfi/shared/utils/helpers';
import Button from '@mui/material/Button';
import AddIcon from '@mui/icons-material/Add';
import {useObservableState} from 'observable-hooks';
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
    handleChange: (changeFromSubComponent: any) => void;
    handleScaleChange: (val: string) => void;
    required: boolean;
    existingKysymys: boolean;
    published: StatusType;
    inputType: InputTypes.matrix_slider | InputTypes.matrix_radio;
    showEnglish: boolean;
    ruotsiVaiEnglantiValittu: string;
    setRuotsiVaiEnglantiValittu: Dispatch<SetStateAction<string | null>>;
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
    showEnglish,
    ruotsiVaiEnglantiValittu,
    setRuotsiVaiEnglantiValittu,
}: MatrixQuestionProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['kysely']);

    const [newQuestion, setNewQuestion] = useState(false);

    const firstQuestion = matrixQuestions.find((e) => !!e);

    // Käyttäjän valinta – EI oletuksen asettamista efektissä.
    const [answerType, setAnswerType] = useState<string | undefined>(
        firstQuestion?.answerType,
    );

    // Asteikot palvelusta (ulkoinen lähde)
    const [matrixScales] = useObservableState(
        () => virkailijapalveluGetMatrixScales$(),
        [],
    );

    // Lajiteltu asteikkolista -> oletustyyppi
    const sortedScales = useMemo(
        () => (matrixScales ?? []).slice().sort((a, b) => a.order_no - b.order_no),
        [matrixScales],
    );
    const defaultFromScales = sortedScales[0]?.name;

    // Lopullinen käytettävä arvo: käyttäjän valinta -> skaalan oletus -> rivikysymyksen arvo
    const effectiveAnswerType =
        answerType ?? firstQuestion?.answerType ?? defaultFromScales;

    const emptyQuestion = useCallback(
        () => ({
            id: uniqueNumber(),
            title: showEnglish ? {fi: '', sv: '', en: ''} : {fi: '', sv: ''},
            description: showEnglish ? {fi: '', sv: '', en: ''} : {fi: '', sv: ''},
            inputType,
            answerType: effectiveAnswerType, // käytä laskettua arvoa
            required,
        }),
        [effectiveAnswerType, inputType, required, showEnglish],
    );

    // Luo oletus‑alirivit, kun luodaan uutta kysymystä ensimmäistä kertaa ja asteikko tiedossa
    useEffect(() => {
        if (!existingKysymys && matrixQuestions.length === 0 && effectiveAnswerType) {
            handleChange({
                matrixQuestions: [emptyQuestion(), emptyQuestion(), emptyQuestion()],
            });
        }
    }, [
        existingKysymys,
        matrixQuestions.length,
        effectiveAnswerType,
        emptyQuestion,
        handleChange,
    ]);

    // Ilmoita asteikosta vanhemmalle kun arvo selviää/muuttuu (ei setStatea)
    useEffect(() => {
        if (existingKysymys && effectiveAnswerType) {
            handleScaleChange(effectiveAnswerType);
        }
    }, [existingKysymys, effectiveAnswerType, handleScaleChange]);

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
            handleChange({matrixQuestions: newList});
        };

    const removeSubQuestion = (index: number) => {
        const newList = matrixQuestions.filter((_item, i) => index !== i);
        handleChange({matrixQuestions: newList});
    };

    const hideSubQuestion = (index: number) => {
        const newList = matrixQuestions.map((item, i) => {
            if (index === i) {
                return {
                    ...item,
                    hidden: !item.hidden,
                    required: !item.hidden ? false : required,
                };
            }
            return item;
        });
        handleChange({matrixQuestions: newList});
    };

    const pressRemoveQuestion = (
        event: KeyboardEvent<HTMLInputElement>,
        index: number,
    ) => {
        if (event.key === 'Enter') {
            removeSubQuestion(index);
        }
    };

    const scaleOptions = (sc: MatrixType) => {
        const scales = sc?.scale.map((s) => s[lang]).join(' - ');
        const eos = capitalize(sc?.eos_value[lang]);
        return [scales, eos].join(' + ');
    };

    const scale = useMemo(
        () => matrixScales?.find((ms) => ms.name === effectiveAnswerType) ?? null,
        [effectiveAnswerType, matrixScales],
    );

    if (!matrixScales?.length) {
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
                    matrixScales.length > 0 && (
                        <DropDownField
                            id="matriisin-asteikko"
                            value={effectiveAnswerType ?? ''}
                            label={t('matriisin-asteikko')}
                            options={matrixScales.map((option) => ({
                                value: option.name,
                                name: `${scaleOptions(option)}`,
                            }))}
                            onChange={onAsteikkoChange}
                        />
                    )
                )}
            </div>

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
                label={t('otsikko-label', {ns: 'yleiset'})}
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
                {matrixQuestions.length !== 0 && t('vaittamat')}
            </div>

            <div className={styles['answer-options']}>
                {matrixQuestions.map((matrixSubQuestion, i) => {
                    const labeltext = `${capitalize(t('kysymys'))} ${i + 1}`;
                    return (
                        <div key={matrixSubQuestion.id}>
                            <div className={styles['answer-option-row']}>
                                <div className={styles['answer-option-row__input']}>
                                    <GenericText
                                        label={labeltext}
                                        value={matrixSubQuestion.title}
                                        fullWidth
                                        autoComplete={false}
                                        autoFocus={newQuestion}
                                        onChange={onChangeQuestion(i, 'title')}
                                        controls
                                        disabled={matrixSubQuestion.hidden}
                                        showEnglish={showEnglish}
                                        ruotsiVaiEnglantiValittu={
                                            ruotsiVaiEnglantiValittu
                                        }
                                    />
                                </div>

                                {published === StatusType.luonnos && (
                                    <div className={styles['answer-option-row__remove']}>
                                        <div
                                            onClick={() => removeSubQuestion(i)}
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

                                {published !== StatusType.luonnos && (
                                    <div className={styles['answer-option-row__remove']}>
                                        <div
                                            onClick={() => hideSubQuestion(i)}
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
                                                {!matrixSubQuestion.hidden ? (
                                                    <VisibilityOff />
                                                ) : (
                                                    <Visibility />
                                                )}
                                            </IconButton>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className={styles['answer-option-desc']}>
                                <DescriptionText
                                    value={matrixSubQuestion.description}
                                    onChange={onChangeQuestion(i, 'description')}
                                    disabled={matrixSubQuestion.hidden}
                                    showEnglish={showEnglish}
                                    ruotsiVaiEnglantiValittu={ruotsiVaiEnglantiValittu}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>

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
        </>
    );
}

export default MatrixQuestion;
