import {useContext, useEffect, useRef, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {useObservable} from 'rxjs-hooks';
import {useLocation} from 'react-router-dom';
import {
    getQueryParam,
    getQueryParamAsNumber,
    uniqueNumber,
} from '@cscfi/shared/utils/helpers';
import {
    raportiointipalveluGetKyselykerrat,
    raportiointipalveluGetResult$,
    raportiointipalveluGetResultPdf$,
    raportiointipalveluPostResult$,
    raportiointipalveluPutResult$,
    SummaryType,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import karviLogo_fi from '@cscfi/shared/components/Navigaatio/KARVI_long_logo.png';
import karviLogo_sv from '@cscfi/shared/components/Navigaatio/NCU_long_logo.png';
import {base64ToArrayBuffer} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {UserInfoType} from '@cscfi/shared/services/Login/Login-service';
import ViewIndicators, {
    strArrToindicatorArr,
    strToIndicator,
} from '../../components/ViewIndicators/ViewIndicators';
import KyselykertaValitsin, {
    ValitsinTyyppi,
} from '../../components/KyselykertaValitsin/KyselykertaValitsin';
import GenericForm, {GenericFormField} from '../../components/GenericForm/GenericForm';
import UserContext from '../../Context';
import styles from '../Raportointi/raportit.module.css';

function createUpdateFunc(userInfo: UserInfoType, summaryId?: number) {
    return summaryId
        ? (body: SummaryType) => raportiointipalveluPutResult$(userInfo!)(summaryId, body)
        : raportiointipalveluPostResult$(userInfo!);
}

type FormField = {
    name: string;
    isLarge: boolean;
};

const arviointituloksetFormFields: FormField[] = [
    {name: 'kuvaus', isLarge: true},
    {name: 'aineisto', isLarge: true},
    {name: 'vahvuudet', isLarge: true},
    {name: 'kohteet', isLarge: true},
    {name: 'keh_toimenpiteet', isLarge: true},
    {name: 'seur_toimenpiteet', isLarge: true},
];

const formMetadataProperties = (
    kysymysryhmaId: number,
    koulutustoimijaOid: string,
    kyselykertaAlkupvm: string,
) => ({
    kysymysryhmaid: kysymysryhmaId,
    koulutustoimija: koulutustoimijaOid,
    kysely_voimassa_alkupvm: kyselykertaAlkupvm,
});

const publishProperties = (isPublish: boolean) => ({
    is_locked: isPublish,
});

function Arviointitulokset() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['arviointitulokset']);
    const userInfo = useContext(UserContext);
    const location = useLocation();
    const kysymysryhmaId = getQueryParamAsNumber(location, 'id');
    const koulutustoimijaOid = getQueryParam(location, 'koulutustoimija_oid');
    const kyselykertaAlkupvm = getQueryParam(location, 'alkupvm');

    const [result, setResult] = useState<SummaryType>();
    // Change of kyselykertaAlkupvm needs to trigger reload
    useEffect(() => {
        raportiointipalveluGetResult$(userInfo!)(
            kysymysryhmaId!,
            koulutustoimijaOid!,
            kyselykertaAlkupvm!,
        ).subscribe((res) => {
            setResult(res);
        });
    }, [kysymysryhmaId, koulutustoimijaOid, kyselykertaAlkupvm, userInfo]);

    const kyselykertas = useObservable(
        () =>
            raportiointipalveluGetKyselykerrat(userInfo!)(
                kysymysryhmaId!,
                koulutustoimijaOid!,
                kyselykertaAlkupvm!,
            ),
        [],
    );

    const aRef = useRef<any | null>(null);

    const pdfNameGenerator = () => {
        const kysymysryhma = result!.taustatiedot!.kysymysryhma_name;
        const krNimi = kysymysryhma ? kysymysryhma[lang as keyof TextType] : '';
        return `${t('arviointitulokset')}_${krNimi}.pdf`;
    };

    const downloadPdf = () => {
        raportiointipalveluGetResultPdf$(userInfo!)(result!.id!, lang).subscribe(
            (resp: string) => {
                const arrBuff = base64ToArrayBuffer(resp);
                const blob = new Blob([arrBuff], {type: 'application/pdf'});
                aRef.current.href = window.URL.createObjectURL(blob);
                aRef.current.download = `${pdfNameGenerator()}.pdf`;
                aRef.current.click();
                return null;
            },
        );
    };

    const formData = (): GenericFormField[] =>
        arviointituloksetFormFields.map((field: FormField) => {
            const fieldKey = field.name as keyof SummaryType;
            return {
                name: field.name,
                title: t(`form-field-title-${field.name}`),
                value: (result![fieldKey] as string) || '',
                isLargeTxtField: field.isLarge,
            };
        });

    return (
        <div className={styles['raporti-page-wrapper']}>
            <div className={styles['raporti-page-header-wrapper']}>
                <h1>
                    {t(
                        !result?.is_locked
                            ? 'tayta-arviointitulokset'
                            : 'arviointitulokset',
                    )}
                </h1>
            </div>
            <div className={styles['raportti-options-wrapper']}>
                <KyselykertaValitsin
                    kyselykertaStart={result?.kysely_voimassa_alkupvm}
                    availableKyselykertas={kyselykertas}
                    tyyppi={ValitsinTyyppi.arviointutulos}
                />
            </div>
            <div
                className={
                    styles[
                        !result?.is_locked
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
                    {result?.is_locked && (
                        <button
                            type="button"
                            className="small"
                            onClick={downloadPdf}
                            disabled={!result?.id}
                        >
                            {t('lataa-pdf')}
                        </button>
                    )}
                </div>
                <div className={styles['secondary-heading-wrapper']}>
                    {result?.is_locked && (
                        <>
                            <h2>
                                {
                                    result?.taustatiedot?.kysymysryhma_name[
                                        lang as keyof TextType
                                    ]
                                }
                            </h2>

                            <ViewIndicators
                                paaindikaattori={strToIndicator(
                                    result?.taustatiedot?.paaindikaattori,
                                )}
                                muutIndikaattorit={strArrToindicatorArr(
                                    result?.taustatiedot?.sekondaariset_indikaattorit,
                                )}
                            />

                            <h3>
                                {result?.koulutustoimija_name &&
                                    result?.koulutustoimija_name[lang as keyof TextType]}
                            </h3>
                            <h3>{t('esikatselu-otsikko')}</h3>
                        </>
                    )}
                </div>

                {result && (
                    <div>
                        {result.is_locked ? (
                            formData().map((field) => (
                                <div key={field.name}>
                                    <h3>{field.title}</h3>
                                    <div className={styles['result-textfield-wrapper']}>
                                        {field.value &&
                                            field.value.split('\n').map((line) =>
                                                line ? (
                                                    <p
                                                        key={`line_${uniqueNumber()}`}
                                                        className="plaintext"
                                                    >
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
                                updateOrCreateFn={createUpdateFunc(userInfo!, result?.id)}
                                translationNameSpace="arviointitulokset"
                                formMetadata={formMetadataProperties(
                                    kysymysryhmaId!,
                                    koulutustoimijaOid!,
                                    kyselykertaAlkupvm!,
                                )}
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

export default Arviointitulokset;
