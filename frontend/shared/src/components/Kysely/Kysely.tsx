import React, {
    MutableRefObject,
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
} from 'react';
import {useNavigate} from 'react-router-dom';
import {SubmitHandler, useForm, useWatch} from 'react-hook-form';
import {useTranslation} from 'react-i18next';
import InputTypes, {KysymysMatrixTypes, MonivalintaTypes} from '../InputType/InputTypes';
import AlertService, {AlertType} from '../../services/Alert/Alert-service';
import ConfirmationDialog from '../ConfirmationDialog/ConfirmationDialog';
import {
    GenericFormValueType,
    KyselyType,
    KyselyVastaus,
    KysymysType,
} from '../../services/Data/Data-service';
import {
    TempVastaus,
    vastauspalveluGetTempAnswers$,
    vastauspalveluPostAnswers$,
    vastauspalveluPostTempAnswers$,
} from '../../services/Vastauspalvelu-api/Vastauspalvelu-api-service';
import {deepCopy, defaultFormValues, getFollowupNotSatisfied} from '../../utils/helpers';
import Form from '../Form/Form';

interface KyselyProps {
    editable?: boolean;
    vastaajaUi?: boolean;
    selectedKysely: KyselyType | null;
    vastaajatunnus?: string;
    tempAnswersAllowed?: boolean;
    renderFormFieldActions?: (
        id: number,
        previousid: number,
        nextid: number,
    ) => React.JSX.Element;
    handleTogglePagebreak?: (kysymys: KysymysType) => void;
    focusTitleRef?: MutableRefObject<HTMLDivElement>;
    language?: string;
}

