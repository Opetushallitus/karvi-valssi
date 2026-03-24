import {useContext, useEffect, useRef, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {forkJoin} from 'rxjs';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import {useNavigate, useLocation} from 'react-router-dom';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import Kysely from '@cscfi/shared/components/Kysely/Kysely';
import {
    capitalize,
    getQueryParamAsNumber,
    kyselyNameGenerator,
} from '@cscfi/shared/utils/helpers';
import {format, parseISO, isSameDay, isBefore} from 'date-fns';
import {
    arvoGetKysymysryhma$,
    arvoGetAllKyselyt$,
    ArvoKysely,
    ArvoKyselyPost,
    ArvoKyselyMassPost,
    arvoMassAddKysely$,
    arvoGetKysymysryhmaKayttoraja$,
    Kayttoraja,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import * as ErrorService from '@cscfi/shared/services/Error/Error-service';
import {AjaxError} from 'rxjs/ajax';
import {toJson} from '@cscfi/shared/services/Http/Http-service';
import {
    SubmitHandler,
    useForm,
    Controller,
    UseFormProps,
    useWatch,
} from 'react-hook-form';
import InputTypes from '@cscfi/shared/components/InputType/InputTypes';
import SingleField from '@cscfi/shared/components/Form/FormFields/SingleField/SingleField';
import DateRangeField from '@cscfi/shared/components/Form/FormFields/DateRangeField/DateRangeField';
import WarningIcon from '@mui/icons-material/Warning';
import {MaxLengths} from '@cscfi/shared/utils/validators';
import {
    OppilaitosSetType,
    virkailijapalveluGetAluejako$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import SinglePanelAccordion from '../../components/SinglePanelAccordion/SinglePanelAccordion';
import SelectionList from '../../components/ToimipaikkaSelectionList/SelectionList';
import styles from './Aktivointi.module.css';
import {
    filterOppilaitosSetByOid,
    flattenItems,
    getDefaultEmptySet,
    hasKayttoraja,
    itemsLength,
    itemsNot,
} from '../../utils/helpers';
import UserContext from '../../Context';
import SelectedList from '../../components/ToimipaikkaSelectionList/SelectedList';

function Aktivointi() {
    const navigate = useNavigate();
    const location = useLocation();
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['aktivointi']);
    const userInfo = useContext(UserContext);

    const [lahdeKysymysryhma, setLahdeKysymysryhma] = useState<KyselyType | null>(null);
    const [lahdeKysely, setLahdeKysely] = useState<ArvoKysely>();
    const [kayttorajat, setKayttorajat] = useState<Kayttoraja[]>([]);

    const [valittavat, setValittavat] = useState<OppilaitosSetType>(getDefaultEmptySet());
    const [valitut, setValitut] = useState<OppilaitosSetType>(getDefaultEmptySet());
    const [aktivoidut, setAktivoidut] = useState<OppilaitosSetType>(getDefaultEmptySet());

    const submitRef = useRef<any | null>(null);

    type KayttoonottoFormType = {
        saate: string;
        startDate: Date | null;
        endDate: Date | null;
        kayttoonotettavat: OppilaitosSetType;
    };

    const {
        handleSubmit,
        control,
        reset,
        formState: {errors, isDirty},
    } = useForm<KayttoonottoFormType>({
        criteriaMode: 'firstError',
        defaultValues: {
            saate: '',
            startDate: null,
            endDate: null,
            kayttoonotettavat: getDefaultEmptySet(),
        } as KayttoonottoFormType,
    } as UseFormProps<KayttoonottoFormType, any> | undefined);

    /**
     +  * Subscribe date fields reactively in a compiler-friendly way.
     +  */
    const watchedDates = useWatch({
        control,
        name: ['startDate', 'endDate'] as const,
    });

    // estä no-unused-vars
    void watchedDates;

    const kysymysryhmaId = getQueryParamAsNumber(location, 'id');
    useEffect(() => {
        if (kysymysryhmaId) {
            const queries = forkJoin([
                arvoGetKysymysryhma$(kysymysryhmaId),
                virkailijapalveluGetAluejako$(userInfo!)(
                    userInfo?.arvoAktiivinenRooli.organisaatio || '',
                ),
                arvoGetAllKyselyt$(),
                arvoGetKysymysryhmaKayttoraja$(kysymysryhmaId),
            ]);

            queries.subscribe(
                ([kysymysryhma, toimipaikat, kayttajanKyselyt, kayttorajaData]: [
                    kysymysryhma: KyselyType,
                    toimipaikat: OppilaitosSetType,
                    kayttajanKyselyt: ArvoKysely[],
                    kayttorajaData: Kayttoraja[],
                ]) => {
                    setLahdeKysymysryhma(kysymysryhma);

                    // find existing kysely related to this kysymysryyhma
                    const filteredKyselyt = kayttajanKyselyt.filter((ak: ArvoKysely) => {
                        const loppu = parseISO(ak.voimassa_loppupvm);
                        const nyt = new Date();

                        return (
                            ak.metatiedot.valssi_kysymysryhma === kysymysryhma.id &&
                            (isSameDay(nyt, loppu) || isBefore(nyt, loppu))
                        );
                    });

                    // pop first kysely to fill up saate and date fields
                    const existingKysely = filteredKyselyt.find((e) => !!e);
                    if (existingKysely) {
                        setLahdeKysely(existingKysely);
                        const formValues = {
                            startDate: parseISO(existingKysely.voimassa_alkupvm),
                            endDate: parseISO(existingKysely.voimassa_loppupvm),
                            saate: existingKysely.metatiedot.valssi_saate,
                            kayttoonotettavat: getDefaultEmptySet(),
                        };
                        reset(formValues);
                    }

                    // loop trough related kyselyt to find activated toimipaikat
                    const oidList = filteredKyselyt.map((f: ArvoKysely) => f.oppilaitos);

                    const aktivoidutLista = filterOppilaitosSetByOid(
                        toimipaikat,
                        oidList,
                    );

                    setAktivoidut(aktivoidutLista);
                    setValittavat(itemsNot(toimipaikat, aktivoidutLista));
                    setKayttorajat(kayttorajaData);
                },
            );
        }
    }, [kysymysryhmaId, location, reset, userInfo]);

    if (lahdeKysymysryhma === null) {
        return null;
    }

    const massaSyottoPost = (
        formData: KayttoonottoFormType,
        nameExtender?: number,
    ): ArvoKyselyMassPost => {
        const alkupvm = format(formData.startDate!, 'yyyy-MM-dd');
        const loppupvm = format(formData.endDate!, 'yyyy-MM-dd');
        return {
            kyselyt: flattenItems(formData.kayttoonotettavat, lang).map((toimipaikka) => {
                const nimi = kyselyNameGenerator(
                    lahdeKysymysryhma,
                    formData.startDate,
                    toimipaikka,
                    nameExtender,
                );

                return {
                    tila: 'julkaistu',
                    voimassa_alkupvm: alkupvm,
                    voimassa_loppupvm: loppupvm,
                    nimi_fi: nimi.fi,
                    nimi_sv: nimi.sv,
                    oppilaitos: toimipaikka.oid,
                    tyyppi: lahdeKysymysryhma.lomaketyyppi,
                    metatiedot: {
                        valssi_saate: formData.saate,
                        valssi_kysymysryhma: lahdeKysymysryhma.id,
                    },
                    kyselykerrat: [
                        {
                            nimi: nimi.fi,
                            voimassa_alkupvm: alkupvm,
                            voimassa_loppupvm: loppupvm,
                        },
                    ],
                    kysymysryhmat: [
                        {
                            kysymysryhmaid: lahdeKysymysryhma.id,
                        },
                    ],
                } as ArvoKyselyPost;
            }),
        };
    };

    const handleKayttoonOtto = (formData: KayttoonottoFormType, retryCounter = 0) => {
        const maxRetry = 2;

        arvoMassAddKysely$(
            massaSyottoPost(formData, retryCounter > 0 ? retryCounter + 1 : undefined),
        ).subscribe({
            complete: () => {
                const alert = {
                    title: {key: 'alert-success-title', ns: 'aktivointi'},
                    severity: 'success',
                } as AlertType;
                AlertService.showAlert(alert);
                navigate(`/tiedonkeruu`);
            },
            error: (error: AjaxError) => {
                const errorMsgRaw: string | string[] = toJson(error.response);
                const sameNameError = 'kysely.massasyotto.samanniminen';

                const isSameNameError = Array.isArray(errorMsgRaw)
                    ? errorMsgRaw.some((errorMsg: string) =>
                          errorMsg.startsWith(sameNameError),
                      )
                    : errorMsgRaw.startsWith(sameNameError);

                if (error.status === 400 && isSameNameError) {
                    if (retryCounter <= maxRetry) {
                        console.info(
                            'Questionnaire with same name found, let´s try again',
                            retryCounter,
                        );
                        handleKayttoonOtto(formData, retryCounter + 1);
                    } else {
                        console.error(
                            'Questionnaire with same name found and retry count has exceeded',
                            retryCounter,
                        );
                        ErrorService.addHttpError(error, {
                            400: {
                                severity: 'error',
                                title: {key: 'alert-error-title', ns: 'aktivointi'},
                                body: {
                                    key: 'alert-error-body-same-name-count-exceeded',
                                    ns: 'aktivointi',
                                },
                            } as AlertType,
                        });
                    }
                } else if ([400, 404].includes(error.status)) {
                    ErrorService.addHttpError(error, {
                        400: {
                            severity: 'error',
                            title: {key: 'alert-error-title', ns: 'aktivointi'},
                            body: {key: '400-general-body', ns: 'alert'},
                        } as AlertType,
                        404: {
                            severity: 'error',
                            title: {key: 'alert-error-title', ns: 'aktivointi'},
                            body: {key: '404-general-body', ns: 'alert'},
                        } as AlertType,
                    });
                }
            },
        });
    };

    const onSubmit: SubmitHandler<KayttoonottoFormType> = (formData) => {
        handleKayttoonOtto(formData);
    };

    return (
        <>
            <h1>{t('sivun-otsikko')}</h1>

            <SinglePanelAccordion
                alignLeft
                alignColumn
                openText={t('esikatselu-avaa', {ns: 'yleiset'})}
                closeText={t('esikatselu-sulje', {ns: 'yleiset'})}
                title={`${
                    lahdeKysymysryhma
                        ? lahdeKysymysryhma.topic[lang as keyof TextType]
                        : ''
                }`}
            >
                <Box sx={{maxWidth: 'md'}}>
                    <Kysely selectedKysely={lahdeKysymysryhma} />
                </Box>
            </SinglePanelAccordion>

            <form onSubmit={handleSubmit(onSubmit)} className="form">
                <div className={styles['section-container']}>
                    <SingleField
                        type={InputTypes.multiline}
                        id="saate"
                        control={control}
                        disabled={!!lahdeKysely}
                        required
                        multiLineResize
                        title={t('saateviesti-label')}
                        fieldErrors={errors.saate}
                        customErrorMessages={{
                            required: t('lisaa-saateviesti'),
                        }}
                        maxLength={MaxLengths.default}
                    />
                </div>

                <div className={styles['section-container']}>
                    <h3>{capitalize(t('vastausaika', {ns: 'lahetys'}))}</h3>
                    <DateRangeField
                        idStartDate="startDate"
                        idEndDate="endDate"
                        disabled={!!lahdeKysely}
                        labelStart={t('alkupvm', {ns: 'aktivointi'})}
                        labelEnd={t('loppupvm', {ns: 'aktivointi'})}
                        rangeMin={new Date()}
                        required
                        customErrorMessagesStart={{
                            required: t('valitse-aloittamispaivamaara'),
                        }}
                        customErrorMessagesEnd={{
                            required: t('valitse-paattymispaivamaara'),
                        }}
                        control={control}
                    />
                </div>

                <div className={styles['section-container']}>
                    <Controller
                        name="kayttoonotettavat"
                        control={control}
                        rules={{
                            validate: (value) => itemsLength(value) > 0,
                        }}
                        render={({field, fieldState}) => {
                            const {onChange} = field;
                            const {error} = fieldState;
                            return (
                                <>
                                    <Grid
                                        container
                                        rowSpacing="3rem"
                                        columnSpacing="1rem"
                                    >
                                        <SelectionList
                                            left={valittavat}
                                            setLeft={setValittavat}
                                            right={valitut}
                                            setRight={(uudetValitut) => {
                                                setValitut(uudetValitut);
                                                onChange(uudetValitut);
                                            }}
                                            selectableGroups
                                        />
                                        {itemsLength(aktivoidut) > 0 && (
                                            <SelectedList list={aktivoidut} />
                                        )}
                                    </Grid>
                                    <div>
                                        {error && (
                                            <p className="error" role="alert">
                                                <WarningIcon />
                                                {t('valitse-ainakin-yksi-toimpaikka')}
                                            </p>
                                        )}
                                    </div>
                                </>
                            );
                        }}
                    />
                </div>

                <p className={styles['required-fields-info']}>
                    {t('pakolliset-kentat-info', {ns: 'yleiset'})}
                </p>

                <div className={styles['section-container']}>
                    <button type="submit" ref={submitRef} style={{display: 'none'}}>
                        form submit button hiding and waiting to be confirmed
                    </button>
                    <Grid container spacing={2}>
                        <Grid>
                            {isDirty ? (
                                <ConfirmationDialog
                                    title={t('painike-takaisin-otsikko')}
                                    confirmBtnText={t('painike-kylla', {ns: 'yleiset'})}
                                    cancelBtnText={t('painike-takaisin-cancel')}
                                    confirm={() => navigate(`/`)}
                                    content={<p>{t('painike-takaisin-teksti')}</p>}
                                >
                                    <button type="button" className="secondary">
                                        {t('painike-takaisin')}
                                    </button>
                                </ConfirmationDialog>
                            ) : (
                                <button
                                    className="secondary"
                                    type="button"
                                    onClick={() => navigate(`/`)}
                                >
                                    {t('peruuta')}
                                </button>
                            )}
                        </Grid>
                        <Grid>
                            <ConfirmationDialog
                                title={t('konfirmaatio-otsikko')}
                                confirm={() => submitRef.current.click()}
                                confirmBtnText={t('painike-aktivoi')}
                                content={
                                    <>
                                        <p>{t('konfirmaatio-sisalto')}</p>
                                        <ol>
                                            {flattenItems(valitut, lang).map(
                                                (valittu) => (
                                                    <li key={valittu.oid}>
                                                        {
                                                            valittu.name[
                                                                lang as keyof TextType
                                                            ]
                                                        }
                                                    </li>
                                                ),
                                            )}
                                        </ol>
                                    </>
                                }
                            >
                                <button
                                    type="button"
                                    disabled={
                                        !!hasKayttoraja(kayttorajat, kysymysryhmaId!)
                                    }
                                >
                                    {t('painike-aktivoi')}
                                </button>
                            </ConfirmationDialog>
                        </Grid>
                    </Grid>
                </div>
            </form>
        </>
    );
}

export default Aktivointi;
