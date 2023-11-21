import React, {useState, Dispatch, SetStateAction} from 'react';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormLabel from '@mui/material/FormLabel';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import Checkbox from '@mui/material/Checkbox';
import Dialog from '@mui/material/Dialog';
import {Box} from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';
import {useTranslation} from 'react-i18next';
import {forkJoin} from 'rxjs';
import QuestionTypes from '@cscfi/shared/components/QuestionType/QuestionTypes';
import InputType from '@cscfi/shared/components/InputType/InputType';
import InputTypes, {
    KysymysMatrixTypes,
    KysymysStringTypes,
    MonivalintaTypes,
} from '@cscfi/shared/components/InputType/InputTypes';
import {
    CheckBoxType,
    KyselyType,
    KysymysType,
    StatusType,
    TextType,
} from '@cscfi/shared/services/Data/Data-service';
import {capitalize, objectsEqualIncludeOnly} from '@cscfi/shared/utils/helpers';
import TextQuestion from '@cscfi/shared/components/TextQuestion/TextQuestion';
import CheckboxQuestion from '@cscfi/shared/components/CheckboxQuestion/CheckboxQuestion';
import MatrixQuestion from '@cscfi/shared/components/MatrixQuestion/MatrixQuestion';
import ArvoInputTypes, {
    ArvoMatriisikysymysId,
    arvoRemoveKysymys$,
    arvoUpdateKysymysryhma$,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import {map} from 'rxjs/operators';
import {useObservable} from 'rxjs-hooks';
import {virkailijapalveluGetMatrixScales$} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import getKysymysFromKysely from '../../services/Kysely/GetKysymys/GetKysymys-service';
import {
    saveKysymysDb,
    saveMatriisiKysymysDb,
} from '../../services/Kysely/SaveKysymysDb/SaveKysymysDb-service';
import updateOneKysely from '../../services/Kysely/UpdateKysely/UpdateKysely-service';
import styles from './LisaaMuokkaaKysymys.module.css';

interface LisaaMuokkaaKysymysProps {
    children: (openDialog: () => void) => void;
    kysely: KyselyType;
    setKysely: Dispatch<SetStateAction<KyselyType | null>>;
    selectedKysymysId: number;
}

interface KysymysDataType {
    // a subset of KysymysType
    title: TextType;
    description: TextType;
    answerOptions: CheckBoxType[];
    matrixQuestions: KysymysType[];
    matrixQuestionType: InputTypes.matrix_slider | InputTypes.matrix_radio;
    answerType?: ArvoInputTypes;
    hidden?: boolean;
}

function LisaaMuokkaaKysymys({
    children,
    kysely,
    setKysely,
    selectedKysymysId,
}: LisaaMuokkaaKysymysProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['kysely']);
    const [showDialog, setShowDialog] = useState(false);
    const [existingKysymys, setExistingKysymys] = useState<KysymysType | null>(null);
    const [selectedQuestionType, setselectedQuestionType] = useState(
        QuestionTypes.matrix,
    );
    const [selectedInputType, setSelectedInputType] = useState(InputTypes.matrix_radio);
    const [title, setTitle] = useState<TextType>({fi: '', sv: ''});
    const [description, setDescription] = useState<TextType>({fi: '', sv: ''});
    const [answers, setAnswers] = useState<CheckBoxType[]>([]);
    const [subQuestions, setSubQuestions] = useState<KysymysType[]>([]);
    const [origSubQuestions, setOrigSubQuestions] = useState<KysymysType[]>([]);
    const [requiredFlag, setRequiredFlag] = useState(false);
    const [eosFlag, setEosFlag] = useState(false);
    const [eosText, setEosText] = useState<string>('');
    const [hidden, setHidden] = useState(false);
    const [error, setError] = useState<string[]>([]);

    const matrixScales = useObservable(() => virkailijapalveluGetMatrixScales$());

    const onDialogClose = () => {
        setShowDialog(false);
    };

    const setDefaultValues = (kysymys: KysymysType, qType: QuestionTypes) => {
        setselectedQuestionType(qType);
        setSelectedInputType(kysymys.inputType);
        setTitle({fi: kysymys.title.fi, sv: kysymys.title.sv});
        setDescription({
            fi: kysymys.description?.fi || '',
            sv: kysymys?.description?.sv || '',
        });
    };

    const openDialog = () => {
        setselectedQuestionType(QuestionTypes.matrix);
        setSelectedInputType(InputTypes.matrix_radio);
        setTitle({fi: '', sv: ''});
        setDescription({fi: '', sv: ''});
        setAnswers([]);
        setSubQuestions([]);
        setOrigSubQuestions([]);
        setRequiredFlag(false);
        setEosFlag(false);
        setError([]);

        const scaleEosText = matrixScales?.map((x) => x)[0].eos_value?.[
            lang as keyof TextType
        ];
        if (scaleEosText !== undefined) {
            setEosText(scaleEosText);
        }

        if (selectedKysymysId !== -1) {
            const kysymys = getKysymysFromKysely(kysely, selectedKysymysId);
            setExistingKysymys(kysymys);

            if (kysymys) {
                setRequiredFlag(kysymys.required ? kysymys.required : false);
                setHidden(kysymys.hidden ? kysymys.hidden : false);
                setEosFlag(kysymys.allowEos ? kysymys.allowEos : false);
                switch (kysymys.inputType) {
                    case InputTypes.singletext:
                    case InputTypes.multiline:
                    case InputTypes.numeric:
                        setDefaultValues(kysymys, QuestionTypes.text);
                        break;
                    case InputTypes.radio:
                    case InputTypes.checkbox:
                        setDefaultValues(kysymys, QuestionTypes.multi);
                        setAnswers(kysymys.answerOptions);
                        break;
                    case InputTypes.matrix_slider:
                    case InputTypes.matrix_radio:
                        setDefaultValues(kysymys, QuestionTypes.matrix);
                        setSubQuestions(kysymys.matrixQuestions);
                        setOrigSubQuestions(kysymys.matrixQuestions);
                        break;
                    default:
                        console.log(`Error: Invalid input-type: ${kysymys.inputType}`);
                        onDialogClose();
                        break;
                }
            } else {
                console.log(`Error: Kysymys not found! Id: ${selectedKysymysId}`);
            }
        }
        setShowDialog(true);
    };

    const handleChange = (changeFromSubComponent: KysymysDataType) => {
        if (changeFromSubComponent.title) {
            setTitle(changeFromSubComponent.title);
            setError((errorList) =>
                errorList.filter((errorItem) => errorItem !== 'title-required'),
            );
        } else if (changeFromSubComponent.description) {
            setDescription(changeFromSubComponent.description);
        } else if (changeFromSubComponent.answerOptions) {
            setAnswers(changeFromSubComponent.answerOptions);
            setError((errorList) =>
                errorList.filter((errorItem) => errorItem !== 'no-answer-options'),
            );
        } else if (changeFromSubComponent.matrixQuestions) {
            setSubQuestions(changeFromSubComponent.matrixQuestions);
        }
    };

    const handleQuestionTypeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = e.target.value;
        if (newValue === QuestionTypes.text) {
            setselectedQuestionType(QuestionTypes.text);
            setSelectedInputType(InputTypes.singletext);
        } else if (newValue === QuestionTypes.multi) {
            setselectedQuestionType(QuestionTypes.multi);
            setSelectedInputType(InputTypes.checkbox);
        } else if (newValue === QuestionTypes.matrix) {
            setselectedQuestionType(QuestionTypes.matrix);
            setSelectedInputType(InputTypes.matrix_radio);
        }
        setError([]);
    };

    const handleInputTypeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = e.target.value as InputTypes;
        setSelectedInputType(newValue);
    };

    const handleRequiredChange = (req: boolean) => {
        setRequiredFlag(req);
        setSubQuestions(
            subQuestions.map((sq) => ({
                ...sq,
                required: req,
            })),
        );
    };

    // Takes scale name and assigns associated eos label.
    const handleScaleChange = (val: string) => {
        const scaleEosText = matrixScales?.find((x) => x.name === val)?.eos_value?.[
            lang as keyof TextType
        ];
        if (scaleEosText !== undefined) setEosText(scaleEosText);
    };

    const handleEosChange = (eos: boolean) => {
        setEosFlag(eos);
        setSubQuestions(
            subQuestions.map((sq) => ({
                ...sq,
                allowEos: eos,
            })),
        );
    };

    const handleCancel = () => {
        setSubQuestions(origSubQuestions);
        onDialogClose();
    };

    const handleSave = () => {
        const updatedKysymys = {
            id: selectedKysymysId,
            inputType: selectedInputType,
            title: {fi: title.fi, sv: title.sv},
            description: {fi: description.fi, sv: description.sv},
            required: requiredFlag,
            hidden,
            allowEos: eosFlag,
            answerOptions: answers,
            matrixQuestions: subQuestions,
        };

        if (MonivalintaTypes.includes(selectedInputType) && answers.length < 1) {
            setError((errorList) => [...errorList, 'no-answer-options']);
            return;
        }
        if (
            (KysymysStringTypes.includes(selectedInputType) ||
                MonivalintaTypes.includes(selectedInputType)) &&
            title.fi === ''
        ) {
            setError((errorList) => [...errorList, 'title-required']);
            return;
        }

        if (selectedKysymysId > 0 && KysymysMatrixTypes.includes(selectedInputType)) {
            const [createQuestions, updateQuestions] = subQuestions.reduce(
                ([create, update]: [KysymysType[], KysymysType[]], question) => {
                    if (!question.matrixRootId) {
                        return [
                            [...create, {...question, matrixRootId: selectedKysymysId}],
                            update,
                        ];
                    }
                    const original = origSubQuestions.find(
                        (osq) => osq.id === question.id,
                    );
                    if (
                        original &&
                        !objectsEqualIncludeOnly(original, question, [
                            'title',
                            'description',
                            'required',
                            'allowEos',
                        ])
                    ) {
                        return [create, [...update, question]];
                    }
                    return [create, update];
                },
                [[], []],
            );
            const removeQuestions = origSubQuestions.filter(
                (osq) => !subQuestions.some((sq) => osq.id === sq.id),
            );

            const createQueries = createQuestions.map((createKysymys) =>
                saveMatriisiKysymysDb(createKysymys, selectedInputType).pipe(
                    map((createResponse: ArvoMatriisikysymysId) => {
                        const index = updatedKysymys.matrixQuestions.findIndex(
                            (mq) => mq.id === createKysymys.id,
                        );
                        updatedKysymys.matrixQuestions[index].id =
                            createResponse.kysymysid;
                        updatedKysymys.matrixQuestions[index].matrixRootId =
                            selectedKysymysId;
                        updatedKysymys.matrixQuestions[index].inputType =
                            selectedInputType;
                        updateOneKysely(kysely, setKysely, updatedKysymys);
                    }),
                ),
            );
            const updateQueries = updateQuestions.map((updateKysymys) =>
                saveKysymysDb(kysely.id, updateKysymys),
            );
            const removeQueries = removeQuestions.map((rq) => arvoRemoveKysymys$(rq.id));
            const allQueries = [...createQueries, ...updateQueries, ...removeQueries];

            forkJoin(allQueries).subscribe({
                complete: () => {
                    onDialogClose();
                },
                error: () => {
                    const alert = {
                        title: {key: 'alert-error-title', ns: 'kysely'},
                        severity: 'error',
                    } as AlertType;
                    AlertService.showAlert(alert);
                    onDialogClose();
                },
            });
        }
        saveKysymysDb(kysely.id, updatedKysymys).subscribe((res) => {
            if (selectedKysymysId === -1) {
                // Create new kysymys in DB and receive a unique kysymysId in response.
                updatedKysymys.id = res.kysymysid;

                if (res?.matriisikysymykset && res?.matriisikysymykset.length > 0) {
                    updatedKysymys.matrixQuestions.forEach((mq, index) => {
                        updatedKysymys.matrixQuestions[index].id =
                            res?.matriisikysymykset[index];
                        updatedKysymys.matrixQuestions[index].matrixRootId =
                            res.kysymysid;
                    });
                }
            }

            updateOneKysely(kysely, setKysely, updatedKysymys);
            onDialogClose();
        });
        /**
         * This empty patch needs to be sent to synchronize
         * kysymysryhma.muutettuaika with kysymysryhma questions
         */
        if (kysely.status !== StatusType.julkaistu) {
            arvoUpdateKysymysryhma$(kysely.id, {}).subscribe(() => {});
        }
    };

    const errorMessageOptions = () => (
        <p className={[styles['error-message'], 'error'].join(' ')}>
            <WarningIcon />
            {t('pakollinen-vastausvaihtoehto')}
        </p>
    );

    const errorMessageTitle = () => (
        <p className={[styles['error-message'], 'error'].join(' ')}>
            <WarningIcon />
            {t('pakollinen-otsikko')}
        </p>
    );

    const generateField = () => {
        switch (selectedInputType) {
            case InputTypes.radio:
            case InputTypes.checkbox:
                return (
                    <CheckboxQuestion
                        key={selectedKysymysId}
                        title={title}
                        description={description}
                        answerOptions={answers}
                        handleChange={handleChange}
                        published={kysely.status}
                    />
                );
            case InputTypes.singletext:
            case InputTypes.multiline:
            case InputTypes.numeric:
                return (
                    <TextQuestion
                        key={selectedKysymysId}
                        title={title}
                        description={description}
                        handleChange={handleChange}
                    />
                );
            case InputTypes.matrix_slider:
            case InputTypes.matrix_radio:
                return (
                    <MatrixQuestion
                        key={selectedKysymysId}
                        title={title}
                        description={description}
                        matrixQuestions={subQuestions}
                        handleChange={handleChange}
                        handleScaleChange={handleScaleChange}
                        required={requiredFlag || false}
                        existingKysymys={!!existingKysymys}
                        published={kysely.status}
                        inputType={selectedInputType}
                    />
                );
            default:
                console.error(`Error: Invalid input-type: ${selectedInputType}`);
                return <p>ERROR</p>;
        }
    };

    return (
        <>
            {children(openDialog)}
            {showDialog && (
                <Dialog
                    open
                    maxWidth={false}
                    fullWidth
                    disableRestoreFocus
                    aria-labelledby="lisaamuokkaakysymys_h1"
                >
                    <h1>
                        {t(
                            existingKysymys
                                ? 'muokkaa-vaittamaa-otsikko'
                                : 'lisaa-uusi-vaittama-otsikko',
                        )}
                    </h1>
                    <div className="button-container-top">
                        <IconButton
                            className="icon-button"
                            aria-label={t('sulje-dialogi', {ns: 'yleiset'})}
                            onClick={() => onDialogClose()}
                        >
                            <CloseIcon />
                        </IconButton>
                    </div>
                    {!existingKysymys && (
                        <div className={styles['kysymys-type__container']}>
                            <div>
                                <FormControl component="fieldset">
                                    <FormLabel component="legend">
                                        {t('vaittaman-tyyppi')}
                                    </FormLabel>
                                    <RadioGroup
                                        aria-label="question type"
                                        name="Question type"
                                        value={selectedQuestionType}
                                        onChange={(e) => handleQuestionTypeChange(e)}
                                    >
                                        <FormControlLabel
                                            aria-label="matrix question"
                                            value={QuestionTypes.matrix}
                                            control={<Radio />}
                                            label={t('matriisi-label')}
                                        />
                                        <FormControlLabel
                                            aria-label="text question"
                                            value={QuestionTypes.text}
                                            control={<Radio />}
                                            label={t('teksti-label')}
                                        />
                                        <FormControlLabel
                                            aria-label="multiselect question"
                                            value={QuestionTypes.multi}
                                            control={<Radio />}
                                            label={t('monivalinta-label')}
                                        />
                                    </RadioGroup>
                                </FormControl>
                            </div>
                            <div>
                                <InputType
                                    questionType={selectedQuestionType}
                                    selectedInputType={selectedInputType}
                                    handleInputTypeChange={handleInputTypeChange}
                                />
                            </div>
                        </div>
                    )}
                    <Box>{generateField()}</Box>
                    <div className={styles['form-controls__container']}>
                        <FormControlLabel
                            label={t('pakollinen-kentta-label')}
                            control={
                                <Checkbox
                                    key="requiredField"
                                    checked={requiredFlag}
                                    onChange={() => handleRequiredChange(!requiredFlag)}
                                    name="requiredField"
                                    className={styles.checkbox}
                                    disabled={eosFlag || hidden}
                                />
                            }
                        />
                        {KysymysMatrixTypes.includes(selectedInputType) && (
                            <FormControlLabel
                                label={`${t('eos-sallittu-label')} ${capitalize(
                                    eosText,
                                )}`}
                                control={
                                    <Checkbox
                                        key="eosField"
                                        checked={eosFlag}
                                        onChange={() => handleEosChange(!eosFlag)}
                                        name="eosField"
                                        className={styles.checkbox}
                                        disabled={!requiredFlag}
                                    />
                                }
                            />
                        )}
                        {error.includes('no-answer-options') ? errorMessageOptions() : ''}
                        {error.includes('title-required') ? errorMessageTitle() : ''}
                        <div className="button-container">
                            <button
                                type="button"
                                className="secondary"
                                onClick={handleCancel}
                            >
                                {t('peruuta')}
                            </button>
                            {selectedQuestionType === QuestionTypes.matrix &&
                            subQuestions.length === 0 ? (
                                <ConfirmationDialog
                                    title={t('matriisin-tallennus-virhe-title')}
                                    confirmBtnText={t('matriisin-tallennus-virhe-btn')}
                                    content={
                                        <p>{t('matriisin-tallennus-virhe-content')}</p>
                                    }
                                >
                                    <button type="button">{t('tallenna')}</button>
                                </ConfirmationDialog>
                            ) : (
                                <button type="button" onClick={handleSave}>
                                    {t('tallenna')}
                                </button>
                            )}
                        </div>
                    </div>
                </Dialog>
            )}
        </>
    );
}

export default LisaaMuokkaaKysymys;
