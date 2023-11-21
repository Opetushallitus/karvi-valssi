import {SetStateAction, useContext, useEffect, useRef, useState} from 'react';
import {useLocation} from 'react-router-dom';
import {format, parse} from 'date-fns';
import {useTranslation} from 'react-i18next';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import DropDownField from '@cscfi/shared/components/DropDownField/DropDownField';
import {base64ToArrayBuffer} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {getQueryParam, getQueryParamAsNumber, round} from '@cscfi/shared/utils/helpers';
import karviLogo_fi from '@cscfi/shared/components/Navigaatio/KARVI_long_logo.png';
import karviLogo_sv from '@cscfi/shared/components/Navigaatio/NCU_long_logo.png';
import ChartGroup from '@cscfi/shared/components/ChartGroup/ChartGroup';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import {
    JobTitles,
    raportiointipalveluGetRaportti$,
    raportiointipalveluGetRaporttiPdf$,
    RaporttiType,
    ReportingBase,
    ReportingTemplate,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import KyselykertaValitsin from '../../components/KyselykertaValitsin/KyselykertaValitsin';
import UserContext from '../../Context';
import ViewIndicators from '../../components/ViewIndicators/ViewIndicators';
import LomakeTyyppi, {
    henkilostoLomakkeet,
    taydennyskoulutusLomakkeet,
} from '../../utils/LomakeTyypit';
import GuardedComponentWrapper, {
    ValssiUserLevel,
} from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import ButtonWithLink from '../../components/ButtonWithLink/ButtonWithLink';
import styles from './raportit.module.css';

const eligibilityCheckedInitial = false;
const filterNimikeInitial = '0';

interface RaporttipohjaPreview {
    main_description: TextType;
}

interface ViewRaporttiProps {
    preview?: boolean;
}

function ViewRaportti({preview = false}: ViewRaporttiProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['raportointi']);
    const userInfo = useContext(UserContext);
    const location = useLocation();
    const [raportti, setRaportti] = useState<RaporttiType | null>(null);

    const [eligibilityChecked, setEligibilityChecked] = useState<boolean>(
        eligibilityCheckedInitial,
    );
    const [filterNimike, setFilterNimike] = useState<string>(filterNimikeInitial);

    const [nimikeFilterUsed, setnimikeFilterUsed] = useState<boolean>(false);
    const [answerRatio, setAnswerRatio] = useState<number>(0);

    const kysymysryhmaId = getQueryParamAsNumber(location, 'raportti');
    const alkupvm = getQueryParam(location, 'alkupvm');
    const aRef = useRef<any | null>(null);
    const nlimit = 5; // represents the minimum number of participants for showing report data
    const downloadPdf = () => {
        raportiointipalveluGetRaporttiPdf$(userInfo!)(
            raportti!.kysymysryhmaid!,
            userInfo!.rooli.organisaatio,
            filterNimike,
            eligibilityChecked,
            alkupvm!,
            userInfo!.rooli.kayttooikeus,
            lang,
        ).subscribe((resp: string) => {
            const arrBuff = base64ToArrayBuffer(resp);
            const blob = new Blob([arrBuff], {type: 'application/pdf'});
            aRef.current.href = window.URL.createObjectURL(blob);
            const raporttiName = `nimi_${lang}` as keyof RaporttiType;
            aRef.current.download = `${t('raportti')}_${raportti![raporttiName]}.pdf`;
            aRef.current.click();
            return null;
        });
    };
    const fetchRaportti = () => {
        raportiointipalveluGetRaportti$(userInfo!)(
            kysymysryhmaId!,
            userInfo!.rooli.organisaatio,
            filterNimike,
            eligibilityChecked,
            alkupvm!,
            userInfo!.rooli.kayttooikeus,
        ).subscribe((raporttiVar: SetStateAction<RaporttiType | null>) => {
            setRaportti(raporttiVar);
        });
        setnimikeFilterUsed(filterNimike !== filterNimikeInitial || eligibilityChecked);
    };
    const clearSelections = () => {
        setFilterNimike(filterNimikeInitial);
        setEligibilityChecked(eligibilityCheckedInitial);
    };

    const lomaketyypit = [...henkilostoLomakkeet, ...taydennyskoulutusLomakkeet];
    useEffect(() => {
        raportiointipalveluGetRaportti$(userInfo!)(
            kysymysryhmaId!,
            userInfo!.rooli.organisaatio,
            filterNimikeInitial,
            eligibilityCheckedInitial,
            alkupvm!,
            userInfo!.rooli.kayttooikeus,
        ).subscribe((raporttiVar) => {
            setRaportti(raporttiVar);
        });
    }, [kysymysryhmaId, alkupvm, userInfo]);
    useEffect(() => {
        if (raportti) {
            setAnswerRatio(
                round(
                    (raportti.survey_participants_count / raportti.survey_sent_count) *
                        100,
                ),
            );
        }
    }, [raportti]);
    const raporttiBase = raportti?.reporting_base;

    const raporttiName = `nimi_${lang}` as keyof ReportingBase;
    const helpText = `description_${lang}` as keyof ReportingTemplate;
    const jobTitles = `job_titles_${lang}` as keyof RaporttiType;
    const translatedJobTitles = raportti?.[jobTitles] as Array<JobTitles>;
    const koulutustoimijanNimi = `koulutustoimija_nimi_${lang}` as keyof RaporttiType;
    if (translatedJobTitles && translatedJobTitles[0]?.job_title_code !== '0') {
        translatedJobTitles.unshift({
            job_title_code: '0',
            name: t('valitse'),
        });
    }

    const descriptionPreview = () => {
        const mainDescription = (
            JSON.parse(
                sessionStorage.getItem(`reportPreviewData_${kysymysryhmaId}`) || '{}',
            ) as RaporttipohjaPreview
        )?.main_description?.[lang as keyof TextType];
        return mainDescription ? <p>{mainDescription}</p> : null;
    };

    const defaultKk = (r: RaporttiType) => {
        if (r.created_date) {
            const parsedDate = parse(r.created_date, 'dd.MM.yyyy', new Date());
            return format(parsedDate, 'yyyy-MM-dd');
        }
        return undefined;
    };

    return (
        raportti && (
            <div className={styles['raporti-page-wrapper']}>
                <div className={styles['raporti-page-header-wrapper']}>
                    <h1>
                        {preview ? t('raporttipohjan-esikatselu') : t('raportin-katselu')}
                    </h1>
                </div>
                <div className={styles['raportti-options-wrapper']}>
                    <GuardedComponentWrapper
                        allowedValssiRoles={[ValssiUserLevel.PAAKAYTTAJA]}
                    >
                        {lomaketyypit.includes(
                            raportti?.metatiedot?.lomaketyyppi as LomakeTyyppi,
                        ) && (
                            <div>
                                <h2>{t('raportin-suodatus')}</h2>
                                <div className={styles['dropdown-wrapper']}>
                                    <DropDownField
                                        id="vastaajan-tehtavanimike"
                                        value={filterNimike}
                                        label={t('vastaajan-tehtavanimike')}
                                        options={translatedJobTitles?.map((option) => ({
                                            value: option.job_title_code,
                                            name: option.name,
                                        }))}
                                        onChange={setFilterNimike}
                                    />
                                </div>
                                <FormControlLabel
                                    label={t<string>('kelpoisuus-tehtavaan')}
                                    control={
                                        <Checkbox
                                            key="eligibility"
                                            checked={eligibilityChecked}
                                            onChange={() =>
                                                setEligibilityChecked(!eligibilityChecked)
                                            }
                                            name="eligibility"
                                        />
                                    }
                                />
                                <div>
                                    <button
                                        type="button"
                                        onClick={() => clearSelections()}
                                        className="secondary"
                                        disabled={
                                            !eligibilityChecked &&
                                            filterNimike === filterNimikeInitial
                                        }
                                    >
                                        {t('tyhjenna-valinnat-nappi')}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={(event) => {
                                            fetchRaportti();
                                            event.currentTarget.blur(); // to ':active'-pseudoclass
                                        }}
                                    >
                                        {t('suodata-nappi')}
                                    </button>
                                </div>
                            </div>
                        )}
                    </GuardedComponentWrapper>
                    <KyselykertaValitsin
                        kyselykertaStart={defaultKk(raportti)}
                        availableKyselykertas={raportti.available_kyselykertas}
                        sideEffects={[clearSelections]}
                    />
                </div>

                <div className={styles['raporti-wrapper']}>
                    <div className={styles['main-heading-wrapper']}>
                        <img
                            src={lang !== 'sv' ? karviLogo_fi : karviLogo_sv}
                            alt={t('karvi-logo-alt-text', {ns: 'yleiset'})}
                            height="75"
                        />

                        <button
                            type="button"
                            className="small"
                            onClick={downloadPdf}
                            disabled={!raportti?.kysymysryhmaid}
                        >
                            {t('lataa-pdf')}
                        </button>
                    </div>
                    <h2 className={styles['raportit-main-heading']}>
                        {raporttiBase && raporttiBase[raporttiName]?.toString()}
                    </h2>
                    <ViewIndicators
                        paaindikaattori={raportti?.metatiedot?.paaIndikaattori}
                        muutIndikaattorit={
                            raportti?.metatiedot?.sekondaariset_indikaattorit
                        }
                    />
                    <h3>{raportti[koulutustoimijanNimi]?.toString()}</h3>
                    <p>{`${t('tiedonkeruun-ajankohta')}: ${
                        raportti.created_date ||
                        t('tilanvaraaja-ajankohta', {ns: 'raporttipohja'})
                    }`}</p>
                    <p>
                        {raportti &&
                            raportti.survey_participants_count >= nlimit &&
                            !nimikeFilterUsed &&
                            `${t('vastausprosentti')}: ${
                                raportti.survey_participants_count
                            }/${raportti.survey_sent_count} (${answerRatio} %)`}
                    </p>
                    {!preview
                        ? raporttiBase?.reporting_template?.[helpText] && (
                              <p>{raporttiBase.reporting_template[helpText] as string}</p>
                          )
                        : descriptionPreview()}
                    <p>
                        {lang === 'fi' && (
                            <a
                                target="_blank"
                                href="https://wiki.eduuni.fi/pages/viewpage.action?pageId=249542063#Valssink%C3%A4ytt%C3%B6ohjeet-Raportintulkinta" // eslint-disable-line
                                rel="noreferrer"
                            >
                                {t('raportin-tulkinta')}
                            </a>
                        )}
                        {lang === 'sv' && (
                            <a
                                target="_blank"
                                href="https://wiki.eduuni.fi/pages/viewpage.action?pageId=348984426#Bruksanvisningf%C3%B6rValssi-Tolkningavrapporten" // eslint-disable-line
                                rel="noreferrer"
                            >
                                {t('raportin-tulkinta')}
                            </a>
                        )}
                    </p>
                    <ChartGroup
                        data={raporttiBase?.questions}
                        kysymysryhmaId={kysymysryhmaId}
                        nlimit={nlimit}
                        helptexts={raporttiBase?.reporting_template.template_helptexts}
                        preview={preview}
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

                <a ref={aRef} href="/#" style={{display: 'none'}}>
                    {/* This element requires content */}
                    Placeholder label
                </a>
            </div>
        )
    );
}

export default ViewRaportti;
