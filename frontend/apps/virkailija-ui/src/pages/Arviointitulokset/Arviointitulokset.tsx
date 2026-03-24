import {useContext, useEffect, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {useObservableState} from 'observable-hooks';
import {useLocation} from 'react-router-dom';
import {
    getQueryParam,
    getQueryParamAsNumber,
    uniqueNumber,
    downloadPdf,
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
import {ArvoRoles, UserInfoType} from '@cscfi/shared/services/Login/Login-service';
import {of} from 'rxjs';
import ViewIndicators, {
    strArrToindicatorArr,
    strToIndicator,
} from '@cscfi/shared/components/ViewIndicators/ViewIndicators';
import {MaxLengths} from '@cscfi/shared/utils/validators';
import KyselykertaValitsin, {
    ValitsinTyyppi,
} from '../../components/KyselykertaValitsin/KyselykertaValitsin';
import GenericForm, {GenericFormField} from '../../components/GenericForm/GenericForm';
import UserContext from '../../Context';
import styles from '../Raportointi/raportit.module.css';
import GuardedComponentWrapper from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';

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
    const oppilaitosOid = getQueryParam(location, 'oppilaitos') || undefined;

    const [result, setResult] = useState<SummaryType>();
    // Change of kyselykertaAlkupvm needs to trigger reload
    useEffect(() => {
        raportiointipalveluGetResult$(userInfo!)(
            kysymysryhmaId!,
            koulutustoimijaOid!,
            kyselykertaAlkupvm!,
            oppilaitosOid,
        ).subscribe((res) => {
            setResult(res);
        });
    }, [kysymysryhmaId, koulutustoimijaOid, kyselykertaAlkupvm, userInfo, oppilaitosOid]);

    const [kyselykertas] = useObservableState(
        () =>
            userInfo?.arvoAktiivinenRooli.kayttooikeus === ArvoRoles.PAAKAYTTAJA
                ? raportiointipalveluGetKyselykerrat(userInfo)(
                      kysymysryhmaId!,
                      koulutustoimijaOid!,
                      kyselykertaAlkupvm!,
                  )
                : of(null),
        [],
    );

    const pdfNameGenerator = () => {
        const kysymysryhma = result!.taustatiedot!.kysymysryhma_name;
        const krNimi = kysymysryhma ? kysymysryhma[lang as keyof TextType] : '';
        return `${t('arviointitulokset')}_${krNimi}.pdf`;
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
                <GuardedComponentWrapper roles={{arvo: [ArvoRoles.PAAKAYTTAJA]}}>
                    <KyselykertaValitsin
                        kyselykertaStart={result?.kysely_voimassa_alkupvm}
                        availableKyselykertas={kyselykertas!}
                        tyyppi={ValitsinTyyppi.arviointutulos}
                    />
                </GuardedComponentWrapper>
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
                            onClick={() =>
                                downloadPdf(
                                    raportiointipalveluGetResultPdf$(userInfo!)(
                                        result!.id!,
                                        oppilaitosOid,
                                        lang,
                                    ),
                                    pdfNameGenerator(),
                                )
                            }
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
                                maxInputLength={MaxLengths.resultField}
                            />
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default Arviointitulokset;