function Kysely({
    editable = false,
    vastaajaUi = false,
    selectedKysely,
    vastaajatunnus = '',
    tempAnswersAllowed = false,
    renderFormFieldActions,
    handleTogglePagebreak,
    focusTitleRef,
    language,
}: KyselyProps) {
    const defaultValues = useMemo(
        () => defaultFormValues(selectedKysely.id, selectedKysely.kysymykset),
        [selectedKysely],
    );
    const {
        handleSubmit,
        reset,
        control,
        getValues,
        trigger,
        setFocus,
        clearErrors,
        formState: {errors, isSubmitting},
    } = useForm<GenericFormValueType>({
        criteriaMode: 'firstError',
        defaultValues,
    });

    const [lastPage, setLastPage] = useState<boolean>(false);

    useEffect(() => {
        reset(defaultValues);
    }, [defaultValues, reset]);

    const destructAnswerValue = useCallback(
        (answer: TempVastaus) => {
            const [, kysymysId] =
                typeof answer.kysymysid === 'string'
                    ? answer.kysymysid.split('_')
                    : [null, null];
            const realKysymys = kysymysId
                ? selectedKysely?.kysymykset.find((k) => k.id === parseInt(kysymysId, 10))
                : null;
            if (realKysymys) {
                if (
                    ['checkbox', 'radiobutton', 'dropdown'].includes(
                        realKysymys.inputType,
                    )
                ) {
                    const val = parseInt(answer.numerovalinta, 10);
                    const existingValue = getValues()[answer.kysymysid] as object;
                    return {...existingValue, [val]: true};
                }
            }
            if (answer.en_osaa_sanoa) {
                return -1;
            }
            if (answer.numerovalinta) {
                return Number(answer.numerovalinta);
            }
            if (answer.string) {
                return answer.string;
            }
            return null;
        },
        [getValues, selectedKysely.kysymykset],
    );

    const tempAnswers = useCallback(() => {
        if (tempAnswersAllowed) {
            vastauspalveluGetTempAnswers$(vastaajatunnus).subscribe((answers) => {
                const tempAnswerData = answers.reduce((answerData, answer) => {
                    const val = destructAnswerValue(answer);
                    // TODO: tempvastaus for InputTypes.numeric fails if the value is 0, as it is falsy
                    if (val) {
                        if (
                            typeof val === 'object' &&
                            typeof answerData[answer.kysymysid] === 'object'
                            // answer is multiple choice and not the first one for this question.
                        ) {
                            answerData[answer.kysymysid] = Object.keys(val).reduce(
                                (acc, key) => {
                                    acc[key] =
                                        val[key] || answerData[answer.kysymysid][key];
                                    return acc;
                                },
                                {} as {[key: string]: boolean},
                            );
                        } else {
                            answerData[answer.kysymysid] = val;
                        }
                    }
                    return answerData;
                }, {} as GenericFormValueType);
                reset(tempAnswerData);
            });
        }
    }, [destructAnswerValue, reset, vastaajatunnus, tempAnswersAllowed]);

    const submitRef = useRef<HTMLButtonElement>(null);
    const navigate = useNavigate();
    const watchValues = useWatch({control});

    const {
        t,
        i18n,
        i18n: {language: lang},
    } = useTranslation(['kysely']);

    const generatePayload = (data: GenericFormValueType, temp = false) => {
        const vastaukset: Array<KyselyVastaus> = [];
        const excludedFields = ['userEmail']; // These fields do not contain answers to kysely
        Object.entries(data).forEach(([key, value]) => {
            if (!excludedFields.includes(key)) {
                // key e.g. 79_149 -> kyselykertaid: 79, kysymysid: 149
                const [kyselyid, kysymysId] = key.split('_');

                const kysymys =
                    selectedKysely.kysymykset.find(
                        (k) => k.id.toString() === kysymysId,
                    ) ||
                    selectedKysely.kysymykset
                        .flatMap((k) => k.matrixQuestions)
                        .find((mq) => mq.id.toString() === kysymysId) ||
                    selectedKysely.kysymykset
                        .flatMap((k) => Object.values(k.followupQuestions))
                        .find((fq) => fq.id.toString() === kysymysId);

                const vastaus: KyselyVastaus = {kysymysid: temp ? key : kysymysId};

                const followUpNotSatisfied = getFollowupNotSatisfied(
                    kyselyid,
                    KysymysMatrixTypes.includes(kysymys.inputType)
                        ? selectedKysely.kysymykset.find(
                              (k) => k.id === kysymys.matrixRootId,
                          )
                        : kysymys,
                    true,
                    watchValues,
                );

                if (followUpNotSatisfied) {
                    // console.info('hidden', key);
                } else if (
                    [InputTypes.singletext, InputTypes.multiline].includes(
                        kysymys.inputType as InputTypes.singletext | InputTypes.multiline,
                    ) &&
                    typeof value === 'string' &&
                    value !== ''
                ) {
                    vastaus.string = value.toString();
                    vastaukset.push(vastaus);
                } else if (
                    InputTypes.numeric === kysymys.inputType &&
                    typeof value === 'string' &&
                    value !== ''
                ) {
                    // comma allowed in input field, replace it with period to make conversion to float possible.
                    vastaus.string = value.toString().replace(/,/g, '.');
                    vastaukset.push(vastaus);
                } else if (
                    KysymysMatrixTypes.includes(kysymys.inputType) &&
                    typeof value === 'number'
                ) {
                    if (value === -1) vastaus.en_osaa_sanoa = 1;
                    else vastaus.numerovalinta = value;
                    vastaukset.push(vastaus);
                } else if (
                    MonivalintaTypes.includes(kysymys.inputType) &&
                    typeof value === 'object'
                ) {
                    if (value !== null) {
                        // monivalinta
                        Object.entries(value).forEach(
                            // value e.g. {1: true, 2: false}
                            ([monivalintaKysymysId, monivalintaKysymysIdSelected]) => {
                                if (monivalintaKysymysIdSelected) {
                                    vastaus.numerovalinta = parseInt(
                                        monivalintaKysymysId,
                                        10,
                                    );
                                    vastaukset.push(deepCopy(vastaus));
                                }
                            },
                        );
                    } else {
                        console.info(`Info: No data in monivalinta`);
                    }
                } else if (value) {
                    console.warn(`Error: value not processable ${value}`);
                }
            }
        });
        return {
            vastaajatunnus,
            vastaukset,
            ...(!temp && {email: data.userEmail || ''}),
        };
    };

    const submitTempAnswers = () => {
        trigger().then(() => {
            const payload = generatePayload(getValues(), true);
            const maxLengthErrors = Object.entries(errors)
                .filter((dd) => dd[1].type === 'maxLength')
                .map((m) => m[0]);

            clearErrors();
            if (maxLengthErrors.length === 0) {
                vastauspalveluPostTempAnswers$(payload).subscribe((response) => {
                    if (response === 'OK') {
                        navigate('/kiitos?temp=true');
                    } else {
                        const [key, body, ns] = [
                            'vastauspalvelu-temp-failure-title',
                            'vastauspalvelu-temp-failure-body',
                            'vastaa-kysely',
                        ];
                        const alert = {
                            title: {key, ns},
                            severity: 'error',
                            ...(i18n.exists(body, {ns}) && {
                                body: {key: body, ns},
                            }),
                        } as AlertType;
                        AlertService.showAlert(alert);
                    }
                });
            } else {
                trigger(maxLengthErrors).then(() => {
                    setFocus(maxLengthErrors[0]);
                    setTimeout(() => {
                        clearErrors();
                    }, 5000);
                });
            }
        });
    };

    const onSubmit: SubmitHandler<GenericFormValueType> = (data) => {
        const payload = generatePayload(data);
        vastauspalveluPostAnswers$(payload, lang).subscribe((response) => {
            if (response === 'OK') {
                navigate('/kiitos');
            } else {
                const [key, body, ns] = [
                    'vastauspalvelu-failure-title',
                    'vastauspalvelu-failure-body',
                    'vastaa-kysely',
                ];
                const alert = {
                    title: {key, ns},
                    severity: 'error',
                    ...(i18n.exists(body, {ns}) && {
                        body: {key: body, ns},
                    }),
                } as AlertType;
                AlertService.showAlert(alert);
            }
        });
    };

    const renderForm = () => (
        <Form
            kysely={selectedKysely}
            editable={editable}
            errors={errors}
            isSubmitting={isSubmitting}
            control={control}
            vastaajaUi={vastaajaUi}
            renderFormFieldActions={renderFormFieldActions}
            handleTogglePagebreak={handleTogglePagebreak}
            tempAnswers={tempAnswers}
            onLastPage={lastPage}
            setLastPage={setLastPage}
            focusTitleRef={focusTitleRef}
            language={language}
        />
    );

    const handleKeyDown = (e: React.KeyboardEvent<HTMLFormElement>) => {
        const {key, target} = e;
        if (key !== 'Enter' || target instanceof HTMLTextAreaElement) {
            // new line on textarea inputs
            return;
        }
        e.preventDefault();
    };

    // Lähetys-page has it's own form-tag. It's not allowed to have two nested form-tags.
    return selectedKysely.kysymykset.length > 0 ? (
        <div>
            {vastaajaUi ? (
                // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
                <form
                    onKeyDown={(e) => handleKeyDown(e)}
                    onSubmit={handleSubmit(onSubmit)}
                    className="form"
                >
                    {renderForm()}
                    {tempAnswersAllowed && (
                        <ConfirmationDialog
                            title={t('haluatko-tallentaa-valiaikaisesti')}
                            confirm={submitTempAnswers}
                            confirmBtnText={t('tallenna-valiaikaisesti-confirm')}
                            content={<p>{t('tallenna-valiaikaisesti-teksti')}</p>}
                        >
                            <button type="button" className="secondary">
                                {t('tallenna-valiaikaisesti')}
                            </button>
                        </ConfirmationDialog>
                    )}
                    <button type="submit" ref={submitRef} style={{display: 'none'}}>
                        -
                    </button>
                    {lastPage && (
                        <ConfirmationDialog
                            title={t('haluatko-lahettaa-vastaukset')}
                            confirm={() => submitRef.current.click()}
                            confirmBtnText={t('laheta-vastaukset')}
                        >
                            <button type="button">{t('laheta-vastaukset')}</button>
                        </ConfirmationDialog>
                    )}
                </form>
            ) : (
                <div className="form">{renderForm()}</div>
            )}
        </div>
    ) : null;
}

export default Kysely;
