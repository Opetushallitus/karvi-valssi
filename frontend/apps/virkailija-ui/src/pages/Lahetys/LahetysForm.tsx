import React, {useState, MouseEvent, useEffect, useContext} from 'react';
import {useTranslation, getI18n} from 'react-i18next';
import {toDate} from 'date-fns';
import {Box} from '@mui/material';
import {useForm, Controller, SubmitHandler} from 'react-hook-form';
import {useNavigate} from 'react-router-dom';
import WarningIcon from '@mui/icons-material/Warning';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';

import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import GenericTextField from '@cscfi/shared/components/GenericTextField/GenericTextField';
import {isValidEmailList} from '@cscfi/shared/utils/validators';
import DateRangePickerField from '@cscfi/shared/components/DateRangePickerField/DateRangePickerField';
import {uniqueNumber} from '@cscfi/shared/utils/helpers';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import Kysely from '@cscfi/shared/components/Kysely/Kysely';
import {
    FormType,
    PeopleType,
    TehtavanimikkeetType,
    LastKyselysendType,
    HasBeenSentToPeopleType,
    VirkailijapalveluKyselyResponseType,
    virkailijapalveluSendUpdateKysely$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import GuardedComponentWrapper, {
    ValssiUserLevel,
} from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import SinglePanelAccordion from '../../components/SinglePanelAccordion/SinglePanelAccordion';
import styles from './Lahetys.module.css';
import UserContext from '../../Context';

interface LahetysFormProps {
    onSubmit: SubmitHandler<FormType>;
    kysely: KyselyType | null;
    emailSubject: TextType;
    startDateLimit: Date | undefined;
    endDateLimit: Date | undefined;
    saateviesti: string;
    startEDate?: Date | null | number | undefined;
    endEDate: Date | null | number;
    peopleListAll?: PeopleType[];
    peopleList?: PeopleType[];
    hasBeenSentToPeople: HasBeenSentToPeopleType[];
    fromVarda?: boolean;
    oid?: string;
    lastKyselysend: LastKyselysendType | null;
}
function LahetysForm({
    onSubmit,
    kysely,
    emailSubject,
    startDateLimit,
    endDateLimit,
    saateviesti,
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
    const locale = getI18n().language;
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['lahetys']);
    const forceUpdate: () => void = React.useState({})[1].bind(null, {}); // Doesnt work without
    const userInfo: any = useContext(UserContext);

    const [startDate, setStartDate] = useState<Date | null | number | undefined>(null);
    const [endDate, setEndDate] = useState<Date | null | number>(null);
    const [generatedEmails, setGeneratedEmails] = useState<PeopleType[] | null>(null);
    const [filterVal, setFilterVal] = useState<string>('');
    const [peopleListFiltered, setPeopleListFiltered] = useState<PeopleType[]>([]);
    const [readyForSubmit, setReadyForSubmit] = useState<boolean>(false);
    const [allPeopleSelected, setAllPeopleSelected] = useState<boolean>(false);
    const [sentListSent, setSentListSent] = useState<HasBeenSentToPeopleType[] | []>([]);
    const [sentListFailed, setSentListFailed] = useState<HasBeenSentToPeopleType[] | []>(
        [],
    );
    const [reSentPeople, setReSentPeople] = useState<number[]>([]);
    const [minDate, SetMinDate] = useState<Date | undefined | number>(toDate(Date.now()));
    const [maxDate, SetMaxDate] = useState<Date | undefined | number>(undefined);

    const [oppilaitos, setOppilaitos] = useState<any>([]);

    const pdfReplacementRegEx = /' '/g;
    const pdfname = kysely
        ? `${kysely.topic[lang as keyof TextType]
              .trim()
              .replace(pdfReplacementRegEx, '_')}.pdf`
        : '';
    const {
        handleSubmit,
        control,
        formState: {errors},
        setValue,
        setError,
        trigger,
        clearErrors,
    } = useForm<FormType>();

    const filterPeopleList = (val: string) => {
        setFilterVal(val);
        let filteredTehtavanimikkeet;
        const filteredResults = peopleList.filter((people: PeopleType) => {
            filteredTehtavanimikkeet = people.tehtavanimikkeet?.map(
                (nimike: TehtavanimikkeetType) =>
                    nimike.tehtavanimike_values?.[locale].nimi
                        .toLowerCase()
                        .includes(val.toLowerCase()),
            );

            const filtered = filteredTehtavanimikkeet?.includes(true);
            return people.kokoNimi?.toLowerCase().includes(val.toLowerCase()) || filtered;
        });
        setPeopleListFiltered(filteredResults);

        return false;
    };

    const handleEndDateChange = (date: Date | null) => {
        if (date) {
            setEndDate(date);
            setValue('endDate', date, {shouldDirty: true});
        }
    };
    const cancelSubmit = () => {
        setReadyForSubmit(false);
    };
    const redirectBack = () => {
        navigate('/');
    };
    const handleStartDateChange = (date: Date | null) => {
        if (date) {
            setStartDate(date);
            setValue('startDate', date, {shouldDirty: true});
        }
    };
    const editChecked = (index: number) => {
        const {id} = peopleListFiltered[index].checkedElem;
        peopleList.forEach((loopItem: PeopleType, i: number) => {
            if (loopItem.checkedElem.id === id) {
                peopleList[i].checkedElem.checked = !loopItem.checkedElem.checked;
            }
        });
        const finalList = peopleList.filter(
            (people: PeopleType) => people.checkedElem.checked,
        );
        setValue('generatedEmails', finalList);
        setGeneratedEmails(Object.keys(finalList).length === 0 ? null : finalList);
        forceUpdate();
    };

    const selectAllPeople = (checked: boolean) => {
        setAllPeopleSelected(!allPeopleSelected);
        peopleListFiltered.map((ele: PeopleType) => {
            if (ele.email === null) {
                return false;
            }
            peopleList.forEach((loopItem: PeopleType, i: number) => {
                if (loopItem.checkedElem.id === ele.checkedElem.id) {
                    peopleList[i].checkedElem.checked = checked;
                }
            });
            return false;
        });
        const finalList = peopleList.filter(
            (people: PeopleType) => people.checkedElem.checked,
        );
        setValue('generatedEmails', finalList);
        setGeneratedEmails(Object.keys(finalList).length === 0 ? null : finalList);
        forceUpdate();
    };

    const checkSendForm = (event: MouseEvent<HTMLButtonElement>) => {
        event.preventDefault();
        setReadyForSubmit(true);
        if (!startDate) {
            setError('startDate', {
                type: 'custom',
                message: t('valitse-aloittamispaivamaara'),
            });
            trigger();
        } else {
            clearErrors('startDate');
            trigger();
        }
        if (!endDate || endDate?.toString() === 'Invalid Date') {
            setError('endDate', {
                type: 'custom',
                message: t('valitse-paattymispaivamaara'),
            });
            trigger();
        } else {
            clearErrors('endDate');
            trigger();
        }

        if (fromVarda) {
            if (!generatedEmails) {
                setError('generatedEmails', {
                    type: 'custom',
                });
                trigger();
            } else {
                clearErrors('generatedEmails');
                trigger();
            }
        }
    };

    useEffect(() => {
        if (lastKyselysend?.vastaajatunnus) {
            SetMinDate(new Date(lastKyselysend?.vastaajatunnus?.voimassa_alkupvm));
            SetMaxDate(new Date(lastKyselysend?.vastaajatunnus?.voimassa_loppupvm));

            setValue(
                'endDate',
                new Date(lastKyselysend?.vastaajatunnus?.voimassa_loppupvm),
                {
                    shouldDirty: true,
                },
            );
            setStartDate(new Date(lastKyselysend?.vastaajatunnus?.voimassa_alkupvm));
            setEndDate(new Date(lastKyselysend?.vastaajatunnus?.voimassa_loppupvm));
            setValue('startDate', lastKyselysend?.vastaajatunnus?.voimassa_alkupvm, {
                shouldDirty: true,
            });
        } else {
            SetMinDate(startDateLimit);
            SetMaxDate(endDateLimit);
            setValue('endDate', endEDate, {shouldDirty: true});

            setValue('startDate', startEDate, {shouldDirty: true});
            setStartDate(startEDate);
            setEndDate(endEDate);
            const current = userInfo.rooli.kayttooikeus;
            if (current === ValssiUserLevel.PAAKAYTTAJA) {
                setValue('startDate', toDate(Date.now()), {shouldDirty: true});
                setStartDate(toDate(Date.now()));
            }
        }
        if (lastKyselysend?.message) {
            setValue('message', lastKyselysend?.message, {shouldDirty: true});
        }
        const oppilaitosVar = userInfo?.rooli.oppilaitokset?.filter(
            (element: any) => element.oppilaitos_oid === oid,
        );
        setOppilaitos(oppilaitosVar);
        const sent = hasBeenSentToPeople?.filter(
            (element: HasBeenSentToPeopleType) =>
                element.msg_status === 'delivered' || element.msg_status === 'sent',
        );
        setSentListSent(sent);
        const failed = hasBeenSentToPeople?.filter(
            (element: HasBeenSentToPeopleType) => element.msg_status === 'failed',
        );
        setSentListFailed(failed);

        setPeopleListFiltered(peopleList);
    }, [setValue, endEDate, setPeopleListFiltered, hasBeenSentToPeople, lastKyselysend]); // eslint-disable-line

    const reSend = (userId: number, userEmail: string) => {
        virkailijapalveluSendUpdateKysely$(userInfo)([
            {
                id: userId,
                email: userEmail,
            },
        ]).subscribe((response: VirkailijapalveluKyselyResponseType) => {
            setReSentPeople([...reSentPeople, userId]);
            const alert = {
                title: {
                    key: 'kysely-on-lahetetty',
                    ns: 'lahetys',
                    lahetetty: response.created,
                },
                severity: 'success',
            } as AlertType;
            AlertService.showAlert(alert);
        });
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="form">
            <h1>{t('sivun-otsikko')}</h1>
            <GuardedComponentWrapper allowedValssiRoles={[ValssiUserLevel.TOTEUTTAJA]}>
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
                    <DateRangePickerField
                        disabled={
                            lastKyselysend !== null ||
                            userInfo.rooli.kayttooikeus === ValssiUserLevel.TOTEUTTAJA
                        }
                        labelStart={t('alkupvm', {ns: 'aktivointi'})}
                        labelEnd={t('loppupvm', {ns: 'aktivointi'})}
                        dateStart={startDate || undefined}
                        dateEnd={endDate || undefined}
                        onChangeStart={(val) => handleStartDateChange(val)}
                        onChangeEnd={(val) => handleEndDateChange(val)}
                        errorStartDate={errors.startDate}
                        errorEndDate={errors.endDate}
                        errorStartDateMessage={errors.startDate?.message}
                        errorEndDateMessage={errors.endDate?.message}
                        rangeMin={minDate}
                        rangeMax={maxDate}
                        disableStartDate
                        required
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
                <div>{emailSubject[lang as keyof TextType]}</div>
            </div>
            <h2>
                {oppilaitos &&
                    (locale === 'fi'
                        ? oppilaitos[0]?.oppilaitos_fi
                        : oppilaitos[0]?.oppilaitos_sv)}
            </h2>
            {lastKyselysend && (
                <>
                    {sentListSent?.length > 0 && (
                        <div className={styles['has-sent-list-wrapper']}>
                            <SinglePanelAccordion
                                alignLeft
                                alignColumn
                                openText={t('avaa')}
                                closeText={t('sulje')}
                                title={t('onnistuneet-lahetykset')}
                            >
                                <Box sx={{maxWidth: 'md'}}>
                                    <ul>
                                        {sentListSent?.map(
                                            (item: HasBeenSentToPeopleType) => {
                                                // estetään uudelleenlähetys-napit
                                                // turhat uudelleen painamiset
                                                const justSent =
                                                    item.msg_status === 'sent' ||
                                                    reSentPeople.includes(item.id);

                                                // haetaan työtenkijöistä ja lähtetyistä match
                                                const vardaPpl = peopleListAll?.find(
                                                    (ppl) =>
                                                        ppl.tyontekija_id ===
                                                        item.tyontekija_id,
                                                );

                                                // jos lähtetyistä löytyy match ja se ei vastaa nykyistä
                                                // s-postia palautetaan uusi s-posti
                                                const [emailChanged, newEmail]: [
                                                    emailChanged: boolean,
                                                    newEmail: string,
                                                ] =
                                                    vardaPpl &&
                                                    vardaPpl.email.toLowerCase() !==
                                                        item.email.toLowerCase()
                                                        ? [true, vardaPpl.email]
                                                        : [false, ''];

                                                // TODO: halutaanko näyttää lähtettyjen kohdalla varda nimi jos mahd?

                                                return (
                                                    <li key={`${item.id}-${item.email}}`}>
                                                        <div
                                                            className={
                                                                styles['sent-prople-item']
                                                            }
                                                        >
                                                            <div
                                                                className={
                                                                    styles[
                                                                        'sent-people-item-name'
                                                                    ]
                                                                }
                                                            >
                                                                {item.email}
                                                            </div>
                                                            <div
                                                                className={
                                                                    styles[
                                                                        'sent-people-item-btn'
                                                                    ]
                                                                }
                                                            >
                                                                <button
                                                                    disabled={justSent}
                                                                    className="small"
                                                                    type="button"
                                                                    onClick={() =>
                                                                        reSend(
                                                                            item.id,
                                                                            emailChanged
                                                                                ? newEmail
                                                                                : item.email,
                                                                        )
                                                                    }
                                                                    style={{
                                                                        marginLeft:
                                                                            '0.5rem',
                                                                    }}
                                                                >
                                                                    {t(
                                                                        'laheta-uudelleen',
                                                                    )}
                                                                </button>
                                                                {!justSent &&
                                                                    emailChanged && (
                                                                        <span>{`${t(
                                                                            'sahkoposti-muuttunut',
                                                                        )}: ${newEmail}`}</span>
                                                                    )}
                                                            </div>
                                                        </div>
                                                    </li>
                                                );
                                            },
                                        )}
                                    </ul>
                                </Box>
                            </SinglePanelAccordion>
                        </div>
                    )}
                    {sentListFailed?.length > 0 && (
                        <div className={styles['has-sent-list-wrapper']}>
                            <SinglePanelAccordion
                                alignLeft
                                alignColumn
                                openText={t('avaa')}
                                closeText={t('sulje')}
                                title={t('epaonnistuneet-lahetykset')}
                            >
                                <Box sx={{maxWidth: 'md'}}>
                                    <ul>
                                        {sentListFailed?.map(
                                            (item: HasBeenSentToPeopleType) => (
                                                <li key={`${item.id}-${item.email}}`}>
                                                    {item.email}
                                                </li>
                                            ),
                                        )}
                                    </ul>
                                </Box>
                            </SinglePanelAccordion>
                        </div>
                    )}
                </>
            )}
            {!fromVarda ? (
                <Controller
                    name="tyontekijat"
                    control={control}
                    rules={{
                        required: 'required',
                        pattern: isValidEmailList,
                    }}
                    render={({field}) => (
                        <GenericTextField
                            fullWidth
                            value={field.value}
                            label={`${t('sahkopostin-vastaanottajat-label')} *`}
                            multiLine
                            multiLineResize
                            onChange={(val: string) => {
                                field.onChange(val);
                            }}
                            error={
                                errors.tyontekijat?.type === 'pattern' ||
                                errors.tyontekijat?.type === 'required'
                            }
                            errorMessage={
                                errors.tyontekijat?.type === 'pattern'
                                    ? t('vaaran-mallinen-sahkopostiosoite')
                                    : t('syota-ainakin-yksi-sahkopostiosoite')
                            }
                        />
                    )}
                />
            ) : (
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
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                            filterPeopleList(e.target.value);
                        }}
                    />
                    <div className={styles['select-all-people-wrapper']}>
                        <FormControlLabel
                            label={t('valitse-kaikki-tyontekijat')}
                            control={
                                <Checkbox
                                    onChange={(e) => {
                                        selectAllPeople(e.target.checked);
                                    }}
                                    checked={allPeopleSelected}
                                    name="select-all-people"
                                />
                            }
                        />
                    </div>

                    <div>
                        {errors.generatedEmails && (
                            <p className="error" role="alert">
                                <WarningIcon />
                                {t('valitse-ainakin-yksi-henkilo-jolle-laheteaan')}
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
                                            checked={people.checkedElem!.checked}
                                            onChange={() => {
                                                editChecked(i);
                                            }}
                                            disabled={people.email === null}
                                            name={`${people.kokoNimi}${people.email}${i}`}
                                        />
                                    }
                                />
                                {people?.tehtavanimikkeet?.map((nimike: any) => (
                                    <span
                                        className={
                                            people.email === null
                                                ? styles['people-list-disabled']
                                                : ''
                                        }
                                        key={`${people.kokoNimi}${uniqueNumber()}`}
                                    >
                                        {`${nimike?.tehtavanimike_values?.[locale].nimi},`}
                                    </span>
                                ))}
                                <span
                                    className={
                                        people.email === null
                                            ? styles['people-list-disabled']
                                            : ''
                                    }
                                >
                                    {people.email}
                                </span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
            <div className={styles['message-container']}>
                <Controller
                    name="message"
                    control={control}
                    rules={{required: true, maxLength: 5000}}
                    render={({field}) => (
                        <GenericTextField
                            fullWidth
                            value={field.value}
                            label={`${t('sahkoposti-viesti-label')} *`}
                            multiLine
                            multiLineResize
                            disabled={lastKyselysend !== null}
                            onChange={(val: string) => {
                                field.onChange(val);
                            }}
                            error={
                                errors.message?.type === 'maxLength' ||
                                errors.message?.type === 'required'
                            }
                            errorMessage={
                                errors.message?.type === 'maxLength'
                                    ? t('viestin-maksimi-merkkimaara')
                                    : t('syota-viesti-sahkopostiin')
                            }
                        />
                    )}
                />
                <p>{t('sahkoposti-viesti-valmis-sisalto')}</p>
            </div>
            <p className={styles['required-fields-info']}>
                {t('pakolliset-kentat-info', {ns: 'yleiset'})}
            </p>
            <div className="button-container">
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
                {Object.keys(errors).length === 0 && readyForSubmit && (
                    <ConfirmationDialog
                        title={t('dialogi-otsikko-laheta')}
                        confirm={handleSubmit(onSubmit)}
                        cancel={cancelSubmit}
                        content={<p>{t('dialogi-teksti-laheta')}</p>}
                        confirmBtnText={t('painike-laheta')}
                        showDialogBoolean
                    />
                )}
                <button type="submit" onClick={(event) => checkSendForm(event)}>
                    {t('painike-laheta')}
                </button>
            </div>
        </form>
    );
}
export default LahetysForm;
