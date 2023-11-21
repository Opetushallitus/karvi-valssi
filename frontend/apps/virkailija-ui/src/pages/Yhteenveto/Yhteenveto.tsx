import {useTranslation} from 'react-i18next';
import {useLocation} from 'react-router-dom';
import {getQueryParamAsNumber} from '@cscfi/shared/utils/helpers';
import {
    raportiointipalveluGetSummary$,
    raportiointipalveluGetSummaryPdf$,
    raportiointipalveluPostSummary$,
    raportiointipalveluPutSummary$,
    SummaryType,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import karviLogo_fi from '@cscfi/shared/components/Navigaatio/KARVI_long_logo.png';
import karviLogo_sv from '@cscfi/shared/components/Navigaatio/NCU_long_logo.png';
import {forkJoin} from 'rxjs';
import {
    arvoGetKysely$,
    ArvoKysely,
    ArvoKysymysryhma,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {useContext, useEffect, useRef, useState} from 'react';
import {base64ToArrayBuffer} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {UserInfoType} from '@cscfi/shared/services/Login/Login-service';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import ViewIndicators, {
    strArrToindicatorArr,
    strToIndicator,
} from '../../components/ViewIndicators/ViewIndicators';
import UserContext from '../../Context';
import GenericForm, {GenericFormField} from '../../components/GenericForm/GenericForm';
import styles from '../Raportointi/raportit.module.css';

function createUpdateFunc(userInfo: UserInfoType, summaryId?: number) {
    return summaryId
        ? (body: SummaryType) =>
              raportiointipalveluPutSummary$(userInfo!)(summaryId, body)
        : raportiointipalveluPostSummary$(userInfo!);
}

type FormField = {
    name: string;
    isLarge: boolean;
};

const yhteenvetoFormFields: FormField[] = [
    {name: 'group_info', isLarge: false},
    {name: 'kuvaus', isLarge: true},
    {name: 'aineisto', isLarge: true},
    {name: 'vahvuudet', isLarge: true},
    {name: 'kohteet', isLarge: true},
    {name: 'keh_toimenpiteet', isLarge: true},
    {name: 'seur_toimenpiteet', isLarge: true},
];

const formMetadataProperties = (kyselyId: number) => ({
    kyselyid: kyselyId,
});

const publishProperties = (isPublish: boolean) => ({
    is_locked: isPublish,
});

function Yhteenveto() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['yhteenveto']);
    const userInfo = useContext(UserContext);
    const location = useLocation();
    const kyselyId = getQueryParamAsNumber(location, 'id');
    const [kysely, setKysely] = useState<ArvoKysely>();
    const [summary, setSummary] = useState<SummaryType>();
    const aRef = useRef<any | null>(null);

    const pdfNameGenerator = () => {
        const firstKysymysryhma = kysely!.kysymysryhmat.find((kr) => !!kr);
        const krNimiKey = `nimi_${lang}` as keyof ArvoKysymysryhma;
        const krNimi = firstKysymysryhma ? firstKysymysryhma[krNimiKey] : '';
        return `${t('yhteenveto')}_${krNimi}.pdf`;
    };

    const downloadPdf = () => {
        raportiointipalveluGetSummaryPdf$(userInfo!)(summary!.id!, lang).subscribe(
            (resp: string) => {
                const arrBuff = base64ToArrayBuffer(resp);
                const blob = new Blob([arrBuff], {type: 'application/pdf'});
                aRef.current.href = window.URL.createObjectURL(blob);
                aRef.current.download = pdfNameGenerator();
                aRef.current.click();
                return null;
            },
        );
    };

    useEffect(() => {
        const queries = forkJoin([
            raportiointipalveluGetSummary$(userInfo!)(kyselyId!),
            arvoGetKysely$(kyselyId!),
        ]);

        queries.subscribe(
            ([currentSummary, arvoKysely]: [
                currentSummary: SummaryType,
                kysely: ArvoKysely,
            ]) => {
                setSummary(currentSummary);
                setKysely(arvoKysely);
            },
        );
    }, [kyselyId, lang, location, userInfo]);

    const formData = (): GenericFormField[] =>
        yhteenvetoFormFields.map((field: FormField) => {
            const fieldKey = field.name as keyof SummaryType;
            return {
                name: field.name,
                title: t(`form-field-title-${field.name}`),
                value: (summary![fieldKey] as string) || '',
                isLargeTxtField: field.isLarge,
            };
        });

    return (
        <div className={styles['raporti-page-wrapper']}>
            <div className={styles['raporti-page-header-wrapper']}>
                <h1>{t(!summary?.is_locked ? 'sivun-otsikko' : 'yhteenveto')}</h1>
            </div>
            <div
                className={
                    styles[
                        !summary?.is_locked
                            ? 'raporti-wrapper-no-borders'
                            : 'raporti-wrapper'
                    ]
                }
            >
                <div className={styles['main-heading-wrapper']}>
                    <img
                        src={lang !== 'sv' ? karviLogo_fi : karviLogo_sv}
                        alt={t('karvi-logo-alt-text', {ns: 'yleiset'})}
                        height="75"
                    />
                    {summary?.is_locked && (
                        <button
                            type="button"
                            className="small"
                            onClick={downloadPdf}
                            disabled={!summary?.id}
                        >
                            {t('lataa-pdf')}
                        </button>
                    )}
                </div>
                <div className={styles['secondary-heading-wrapper']}>
                    {summary && (
                        <>
                            <h2>
                                {kysely
                                    ? (kysely[
                                          `nimi_${lang}` as keyof ArvoKysely
                                      ] as string)
                                    : ''}
                            </h2>

                            <ViewIndicators
                                paaindikaattori={strToIndicator(
                                    summary?.taustatiedot?.paaindikaattori,
                                )}
                                muutIndikaattorit={strArrToindicatorArr(
                                    summary?.taustatiedot?.sekondaariset_indikaattorit,
                                )}
                            />

                            <h3>
                                {summary.koulutustoimija_name &&
                                    summary.koulutustoimija_name[lang as keyof TextType]}
                            </h3>
                            {summary.is_locked && (
                                <h3>{`${t('otsikko')}: ${
                                    formData().find((fd) => fd.name === 'group_info')
                                        ?.value || '-'
                                }`}</h3>
                            )}
                        </>
                    )}
                </div>

                {summary && (
                    <div>
                        {summary.is_locked ? (
                            formData()
                                .filter((fd) => fd.name !== 'group_info')
                                .map((field) => (
                                    <div key={field.name}>
                                        <h3>{field.title}</h3>
                                        <div
                                            className={styles['result-textfield-wrapper']}
                                        >
                                            {field.value &&
                                                field.value
                                                    .split('\n')
                                                    .map((line) =>
                                                        line ? (
                                                            <p className="plaintext">
                                                                {line}
                                                            </p>
                                                        ) : (
                                                            <br />
                                                        ),
                                                    )}
                                        </div>
                                    </div>
                                ))
                        ) : (
                            <GenericForm
                                sourcePage="raportointi"
                                fields={formData()}
                                updateOrCreateFn={createUpdateFunc(
                                    userInfo!,
                                    summary?.id,
                                )}
                                translationNameSpace="yhteenveto"
                                formMetadata={formMetadataProperties(kyselyId!)}
                                publishFeature={publishProperties}
                            />
                        )}
                    </div>
                )}
            </div>
            <a ref={aRef} href="/#" style={{display: 'none'}}>
                {/* This element requires content */}
                Placeholder label
            </a>
        </div>
    );
}

export default Yhteenveto;
