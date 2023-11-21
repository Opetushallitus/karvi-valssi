import {useContext, useEffect, useMemo, useState, ReactElement} from 'react';
import {useLocation, useNavigate} from 'react-router-dom';
import {FieldNamesMarkedBoolean, SubmitHandler, useForm} from 'react-hook-form';
import {useTranslation} from 'react-i18next';
import {defaultFormValues, getQueryParamAsNumber} from '@cscfi/shared/utils/helpers';
import {Box} from '@mui/material';
import InputTypes from '@cscfi/shared/components/InputType/InputTypes';
import SingleField from '@cscfi/shared/components/Form/FormFields/SingleField/SingleField';
import MultiOptionField from '@cscfi/shared/components/Form/FormFields/MultiOptionField/MultiOptionField';
import MatrixField from '@cscfi/shared/components/Form/FormFields/MatrixField/MatrixField';
import TitleField from '@cscfi/shared/components/Form/FormFields/TitleField/TitleField';
import {GenericFormValueType, TextType} from '@cscfi/shared/services/Data/Data-service';
import AlertService from '@cscfi/shared/services/Alert/Alert-service';
import LaunchIcon from '@mui/icons-material/Launch';
import {
    raportiointipalveluPostReportingTemplate$,
    raportiointipalveluPutReportingTemplate$,
    ReportingBase,
    ReportingTemplate,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import UserContext from '../../Context';
import RaportointiPohjaButtons from './RaportointiPohjaButtons';
import styles from './RaporttiPohja.module.css';

type GroupedFormValues = {
    [key: string | number]: GenericFormValueType;
};

function templateHelpTextIdByQuestionId(questionId: number, template: ReportingTemplate) {
    return template.template_helptexts.find((ht) => ht.question_id === questionId)?.id;
}

function hasDirtyFields(
    dirtyFields: Partial<Readonly<FieldNamesMarkedBoolean<GenericFormValueType>>>,
) {
    return (
        Object.entries(dirtyFields).filter((obj) => obj[0].startsWith('help_')).length > 0
    );
}

function payloadGenerator(formdata: GenericFormValueType, raporttipohja: ReportingBase) {
    const helps = Object.entries(formdata).filter((h) => h[0].startsWith('help_'));
    const groupedQuestions = helps.reduce((questionFields: GroupedFormValues, qd) => {
        const [key, val] = qd;
        const [, type, id, qlang] = key.split('_');
        if (type === 'kysymys') {
            questionFields[id] = questionFields[id] ?? {};
            questionFields[id][`description_${qlang}`] = val || '';
        }
        return questionFields;
    }, {}) as GroupedFormValues;
    return {
        ...(raporttipohja.reporting_template.id && {
            id: raporttipohja.reporting_template.id,
        }),
        kysymysryhmaid: raporttipohja.kysymysryhmaid,
        description_fi: formdata.help_main_description_fi || '',
        description_sv: formdata.help_main_description_sv || '',
        template_helptexts: Object.entries(groupedQuestions).map((gq) => {
            const [key, val] = gq;
            const htId = templateHelpTextIdByQuestionId(
                parseInt(key, 10),
                raporttipohja.reporting_template,
            );
            return {
                ...(htId && {id: htId}),
                question_id: parseInt(key, 10),
                ...val,
            };
        }),
    } as ReportingTemplate;
}

interface MuokkaaRaporttiPohjaProps {
    raporttipohja: ReportingBase;
    // TODO: tyypit mittaridatalle
    mittaridata?: any;
    sourcePage?: string;
    showButtons?: boolean;
    oppilaitos?: string;
    ajankohta_alku?: string;
    ajankohta_loppu?: string;
}

function RaporttiPohja({
    raporttipohja,
    mittaridata,
    sourcePage,
    showButtons = true,
    oppilaitos,
    ajankohta_alku,
    ajankohta_loppu,
}: MuokkaaRaporttiPohjaProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['raporttipohja']);
    const userInfo = useContext(UserContext);
    const navigate = useNavigate();
    const location = useLocation();
    const kysymysryhmaId = getQueryParamAsNumber(location, 'id');
    function prevPage() {
        return sourcePage ? `/${sourcePage}` : '/';
    }

    const [expanded, setExpanded] = useState<string[]>([]);
    const handleExpandedChange = (panel: string) => {
        if (expanded.includes(panel)) {
            setExpanded(expanded.filter((key) => key !== panel));
        } else {
            setExpanded([...expanded, panel]);
        }
    };
    const kysymysryhmanimi = `nimi_${lang}` as keyof ReportingBase;
    const langKey = lang as keyof TextType;

    const defaultValues = useMemo(() => {
        const qArray: GenericFormValueType = {};
        raporttipohja.reporting_template.template_helptexts.forEach((ht) => {
            qArray[`help_kysymys_${ht.question_id}_fi`] = ht.description_fi;
            qArray[`help_kysymys_${ht.question_id}_sv`] = ht.description_sv;
        });
        return {
            ...defaultFormValues(raporttipohja.kysymysryhmaid, raporttipohja.questions),
            help_main_description_fi: raporttipohja.reporting_template.description_fi,
            help_main_description_sv: raporttipohja.reporting_template.description_sv,
            ...qArray,
        };
    }, [raporttipohja]);

    const {
        handleSubmit,
        reset,
        control,
        formState: {errors, dirtyFields},
        getValues,
        setValue,
    } = useForm<GenericFormValueType>({defaultValues});

    useEffect(() => {
        reset(defaultValues);
    }, [defaultValues, reset]);

    // if sessionStorage has reportPreviewData, populate fields with those
    useEffect(() => {
        const reportPreviewData = JSON.parse(
            sessionStorage.getItem(`reportPreviewData_${kysymysryhmaId}`) as string,
        );
        if (reportPreviewData) {
            Object.keys(reportPreviewData).forEach((key: any) => {
                const [prefix, index] = key.split('_');
                if (prefix === 'main') {
                    setValue('help_main_description_fi', reportPreviewData[key].fi, {
                        shouldDirty: true,
                    });
                    setValue('help_main_description_sv', reportPreviewData[key].sv, {
                        shouldDirty: true,
                    });
                } else if (prefix === 'kysymys' && index) {
                    setValue(
                        `help_kysymys_${key.split('_')[1]}_fi`,
                        reportPreviewData[key].fi,
                        {shouldDirty: true},
                    );
                    setValue(
                        `help_kysymys_${key.split('_')[1]}_sv`,
                        reportPreviewData[key].sv,
                        {shouldDirty: true},
                    );
                }
            });
        }
    }, [kysymysryhmaId, setValue]);

    const onSubmit: SubmitHandler<GenericFormValueType> = (data) => {
        const createUpdateFunc = raporttipohja.reporting_template.id
            ? raportiointipalveluPutReportingTemplate$(userInfo!)(
                  raporttipohja.reporting_template.id!,
                  payloadGenerator(data, raporttipohja),
              )
            : raportiointipalveluPostReportingTemplate$(userInfo!)(
                  payloadGenerator(data, raporttipohja),
              );

        createUpdateFunc.subscribe({
            complete: () => {
                AlertService.showAlert({
                    title: {key: 'save-success-title', ns: 'raporttipohja'},
                    severity: 'success',
                });
            },
            error: () => {
                AlertService.showAlert({
                    title: {key: 'save-error-title', ns: 'raporttipohja'},
                    severity: 'error',
                });
            },
            next: () => navigate(prevPage()),
        });
    };

    const hasValue = (fieldName: string) =>
        getValues([`${fieldName}_fi`, `${fieldName}_sv`]).filter(
            (val) => val && val !== '',
        ).length > 0;

    const btnOrField = (fieldName: string) =>
        !expanded.includes(fieldName) && !hasValue(fieldName) ? (
            <button type="button" onClick={() => handleExpandedChange(fieldName)}>
                {t('lisaa-tekstia')}
            </button>
        ) : (
            <>
                <SingleField
                    type={InputTypes.multiline}
                    id={`${fieldName}_fi`}
                    required={false}
                    title={t('kysymyksesta-suomeksi')}
                    fieldErrors={errors[`${fieldName}_fi`]}
                    control={control}
                />
                <SingleField
                    type={InputTypes.multiline}
                    id={`${fieldName}_sv`}
                    required={false}
                    title={t('kysymyksesta-ruotsiksi')}
                    fieldErrors={errors[`${fieldName}_sv`]}
                    control={control}
                />
            </>
        );

    const renderKysymykset = () =>
        raporttipohja!.questions.map((kysymys) => {
            const {inputType, id, title, description} = kysymys;
            const kyselyKysymysId = `kysymys_${id}`;
            let element: ReactElement;
            switch (inputType) {
                case InputTypes.singletext:
                case InputTypes.multiline:
                case InputTypes.numeric:
                    element = (
                        <SingleField
                            type={inputType as InputTypes}
                            id={kyselyKysymysId}
                            required={false}
                            title={title?.[langKey]}
                            description={description?.[langKey]}
                            control={control}
                        />
                    );
                    break;
                case InputTypes.radio:
                case InputTypes.checkbox: {
                    const {answerOptions} = kysymys;
                    element = (
                        <MultiOptionField
                            id={kyselyKysymysId}
                            required={false}
                            title={title?.[langKey]}
                            description={description?.[langKey]}
                            answerOptions={answerOptions}
                            type={inputType}
                            control={control}
                        />
                    );
                    break;
                }
                case InputTypes.matrix_slider:
                case InputTypes.matrix_radio: {
                    const {matrixQuestions} = kysymys;
                    element = (
                        <MatrixField
                            id={raporttipohja!.kysymysryhmaid.toString()}
                            title={title?.[langKey]}
                            description={description?.[langKey]}
                            questions={matrixQuestions}
                            isSubmitting={false}
                            type={inputType}
                            control={control}
                            ignoreRequired
                        />
                    );
                    break;
                }
                case InputTypes.statictext: {
                    element = (
                        <TitleField
                            title={title?.[langKey]}
                            description={description?.[langKey]}
                        />
                    );
                    break;
                }
                default:
                    console.log(`Error: Invalid Field input type: ${inputType}`);
                    element = (
                        <div key={id}>
                            <span>{`${t(
                                'invalid-field-input-type',
                            )}: (${inputType})`}</span>
                        </div>
                    );
            }
            const help = `help_${kyselyKysymysId}`;
            // @ts-ignore
            const helpLabel = getValues(`${help}_${lang}`) as string;

            if (!kysymys.hidden) {
                return (
                    <Box key={help} className={styles.questionContainer}>
                        <div key={kyselyKysymysId} className={styles.FlexContainer}>
                            {element}
                        </div>
                        <div className="field-row">
                            {mittaridata
                                ? helpLabel !== '' && <p>{helpLabel}</p>
                                : btnOrField(help)}
                        </div>
                    </Box>
                );
            }
            return null;
        });
    // @ts-ignore
    const helpLabel = getValues(`help_main_description_${lang}`) as string;

    const dateRange =
        ajankohta_alku === undefined && ajankohta_loppu === undefined
            ? t('tilanvaraaja-ajankohta')
            : `${ajankohta_alku || ''} - ${ajankohta_loppu || ''}`;

    const saveEsikatseluValues = () => {
        const acc: any = {};
        Object.keys(getValues())
            .filter((key) => key.startsWith('help_'))
            .forEach((key) => {
                const [, prefix, subkey, langPostfix] = key.split('_');
                acc[`${prefix}_${subkey}`] = acc[`${prefix}_${subkey}`] || {};
                acc[`${prefix}_${subkey}`][langPostfix] = getValues()[key];
            });
        sessionStorage.setItem(
            `reportPreviewData_${kysymysryhmaId}`,
            JSON.stringify(acc),
        );
    };

    const rpButtons = (
        <RaportointiPohjaButtons
            needsCancelConfirmation={hasDirtyFields(dirtyFields)}
            sourcePage={sourcePage}
            kysymysryhmaId={kysymysryhmaId!}
            onPreviewClick={saveEsikatseluValues}
        />
    );

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="form">
            {showButtons && rpButtons}
            <h2>{`${raporttipohja[kysymysryhmanimi]}`}</h2>
            <h3>{oppilaitos || t('tilanvaaraja-vakatoimija')}</h3>
            <h3>{`${t('tiedonkeruu-ajankohta')}: ${dateRange}`}</h3>

            <div className="field-row">
                {mittaridata
                    ? helpLabel !== '' && <p>{helpLabel}</p>
                    : btnOrField('help_main_description')}
            </div>

            <div className={styles.instructionsLink}>
                <a
                    href={t('link-raporttien-lukuohje-url')}
                    target="_blank"
                    rel="noreferrer"
                >
                    <LaunchIcon
                        sx={{
                            blockSize: 16,
                            marginRight: 1,
                            verticalAlign: 'top',
                        }}
                    />
                    {t('link-raporttien-lukuohje-text')}
                </a>
            </div>

            {renderKysymykset()}
            {mittaridata && <p>raportin mittari datalle</p>}
            {showButtons && rpButtons}
        </form>
    );
}

export default RaporttiPohja;
