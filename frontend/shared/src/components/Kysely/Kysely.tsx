import {useEffect, useMemo, useRef, useCallback} from 'react';
import {useNavigate} from 'react-router-dom';
import {SubmitHandler, useForm} from 'react-hook-form';
import {useTranslation} from 'react-i18next';
import AlertService, {AlertType} from '../../services/Alert/Alert-service';
import ConfirmationDialog from '../ConfirmationDialog/ConfirmationDialog';
import {
    KyselyType,
    GenericFormValueType,
    KyselyVastaus,
} from '../../services/Data/Data-service';
import {
    vastauspalveluPostAnswers$,
    vastauspalveluPostTempAnswers$,
    vastauspalveluGetTempAnswers$,
    TempVastaus,
} from '../../services/Vastauspalvelu-api/Vastauspalvelu-api-service';
import {deepCopy, defaultFormValues} from '../../utils/helpers';
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
    ) => JSX.Element;
}

function Kysely({
    editable = false,
    vastaajaUi = false,
    selectedKysely,
    vastaajatunnus = '',
    tempAnswersAllowed = false,
    renderFormFieldActions,
}: KyselyProps) {
    const defaultValues = useMemo(
        () => defaultFormValues(selectedKysely.id, selectedKysely.kysymykset),
        [selectedKysely],
    );
    const {
        handleSubmit,
        reset,
        control,
        setValue,
        getValues,
        formState: {errors, isSubmitting},
    } = useForm<GenericFormValueType>({
        criteriaMode: 'firstError',
        defaultValues,
    });

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
                ? selectedKysely.kysymykset.find((k) => k.id === parseInt(kysymysId, 10))
                : null;
            if (realKysymys) {
                if (['checkbox', 'radiobutton'].includes(realKysymys.inputType)) {
                    const val = parseInt(answer.numerovalinta, 10);
                    const existingValue = getValues()[answer.kysymysid] as Object;
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

    const getTempAnswers = useCallback(() => {
        vastauspalveluGetTempAnswers$(vastaajatunnus).subscribe((answers) => {
            answers.forEach((answer) => {
                const val = destructAnswerValue(answer);
                if (val) {
                    setValue(answer.kysymysid, val);
                }
            });
        });
    }, [destructAnswerValue, setValue, vastaajatunnus]);

    useEffect(() => {
        if (tempAnswersAllowed) {
            getTempAnswers();
        }
    }, [getTempAnswers, tempAnswersAllowed]);

    const submitRef = useRef<HTMLButtonElement>(null);
    const navigate = useNavigate();
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
                const [, kysymysId] = key.split('_');
                const vastaus: KyselyVastaus = {kysymysid: temp ? key : kysymysId};
                if (typeof value === 'number') {
                    /* Conditional put in place for "ei koske ryhmääni” in matrix questions, might break
                     * something when number fields are implemented.
                     */
                    if (value === -1) {
                        vastaus.en_osaa_sanoa = 1;
                    } else {
                        vastaus.numerovalinta = value;
                    }
                    vastaukset.push(vastaus);
                } else if (value === '-1') {
                    vastaus.en_osaa_sanoa = 1;
                    vastaukset.push(vastaus);
                } else if (
                    typeof value === 'string' &&
                    value.length === 1 &&
                    Number(value)
                ) {
                    vastaus.numerovalinta = Number(value);
                    vastaukset.push(vastaus);
                } else if (typeof value === 'string') {
                    vastaus.string = value;
                    vastaukset.push(vastaus);
                } else if (typeof value === 'object' && value !== null) {
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
                    console.log(`Error: Undefined kysymys-type: ${typeof value}`);
                }
            }
        });
        const payload = {
            vastaajatunnus,
            vastaukset,
            ...(!temp && {email: data.userEmail || ''}),
        };
        return payload;
    };

    const submitTempAnswers = () => {
        const payload = generatePayload(getValues(), true);
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
        />
    );

    // Lähetys-page has it's own form-tag. It's not allowed to have two nested form-tags.
    return selectedKysely !== null && selectedKysely.kysymykset.length > 0 ? (
        <div>
            {vastaajaUi ? (
                <form onSubmit={handleSubmit(onSubmit)} className="form">
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
                    <ConfirmationDialog
                        title={t('haluatko-lahettaa-vastaukset')}
                        confirm={() => submitRef.current.click()}
                        confirmBtnText={t('laheta-vastaukset')}
                    >
                        <button type="button">{t('laheta-vastaukset')}</button>
                    </ConfirmationDialog>
                </form>
            ) : (
                <div className="form">{renderForm()}</div>
            )}
        </div>
    ) : null;
}

export default Kysely;
