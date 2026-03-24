import React, {useContext, useEffect, useMemo, useState} from 'react';
import {useLocation} from 'react-router-dom';
import {format, parse} from 'date-fns';
import {useTranslation} from 'react-i18next';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import DropDownField, {
    DropDownItem,
} from '@cscfi/shared/components/DropDownField/DropDownField';
import {
    getQueryParam,
    getQueryParamAsNumber,
    round,
    downloadPdf,
    sortedLangs,
} from '@cscfi/shared/utils/helpers';
import karviLogo_fi from '@cscfi/shared/components/Navigaatio/KARVI_long_logo.png';
import karviLogo_sv from '@cscfi/shared/components/Navigaatio/NCU_long_logo.png';
import ChartGroup from '@cscfi/shared/components/ChartGroup/ChartGroup';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import {
    JobTitles,
    raportiointipalveluGetAnswersCsv$,
    raportiointipalveluGetRaportti$,
    raportiointipalveluGetRaporttiPdf$,
    RaporttiType,
    ReportingBase,
    ReportingTemplate,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import LomakeTyyppi, {
    henkilostoLomakkeet,
    paakayttajaLomakkeet,
    taydennyskoulutusLomakkeet,
} from '@cscfi/shared/utils/LomakeTyypit';
import ViewIndicators from '@cscfi/shared/components/ViewIndicators/ViewIndicators';
import {Observable} from 'rxjs';
import LaunchIcon from '@mui/icons-material/Launch';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import Grid from '@mui/material/Grid';
import KyselykertaValitsin from '../../components/KyselykertaValitsin/KyselykertaValitsin';
import UserContext from '../../Context';
import GuardedComponentWrapper from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import ButtonWithLink from '../../components/ButtonWithLink/ButtonWithLink';
import styles from './raportit.module.css';
import VirkailijaUILanguageButtons from '../../components/VirkailijaUILanguageButtons/VirkailijaUILanguageButtons';

interface Filters {
    filterNimike: string;
    filterNimikeValikko: string;
    eligibilityChecked: boolean;
    eligibilityCheckedValikko: boolean;
    filterLanguageCode: string;
    filterLanguageCodeValikko: string;
    filterGroup: string;
    filterGroupValikko: string;
}

const initialFilters: Filters = {
    filterNimike: '0',
    filterNimikeValikko: '0',
    eligibilityChecked: false,
    eligibilityCheckedValikko: false,
    filterLanguageCode: 'valitse',
    filterLanguageCodeValikko: 'valitse',
    filterGroup: '-1',
    filterGroupValikko: '-1',
};

interface RaporttipohjaPreview {
    main_description: TextType;
}

interface ViewRaporttiProps {
    preview?: boolean;
}

function ViewRaportti({preview = false}: ViewRaporttiProps) {
    const {t, i18n} = useTranslation(['raportointi']);
    const userInfo = useContext(UserContext);
    const location = useLocation();
    const [raportti, setRaportti] = useState<RaporttiType | null>(null);

    // Pidä local state synkassa i18n:n kanssa tilaamalla kielenmuutoksiin
    const [language, setLanguage] = useState<string>(i18n.language);
    useEffect(() => {
        const handleChange = (lng: string) => setLanguage(lng);
        i18n.on('languageChanged', handleChange);
        return () => i18n.off('languageChanged', handleChange);
    }, [i18n]);

    const fixedT = useMemo(
        () => i18n.getFixedT(language, 'raportointi'),
        [language, i18n],
    );

    const [
        {
            filterNimike,
            filterNimikeValikko,
            eligibilityChecked,
            eligibilityCheckedValikko,
            filterLanguageCode,
            filterLanguageCodeValikko,
            filterGroup,
            filterGroupValikko,
        },
        setFilters,
    ] = useState<Filters>(initialFilters);

    const kysymysryhmaId = getQueryParamAsNumber(location, 'raportti');
    const alkupvm = getQueryParam(location, 'alkupvm');
    const nlimit = 5; // represents the minimum number of participants for showing report data

    const pdfNameGenerator = () => {
        const raporttiName = `nimi_${i18n.language}` as keyof RaporttiType;
        return `${fixedT('raportti')}_${raportti![raporttiName]}.pdf`;
    };

    const csvNameGenerator = () => {
        const raporttiName = `nimi_${i18n.language}` as keyof RaporttiType;
        return `${fixedT('vastaukset')}_${raportti![raporttiName]}.csv`;
    };

    // CSV-observable ei tarvitse manuaalista memoisaatiota
    const fetchRaporttiObservableCsv: Observable<string> =
        raportiointipalveluGetAnswersCsv$(userInfo!)(
            kysymysryhmaId!,
            userInfo!.rooli.organisaatio,
            alkupvm!,
            i18n.language,
        );

    // HUOM: effectiveFilterGroup lisätään myöhemmin — siksi tämä on alempana koodissa.
    // Jotta tyypitys pysyy, määrittelemme ensin muut riippuvuudet.

    const raporttiBase = raportti?.reporting_base;
    const raporttiName = `nimi_${language}` as keyof ReportingBase;
    const helpText = `description_${i18n.language}` as keyof ReportingTemplate;
    const jobTitles = `job_titles_${i18n.language}` as keyof RaporttiType;

    const translatedJobTitles = raportti?.[jobTitles] as Array<JobTitles>;
    const koulutustoimijanNimi =
        `koulutustoimija_nimi_${i18n.language}` as keyof RaporttiType;

    if (translatedJobTitles && translatedJobTitles[0]?.job_title_code !== '0') {
        translatedJobTitles.unshift({
            job_title_code: '0',
            name: t('valitse'),
        });
    }

    const languageCodes = ['valitse'].concat(
        raportti ? sortedLangs(raportti?.language_codes as Array<string>) : [],
    );

    // Ryhmälista ilman sivuvaikutuksia renderissä
    const groupNames = useMemo(
        () =>
            [{id: '-1', name: fixedT('valitse')}].concat(
                raportti
                    ? raportti.aluejako_alueet.map((alue) => ({
                          id: alue.id.toString(),
                          name: alue.name[i18n.language],
                      }))
                    : [],
            ),
        [i18n.language, raportti, fixedT],
    );

    // Johdetut arvot UI:lle ja API-kutsuihin
    const hasGroups = (raportti?.aluejako_alueet?.length ?? 0) > 0;
    const effectiveFilterGroup = hasGroups ? filterGroup : initialFilters.filterGroup;
    const effectiveFilterGroupValikko = hasGroups
        ? filterGroupValikko
        : initialFilters.filterGroupValikko;

    // PDF-observable ilman manuaalista memoisaatiota
    const fetchRaporttiObservablePdf: Observable<string> =
        raportiointipalveluGetRaporttiPdf$(userInfo!)(
            kysymysryhmaId!,
            userInfo!.rooli.organisaatio,
            filterNimike,
            eligibilityChecked,
            filterLanguageCode !== initialFilters.filterLanguageCode
                ? filterLanguageCode
                : '',
            effectiveFilterGroup !== initialFilters.filterGroup
                ? effectiveFilterGroup
                : '',
            alkupvm!,
            userInfo!.rooli.kayttooikeus,
            i18n.language,
            language,
        );

    const clearSelections = () => {
        setFilters(initialFilters);
    };

    const lomaketyypit = [
        ...henkilostoLomakkeet,
        ...taydennyskoulutusLomakkeet,
        LomakeTyyppi.asiantuntijalomake_paivakoti_rakennetekijat,
        LomakeTyyppi.asiantuntijalomake_paivakoti_kansallinen,
    ];

    useEffect(() => {
        if (
            !userInfo ||
            !kysymysryhmaId ||
            !userInfo?.rooli?.organisaatio ||
            !userInfo?.rooli?.kayttooikeus
        ) {
            return;
        }
        const sub = raportiointipalveluGetRaportti$(userInfo)(
            kysymysryhmaId,
            userInfo.rooli.organisaatio,
            filterNimike,
            eligibilityChecked,
            filterLanguageCode !== initialFilters.filterLanguageCode
                ? filterLanguageCode
                : '',
            effectiveFilterGroup !== initialFilters.filterGroup
                ? effectiveFilterGroup
                : '',
            alkupvm!,
            userInfo.rooli.kayttooikeus,
            i18n.language,
        ).subscribe((raporttiVar) => {
            setRaportti(raporttiVar);
        });
        return () => sub.unsubscribe();
    }, [
        userInfo,
        kysymysryhmaId,
        filterNimike,
        eligibilityChecked,
        filterLanguageCode,
        effectiveFilterGroup,
        alkupvm,
        i18n.language,
    ]);

    const descriptionPreview = () => {
        const mainDescription = (
            JSON.parse(
                sessionStorage.getItem(`reportPreviewData_${kysymysryhmaId}`) ?? '{}',
            ) as RaporttipohjaPreview
        )?.main_description?.[i18n.language as keyof TextType];
        return mainDescription ? <p>{mainDescription}</p> : null;
    };

    const defaultKk = (r: RaporttiType) => {
        if (r.created_date) {
            const parsedDate = parse(r.created_date, 'dd.MM.yyyy', new Date());
            return format(parsedDate, 'yyyy-MM-dd');
        }
        return undefined;
    };

    const filterIsDefault = () =>
        filterNimikeValikko === initialFilters.filterNimikeValikko &&
        eligibilityCheckedValikko === initialFilters.eligibilityCheckedValikko &&
        filterLanguageCode === initialFilters.filterLanguageCode &&
        filterGroup === initialFilters.filterGroup;

    return (
        raportti && (
            <div className={styles['raporti-page-wrapper']}>
                <div className={styles['raporti-page-header-wrapper']}>
                    <h1>
                        {preview ? t('raporttipohjan-esikatselu') : t('raportin-katselu')}
                    </h1>
                </div>

                <div className={styles['raportti-options-wrapper']}>
                    <KyselykertaValitsin
                        kyselykertaStart={defaultKk(raportti)}
                        availableKyselykertas={raportti.available_kyselykertas}
                        sideEffects={[clearSelections]}
                        csvObservable={fetchRaporttiObservableCsv}
                        csvName={csvNameGenerator()}
                    />

                    <GuardedComponentWrapper roles={{arvo: [ArvoRoles.PAAKAYTTAJA]}}>
                        {lomaketyypit.includes(
                            raportti?.metatiedot?.lomaketyyppi as LomakeTyyppi,
                        ) && (
                            <div>
                                <h2>{t('raportin-suodatus')}</h2>
                                <Grid container columnSpacing="1rem" rowSpacing="2rem">
                                    {raportti?.metatiedot?.lomaketyyppi !==
                                        LomakeTyyppi.asiantuntijalomake_paivakoti_rakennetekijat &&
                                        raportti?.metatiedot?.lomaketyyppi !==
                                            LomakeTyyppi.asiantuntijalomake_paivakoti_kansallinen && (
                                            <Grid size={12}>
                                                <DropDownField
                                                    id="vastaajan-tehtavanimike"
                                                    value={filterNimikeValikko}
                                                    label={t('vastaajan-tehtavanimike')}
                                                    tightLabel
                                                    options={translatedJobTitles?.map(
                                                        (option) =>
                                                            ({
                                                                value: option.job_title_code,
                                                                name: option.name,
                                                            }) as DropDownItem,
                                                    )}
                                                    onChange={(val: any) =>
                                                        setFilters((prev) => ({
                                                            ...prev,
                                                            filterNimikeValikko: val,
                                                        }))
                                                    }
                                                />
                                                <FormControlLabel
                                                    label={t('kelpoisuus-tehtavaan')}
                                                    role="checkbox"
                                                    control={
                                                        <Checkbox
                                                            key="eligibility"
                                                            checked={
                                                                eligibilityCheckedValikko
                                                            }
                                                            onChange={() =>
                                                                setFilters((prev) => ({
                                                                    ...prev,
                                                                    eligibilityCheckedValikko:
                                                                        !eligibilityCheckedValikko,
                                                                }))
                                                            }
                                                            name="eligibility"
                                                            aria-label={t(
                                                                'kelpoisuus-tehtavaan',
                                                            )}
                                                        />
                                                    }
                                                />
                                            </Grid>
                                        )}

                                    <Grid size={6}>
                                        <DropDownField
                                            id="valitse-toimintakieli"
                                            value={filterLanguageCodeValikko}
                                            label={t('valitse-toimintakieli')}
                                            tightLabel
                                            options={languageCodes.map(
                                                (option) =>
                                                    ({
                                                        value: option,
                                                        name: t(
                                                            `toimintakieli-${option.toLowerCase()}`,
                                                        ),
                                                    }) as DropDownItem,
                                            )}
                                            onChange={(val) =>
                                                setFilters((prev) => ({
                                                    ...prev,
                                                    filterLanguageCodeValikko: val,
                                                }))
                                            }
                                        />
                                    </Grid>

                                    <Grid size={6}>
                                        <DropDownField
                                            id="valitse-alue"
                                            value={effectiveFilterGroupValikko}
                                            label={t('valitse-alue')}
                                            tightLabel
                                            options={groupNames.map(
                                                (option) =>
                                                    ({
                                                        value: option.id,
                                                        name: option.name,
                                                    }) as DropDownItem,
                                            )}
                                            onChange={(val) =>
                                                setFilters((prev) => ({
                                                    ...prev,
                                                    filterGroupValikko: val,
                                                }))
                                            }
                                        />
                                    </Grid>
                                </Grid>

                                <div className={styles['filter-buttons']}>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            clearSelections();
                                            const alert = {
                                                title: {
                                                    key: 'alert-suodattimet-tyhjennetty',
                                                    ns: 'raportointi',
                                                },
                                                severity: 'success',
                                            } as AlertType;
                                            AlertService.showAlert(alert);
                                        }}
                                        className="secondary"
                                        disabled={filterIsDefault()}
                                        aria-label={
                                            filterIsDefault()
                                                ? t('ei-aktiivisia-suodatuksia')
                                                : t('tyhjenna-suodatin')
                                        }
                                    >
                                        {t('tyhjenna-valinnat-nappi')}
                                    </button>

                                    <button
                                        type="button"
                                        onClick={(event) => {
                                            setFilters((prev) => ({
                                                ...prev,
                                                filterNimike: filterNimikeValikko,
                                                eligibilityChecked:
                                                    eligibilityCheckedValikko,
                                                filterLanguageCode:
                                                    filterLanguageCodeValikko,
                                                filterGroup: filterGroupValikko,
                                            }));
                                            event.currentTarget.blur(); // to ':active'-pseudoclass
                                        }}
                                    >
                                        {t('suodata-nappi')}
                                    </button>
                                </div>
                            </div>
                        )}
                    </GuardedComponentWrapper>
                </div>

                <div className={styles['raporti-wrapper']}>
                    <div className={styles['main-heading-wrapper']}>
                        <img
                            src={i18n.language !== 'sv' ? karviLogo_fi : karviLogo_sv}
                            alt={t('karvi-logo-alt-text', {ns: 'yleiset'})}
                            height="75"
                        />
                        <button
                            type="button"
                            className="small"
                            onClick={() =>
                                downloadPdf(
                                    fetchRaporttiObservablePdf,
                                    pdfNameGenerator(),
                                )
                            }
                            disabled={!raportti?.kysymysryhmaid}
                        >
                            {t('lataa-pdf')}
                        </button>
                    </div>
                    {raportti?.nimi_en && raportti?.nimi_en?.trim().length > 0 && (
                        <VirkailijaUILanguageButtons
                            englishTopic={raportti?.nimi_en}
                            setLanguage={setLanguage}
                            selectedLanguage={language}
                        />
                    )}
                    <h2 className={styles['raportit-main-heading']}>
                        {raporttiBase && raporttiBase[raporttiName]?.toString()}
                    </h2>

                    <ViewIndicators
                        paaindikaattori={raportti?.metatiedot?.paaIndikaattori}
                        muutIndikaattorit={
                            raportti?.metatiedot?.sekondaariset_indikaattorit
                        }
                        language={language}
                    />

                    <h3>{raportti[koulutustoimijanNimi]?.toString()}</h3>

                    <p>{`${fixedT('tiedonkeruun-ajankohta')}: ${
                        raportti.created_date ??
                        fixedT('tilanvaraaja-ajankohta', {ns: 'raporttipohja'})
                    }`}</p>

                    {raportti.metatiedot?.lomaketyyppi !== undefined &&
                        !paakayttajaLomakkeet.includes(
                            raportti?.metatiedot?.lomaketyyppi as LomakeTyyppi,
                        ) && (
                            <p>
                                {`${fixedT('toimipaikkojen-maara')}: ${
                                    raportti.survey_oppilaitoses_answered_count
                                }/${raportti.survey_oppilaitoses_activated_count}`}
                            </p>
                        )}

                    <p>
                        {raportti &&
                            raportti.survey_participants_count >= nlimit &&
                            filterNimike === initialFilters.filterNimike &&
                            eligibilityChecked === initialFilters.eligibilityChecked &&
                            `${fixedT('vastausprosentti')}: ${
                                raportti.survey_participants_count
                            }/${raportti.survey_sent_count} (${round(
                                (raportti.survey_participants_count /
                                    raportti.survey_sent_count) *
                                    100,
                            )} %)`}
                    </p>

                    {!preview
                        ? raporttiBase?.reporting_template?.[helpText] && (
                              <p>
                                  {raporttiBase?.reporting_template[helpText] as string}
                              </p>
                          )
                        : descriptionPreview()}

                    <p>
                        <a
                            target="_blank"
                            href={fixedT('raportin-tulkinta-url')}
                            rel="noreferrer"
                        >
                            {fixedT('raportin-tulkinta')}
                            <LaunchIcon
                                sx={{
                                    blockSize: 16,
                                    marginRight: 1,
                                    verticalAlign: 'top',
                                }}
                            />
                        </a>
                    </p>

                    <ChartGroup
                        data={raporttiBase?.questions}
                        kysymysryhmaId={kysymysryhmaId}
                        nlimit={nlimit}
                        helptexts={raporttiBase?.reporting_template.template_helptexts}
                        preview={preview as boolean}
                        language={language}
                    />
                </div>

                <div className={styles['view-raportti-buttons']}>
                    <ButtonWithLink
                        linkTo={
                            !preview
                                ? '/raportointi'
                                : `/raportointipohja?id=${kysymysryhmaId}`
                        }
                        linkText={t('poistu', {ns: 'confirmation'})}
                    />
                    {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
                    <a className="button-alike" role="button" href="#">
                        {t('palaa-ylos')}
                    </a>
                </div>
            </div>
        )
    );
}

export default ViewRaportti;
