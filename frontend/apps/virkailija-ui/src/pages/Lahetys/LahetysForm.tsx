import React, {useState, useEffect, useContext, useRef} from 'react';
import {useTranslation} from 'react-i18next';
import {toDate, isValid} from 'date-fns';
import {Box} from '@mui/material';
import {useForm, SubmitHandler, Controller} from 'react-hook-form';
import {useNavigate} from 'react-router-dom';
import WarningIcon from '@mui/icons-material/Warning';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import {uniqueNumber} from '@cscfi/shared/utils/helpers';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import Kysely from '@cscfi/shared/components/Kysely/Kysely';
import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import {
    FormType,
    PeopleType,
    TehtavanimikkeetType,
    LastKyselysendType,
    HasBeenSentToPeopleType,
    virkailijapalveluSendUpdateKysely$,
    VirkailijapalveluUpdateKyselyResponseType,
    virkailijapalveluSendReminderKysely$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {
    arvoGetKysymysryhmaKayttoraja$,
    Kayttoraja,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import InputTypes from '@cscfi/shared/components/InputType/InputTypes';
import SingleField from '@cscfi/shared/components/Form/FormFields/SingleField/SingleField';
import DateRangeField from '@cscfi/shared/components/Form/FormFields/DateRangeField/DateRangeField';
import {MaxLengths} from '@cscfi/shared/utils/validators';
import GuardedComponentWrapper from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import SinglePanelAccordion from '../../components/SinglePanelAccordion/SinglePanelAccordion';
import styles from './Lahetys.module.css';
import UserContext from '../../Context';
import {hasKayttoraja} from '../../utils/helpers';

export type DuplicateEmailsPeopleType = PeopleType & {
    duplicateEmail: boolean; // Marks whether the list of people has the same email address on more than one person.
};

interface LahetysFormProps {
    onSubmit: SubmitHandler<FormType>;
    kysely: KyselyType | null;
    kyselykertaId?: number;
    emailSubjectFn: (nameExtender?: number) => TextType;
    startDateLimit: Date | undefined;
    endDateLimit: Date | undefined;
    saateviesti: string;
    numOfUnanswered: number;
    startEDate?: Date | null | number | undefined;
    endEDate: Date | null | number;
    peopleListAll?: DuplicateEmailsPeopleType[];
    peopleList?: DuplicateEmailsPeopleType[];
    hasBeenSentToPeople: HasBeenSentToPeopleType[];
    fromVarda?: boolean;
    oid?: string;
    lastKyselysend: LastKyselysendType | null;
}
function LahetysForm({
    onSubmit,
    kysely,
    kyselykertaId,
    emailSubjectFn,
    startDateLimit,
    endDateLimit,
    saateviesti,
    numOfUnanswered,
    startEDate,
    endEDate,
    peopleListAll = [],
    peopleList = [],
    hasBeenSentToPeople,
    fromVarda = false,
    oid,
    lastKyselysend,
}: LahetysFormProps) {
    const navigate = useNavigate();
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['lahetys']);
    const userInfo: any = useContext(UserContext);
    const submitRef = useRef<any | null>(null);

    const [filterVal, setFilterVal] = useState<string>('');
    const [peopleListFiltered, setPeopleListFiltered] = useState<
        DuplicateEmailsPeopleType[]
    >([]);
    const [sentListSent, setSentListSent] = useState<HasBeenSentToPeopleType[]>([]);
    const [sentListFailed, setSentListFailed] = useState<HasBeenSentToPeopleType[]>([]);
    const [sentNumUnanswered, setSentNumUnanswered] = useState<number>(0);
    const [reSentPeople, setReSentPeople] = useState<number[]>([]);
    const [minDate, setMinDate] = useState<Date | undefined | number>(toDate(Date.now()));
    const [maxDate, setMaxDate] = useState<Date | undefined | number>();
    const [oppilaitos, setOppilaitos] = useState<any>([]);
    const [kayttorajat, setKayttorajat] = useState<Kayttoraja[]>([]);

    useEffect(() => {
        if (userInfo?.rooli.kayttooikeus === ArvoRoles.PAAKAYTTAJA) {
            arvoGetKysymysryhmaKayttoraja$(kysely?.id).subscribe((krs) =>
                setKayttorajat(krs),
            );
        }
    }, [kysely?.id, userInfo?.rooli.kayttooikeus]);

    const pdfReplacementRegEx = /' '/g;
    const pdfname = kysely
        ? `${kysely.topic[lang as keyof TextType]
              .trim()
              .replace(pdfReplacementRegEx, '_')}.pdf`
        : '';
    const {
        handleSubmit,
        control,
        reset,
        watch,
        formState: {errors, isDirty},
    } = useForm<FormType>({
        criteriaMode: 'firstError',
        defaultValues: {message: '', generatedEmails: [], tyontekijat: ''},
    });

    /**
     * unless these dates won't get updated into formValues upon field changes
     * mandatory to validate dates intersecting each other.
     */
    watch();

    const filterPeopleList = (val: string) => {
        setFilterVal(val);
        let filteredTehtavanimikkeet;
        const filteredResults = peopleList
            ? peopleList.filter((people) => {
                  filteredTehtavanimikkeet = people.tehtavanimikkeet?.map(
                      (nimike: TehtavanimikkeetType) =>
                          nimike.tehtavanimike_values?.[lang].nimi
                              .toLowerCase()
                              .includes(val.toLowerCase()),
                  );

                  const filtered = filteredTehtavanimikkeet?.includes(true);
                  return (
                      people.kokoNimi?.toLowerCase().includes(val.toLowerCase()) ||
                      filtered
                  );
              })
            : [];
        setPeopleListFiltered(filteredResults);
        return false;
    };

    const redirectBack = () => {
        navigate('/');
    };

    const seleceOneEmp = (
        event: React.ChangeEvent<HTMLInputElement>,
        checked: boolean,
        value: DuplicateEmailsPeopleType[] | undefined,
        onChange: (...event: any[]) => void,
    ) => {
        const ttid = parseInt(event.target.value, 10);
        const oldChecked = value?.length ? value : [];
        if (checked) {
            const newChecked = [
                ...oldChecked,
                peopleListFiltered.find((ppl) => ttid === ppl.tyontekija_id),
            ];
            onChange(newChecked);
        } else {
            onChange(oldChecked.filter((ppl) => ttid !== ppl.tyontekija_id));
        }
    };

    const selectAllEmp = (
        checked: boolean,
        value: DuplicateEmailsPeopleType[] | undefined,
        onChange: (...event: any[]) => void,
    ) => {
        const oldChecked = value?.length ? value : [];
        if (checked) {
            onChange([...oldChecked, ...peopleListFiltered]);
        } else {
            const ttids = peopleListFiltered.map((ppl) => ppl.tyontekija_id);
            onChange(oldChecked.filter((ppl) => !ttids.includes(ppl.tyontekija_id)));
        }
    };

    const allEmpSelected = (value: PeopleType[] | undefined) =>
        peopleListFiltered.every((ppl) =>
            value?.find(
                (alreadyChecked) => alreadyChecked.tyontekija_id === ppl.tyontekija_id,
            ),
        );

    // initializing the form values
    useEffect(() => {
        const formValues = {
            startDate: startEDate,
            endDate: endEDate,
            message: lastKyselysend?.message && (lastKyselysend?.message || ''),
            generatedEmails: [],
            tyontekijat: '',
        };
        if (lastKyselysend?.vastaajatunnus) {
            const [alkupvm, loppupvm] = [
                new Date(lastKyselysend.vastaajatunnus?.voimassa_alkupvm),
                new Date(lastKyselysend.vastaajatunnus?.voimassa_loppupvm),
            ];
            if (isValid(alkupvm)) {
                setMinDate(alkupvm);
                formValues.startDate = alkupvm;
            }
            if (isValid(loppupvm)) {
                setMaxDate(loppupvm);
                formValues.endDate = loppupvm;
            }
        } else {
            setMinDate(startDateLimit);
            setMaxDate(endDateLimit);
            const current = userInfo.rooli.kayttooikeus;
            if (current === ArvoRoles.PAAKAYTTAJA) {
                formValues.startDate = toDate(Date.now());
            }
        }
        reset(formValues);

        const oppilaitosVar = userInfo?.rooli.oppilaitokset?.filter(
            (element: any) => element.oppilaitos_oid === oid,
        );
        setOppilaitos(oppilaitosVar);
        const sent =
            hasBeenSentToPeople?.filter(
                (element: HasBeenSentToPeopleType) =>
                    element.msg_status === 'delivered' || element.msg_status === 'sent',
            ) || [];
        setSentListSent(sent);
        const failed =
            hasBeenSentToPeople?.filter(
                (element: HasBeenSentToPeopleType) => element.msg_status === 'failed',
            ) || [];

        setSentListFailed(failed);
        setPeopleListFiltered(peopleList || []);
        if (numOfUnanswered) setSentNumUnanswered(numOfUnanswered);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [endEDate, setPeopleListFiltered, hasBeenSentToPeople, lastKyselysend]);

    const reSend = (userId: number, userEmail: string) => {
        virkailijapalveluSendUpdateKysely$(userInfo)([
            {
                id: userId,
                email: userEmail,
            },
        ]).subscribe((response: VirkailijapalveluUpdateKyselyResponseType) => {
            setReSentPeople([...reSentPeople, userId]);
            const alert = {
                title: {
                    key: 'kysely-on-lahetetty',
                    ns: 'lahetys',
                    lahetetty: response.updates,
                },
                severity: 'success',
            } as AlertType;
            AlertService.showAlert(alert);
        });
    };

    const sendReminder = (kkId: number) => {
        virkailijapalveluSendReminderKysely$(userInfo)(kkId).subscribe((response) => {
            const alert = {
                title: {
                    key: 'muistutus-on-lahetetty',
                    ns: 'lahetys',
                    num: response.updates,
                },
                severity: 'success',
            } as AlertType;
            AlertService.showAlert(alert);
        });
    };

    const renderSentList = (sentList: HasBeenSentToPeopleType[] | [], failed: boolean) =>
        sentList?.map((item: HasBeenSentToPeopleType) => {
            // for preventing re-sending something that has just been sent.
            const justSent = item.msg_status === 'sent' || reSentPeople.includes(item.id);

            // look for a match between personnel list and sent-list.
            const vardaPpl = peopleListAll?.find(
                (ppl) => ppl.tyontekija_id === item.tyontekija_id,
            );

            // if there is a match in the sent-list, and the email adderss is
            // different from current address, return the new address.
            const [emailChanged, newEmail]: [emailChanged: boolean, newEmail: string] =
                vardaPpl && vardaPpl.email.toLowerCase() !== item.email.toLowerCase()
                    ? [true, vardaPpl.email]
                    : [false, ''];

            return (
                <ul>
                    <li key={`${item.id}-${item.email}`}>
                        <div className={styles['sent-prople-item']}>
                            <div className={styles['sent-people-item-name']}>
                                {item.email}
                            </div>
                            {(!failed || emailChanged) && (
                                <div className={styles['sent-people-item-btn']}>
                                    <button
                                        disabled={justSent}
                                        className="small"
                                        type="button"
                                        onClick={() =>
                                            reSend(
                                                item.id,
                                                emailChanged ? newEmail : item.email,
                                            )
                                        }
                                    >
                                        {t('laheta-uudelleen')}
                                    </button>
                                    {!justSent && emailChanged && (
                                        <span>{`${t('sahkoposti-muuttunut')}: ${newEmail}`}</span>
                                    )}
                                </div>
                            )}
                        </div>
                    </li>
                </ul>
            );
        });

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="form">
            <h1>{t('sivun-otsikko')}</h1>
            <GuardedComponentWrapper roles={{arvo: [ArvoRoles.TOTEUTTAJA]}}>
                <Box className={styles['accompanying-msg']}>
                    <h3>{t('saateviesti-otsikko')}</h3>
                    <p>{saateviesti}</p>
                </Box>
            </GuardedComponentWrapper>
            <SinglePanelAccordion
                alignLeft
                alignColumn
                openText={t('esikatselu-avaa', {ns: 'yleiset'})}
                closeText={t('esikatselu-sulje', {ns: 'yleiset'})}
                title={`${kysely ? kysely.topic[lang as keyof TextType] : ''}`}
            >
                <Box sx={{maxWidth: 'md'}}>
                    {kysely && <Kysely selectedKysely={kysely} />}
                </Box>
            </SinglePanelAccordion>
            <div className={styles['section-container']}>
                <h3>{t('vastausaika')}</h3>
                <div className={styles['section-container']}>
                    <DateRangeField
                        idStartDate="startDate"
                        idEndDate="endDate"
                        disabled={
                            lastKyselysend !== null ||
                            userInfo.rooli.kayttooikeus === ArvoRoles.TOTEUTTAJA
                        }
                        labelStart={t('alkupvm', {ns: 'aktivointi'})}
                        labelEnd={t('loppupvm', {ns: 'aktivointi'})}
                        rangeMin={minDate}
                        rangeMax={maxDate}
                        disableStartDate
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
            </div>
            <h3>{t('sahkopostin-tiedot')}</h3>
            <div className={styles['grid-container']}>
                <div className={styles['grid-label']}>{t('lahettaja')}</div>
                <div>{t('lahettaja-nimi')} &lt;no-reply@karvi.fi&gt;</div>

                <div className={styles['grid-label']}>{t('liitetiedosto')}</div>
                <div>{pdfname}</div>

                <div className={styles['grid-label']}>{t('sahkopostin-otsikko')}</div>
                <div>{emailSubjectFn()[lang as keyof TextType]}</div>
            </div>
            <h2>
                {oppilaitos &&
                    (lang === 'fi'
                        ? oppilaitos[0]?.oppilaitos_fi
                        : oppilaitos[0]?.oppilaitos_sv)}
            </h2>
            {lastKyselysend && (
                <>
                    {sentListSent?.length > 0 && (
                        <div className={styles['sent-list-wrapper']}>
                            <SinglePanelAccordion
                                alignLeft
                                alignColumn
                                openText={t('avaa')}
                                closeText={t('sulje')}
                                title={t('onnistuneet-lahetykset')}
                            >
                                <Box sx={{maxWidth: 'md'}}>
                                    {sentNumUnanswered > 0 && (
                                        <div className={styles['sent-reminder-wrapper']}>
                                            <h3 className={styles['sent-reminder-label']}>
                                                {t('laheta-muistutus-otsikko')}
                                            </h3>
                                            <span>
                                                {t('laheta-muistutus-maara', {
                                                    num: numOfUnanswered?.toString(),
                                                })}
                                            </span>
                                            <button
                                                className="small"
                                                type="button"
                                                disabled={!kyselykertaId}
                                                onClick={
                                                    kyselykertaId
                                                        ? () =>
                                                              sendReminder(kyselykertaId)
                                                        : () => null
                                                }
                                            >
                                                {t('laheta-muistutus-painike')}
                                            </button>
                                        </div>
                                    )}
                                    {renderSentList(sentListSent, false)}
                                </Box>
                            </SinglePanelAccordion>
                        </div>
                    )}
                    {sentListFailed?.length > 0 && (
                        <div className={styles['sent-list-wrapper']}>
                            <SinglePanelAccordion
                                alignLeft
                                alignColumn
                                openText={t('avaa')}
                                closeText={t('sulje')}
                                title={t('epaonnistuneet-lahetykset')}
                            >
                                <Box sx={{maxWidth: 'md'}}>
                                    {renderSentList(sentListFailed, true)}
                                </Box>
                            </SinglePanelAccordion>
                        </div>
                    )}
                </>
            )}
            {!fromVarda ? (
                <SingleField
                    type={InputTypes.emailList}
                    id="tyontekijat"
                    control={control}
                    required
                    multiLineResize
                    title={t('sahkopostin-vastaanottajat-label')}
                    fieldErrors={errors.tyontekijat}
                    customErrorMessages={{
                        required: t('syota-ainakin-yksi-sahkopostiosoite'),
                    }}
                    maxLength={MaxLengths.default}
                />
            ) : (
                <Controller
                    name="generatedEmails"
                    control={control}
                    rules={{
                        validate: (value) => value && value?.length > 0,
                    }}
                    render={({field, fieldState}) => {
                        const {value, onChange} = field;
                        const {error} = fieldState;
                        return (
                            <div className={styles['people-list-wrapper']}>
                                <label
                                    htmlFor="filterPeople"
                                    className={styles['people-list-header']}
                                >
                                    {t('valitse-tyontekijat-joille-kysely-lahetetaan')} *
                                </label>
                                <input
                                    type="text"
                                    value={filterVal}
                                    aria-label={t('aria-label-vastaanottajat')}
                                    id="filterPeople"
                                    className={styles['filter-people']}
                                    placeholder={t('suodata')}
                                    onChange={(
                                        e: React.ChangeEvent<HTMLInputElement>,
                                    ) => {
                                        filterPeopleList(e.target.value);
                                    }}
                                />
                                <div className={styles['select-all-people-wrapper']}>
                                    <FormControlLabel
                                        label={t('valitse-kaikki-tyontekijat')}
                                        control={
                                            <Checkbox
                                                onChange={(e) =>
                                                    selectAllEmp(
                                                        e.target.checked,
                                                        value,
                                                        onChange,
                                                    )
                                                }
                                                checked={allEmpSelected(value)}
                                                name="select-all-people"
                                            />
                                        }
                                    />
                                </div>

                                <div>
                                    {error && (
                                        <p className="error" role="alert">
                                            <WarningIcon />
                                            {t(
                                                'valitse-ainakin-yksi-henkilo-jolle-laheteaan',
                                            )}
                                        </p>
                                    )}
                                </div>
                                <ul className={styles['people-list']}>
                                    {peopleListFiltered.map((people: any, i: number) => (
                                        <li key={`${people.kokoNimi}${people.email}`}>
                                            <FormControlLabel
                                                label={`${people.kokoNimi},`}
                                                style={{marginRight: '0'}}
                                                control={
                                                    <Checkbox
                                                        value={people.tyontekija_id}
                                                        checked={
                                                            !!value?.find(
                                                                (ppl) =>
                                                                    ppl.tyontekija_id ===
                                                                    people.tyontekija_id,
                                                            )
                                                        }
                                                        onChange={(event, checked) =>
                                                            seleceOneEmp(
                                                                event,
                                                                checked,
                                                                value,
                                                                onChange,
                                                            )
                                                        }
                                                        disabled={people.email === null}
                                                        name={`${people.kokoNimi}${people.email}${i}`}
                                                    />
                                                }
                                            />
                                            {people?.tehtavanimikkeet?.map(
                                                (nimike: any) => (
                                                    <span
                                                        className={
                                                            people.email === null
                                                                ? styles[
                                                                      'people-list-disabled'
                                                                  ]
                                                                : ''
                                                        }
                                                        key={`${
                                                            people.kokoNimi
                                                        }${uniqueNumber()}`}
                                                    >
                                                        {`${nimike?.tehtavanimike_values?.[lang].nimi},`}
                                                    </span>
                                                ),
                                            )}
                                            <span
                                                className={
                                                    people.duplicateEmail
                                                        ? 'overall-error'
                                                        : ''
                                                }
                                                aria-description={
                                                    people.duplicateEmail
                                                        ? t('osoite-ei-uniikki')
                                                        : ''
                                                }
                                            >
                                                {people.email}
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        );
                    }}
                />
            )}

            <div className={styles['message-container']}>
                <SingleField
                    type={InputTypes.multiline}
                    id="message"
                    control={control}
                    disabled={lastKyselysend !== null}
                    required
                    multiLineResize
                    maxLength={MaxLengths.lahetysFormMessage}
                    title={t('sahkoposti-viesti-label')}
                    fieldErrors={errors.message}
                    customErrorMessages={{
                        required: t('syota-viesti-sahkopostiin'),
                        maxLength: t('saateviesti-maksimipituus', {
                            maxLength: MaxLengths.lahetysFormMessage,
                        }),
                    }}
                />
                <p>{t('sahkoposti-viesti-valmis-sisalto')}</p>
            </div>
            <p className={styles['required-fields-info']}>
                {t('pakolliset-kentat-info', {ns: 'yleiset'})}
            </p>
            <div className="button-container">
                {isDirty ? (
                    <ConfirmationDialog
                        title={t('palaa-takaisin-heading')}
                        confirm={redirectBack}
                        content={<p>{t('palaa-takaisin-content')}</p>}
                        confirmBtnText={t('painike-kylla', {ns: 'yleiset'})}
                        cancelBtnText={t('painike-peruuta-sulje')}
                    >
                        <button type="button" className="secondary">
                            {t('painike-peruuta', {ns: 'yleiset'})}
                        </button>
                    </ConfirmationDialog>
                ) : (
                    <button type="button" className="secondary" onClick={redirectBack}>
                        {t('painike-poistu', {ns: 'yleiset'})}
                    </button>
                )}

                <button type="submit" ref={submitRef} style={{display: 'none'}}>
                    form submit button hiding and waiting to be confirmed
                </button>

                <ConfirmationDialog
                    title={t('dialogi-otsikko-laheta')}
                    confirm={() => submitRef.current.click()}
                    content={<p>{t('dialogi-teksti-laheta')}</p>}
                    confirmBtnText={t('painike-laheta')}
                >
                    <button
                        type="button"
                        disabled={!!(kysely?.id && hasKayttoraja(kayttorajat, kysely.id))}
                    >
                        {t('painike-laheta')}
                    </button>
                </ConfirmationDialog>
            </div>
        </form>
    );
}
export default LahetysForm;
