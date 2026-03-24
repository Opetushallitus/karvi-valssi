import {useContext, useEffect, useMemo, useState} from 'react';
import {useObservableState} from 'observable-hooks';
import {useTranslation} from 'react-i18next';
import {useLocation} from 'react-router-dom';
import {
    getQueryParam,
    getQueryParamAsNumber,
    uniqueNumber,
    downloadCsv,
    downloadPdf,
} from '@cscfi/shared/utils/helpers';
import {
    raportiointipalveluGetSummaryList$,
    raportiointipalveluGetSummaryPdf$,
    raportiointipalveluGetSummaryCsv$,
    raportiointipalveluGetKyselykerrat,
    SummaryType,
} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import karviLogo_fi from '@cscfi/shared/components/Navigaatio/KARVI_long_logo.png';
import karviLogo_sv from '@cscfi/shared/components/Navigaatio/NCU_long_logo.png';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import ViewIndicators, {
    strArrToindicatorArr,
    strToIndicator,
} from '@cscfi/shared/components/ViewIndicators/ViewIndicators';
import KyselykertaValitsin, {
    ValitsinTyyppi,
} from '../../components/KyselykertaValitsin/KyselykertaValitsin';
import UserContext from '../../Context';
import {GenericFormField} from '../../components/GenericForm/GenericForm';
import styles from '../Raportointi/raportit.module.css';

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

function YhteenvetoList() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['yhteenveto']);
    const userInfo = useContext(UserContext);
    const langKey = lang as keyof TextType;
    const location = useLocation();
    const kysymysryhmaId = getQueryParamAsNumber(location, 'id');
    const koulutustoimijaOid = getQueryParam(location, 'koulutustoimija_oid');
    const alkupvm = getQueryParam(location, 'alkupvm');

    // Käyttäjän klikkauksella valittu summary (saa jäädä tilaan)
    const [summary, setSummary] = useState<SummaryType>();

    // Lista noudetaan palvelusta
    const [summaryList, setSummaryList] = useState<SummaryType[]>([]);

    // Change of alkupvm needs to trigger reload
    useEffect(() => {
        raportiointipalveluGetSummaryList$(userInfo!)(
            kysymysryhmaId!,
            koulutustoimijaOid!,
            alkupvm!,
        ).subscribe((summaires) => {
            setSummaryList(summaires);
        });
    }, [kysymysryhmaId, koulutustoimijaOid, alkupvm, userInfo]);

    const [kyselykertas] = useObservableState(
        () =>
            raportiointipalveluGetKyselykerrat(userInfo!)(
                kysymysryhmaId!,
                koulutustoimijaOid!,
                alkupvm!,
            ),
        [],
    );

    // Johdettu oletus: jos käyttäjä ei ole valinnut mitään (summary on tyhjä),
    // näytetään listan ensimmäinen olemassa oleva item.
    const selectedSummary = useMemo(
        () => summary ?? summaryList.find(Boolean),
        [summary, summaryList],
    );

    // Tiedostonimen muodostus (käyttää selectedSummarya)
    const fileNameGenerator = (filetype: string) => {
        const kysymysryhmaName = selectedSummary?.taustatiedot?.kysymysryhma_name;
        const krNimi = kysymysryhmaName ? kysymysryhmaName[langKey] : '';
        return `${t('yhteenveto')}_${krNimi}.${filetype}`;
    };

    const formData = (): GenericFormField[] =>
        yhteenvetoFormFields.map((field: FormField) => {
            const fieldKey = field.name as keyof SummaryType;
            return {
                name: field.name,
                title: t(`form-field-title-${field.name}`),
                value: (selectedSummary?.[fieldKey] as string) ?? '',
                isLargeTxtField: field.isLarge,
            };
        });

    return (
        <div className={styles['raporti-page-wrapper']}>
            <div className={styles['raporti-page-header-wrapper']}>
                <h1>{t('yhteenveto')}</h1>
            </div>

            <div className={styles['raportti-options-wrapper']}>
                <KyselykertaValitsin
                    kyselykertaStart={selectedSummary?.kysely_voimassa_alkupvm}
                    availableKyselykertas={kyselykertas}
                    tyyppi={ValitsinTyyppi.yhteenveto}
                />
            </div>

            <div className={styles['raporti-page-content-wrapper']}>
                <div className={styles['raportti-navigation-wrapper']}>
                    <button
                        type="button"
                        className="small"
                        onClick={() =>
                            downloadCsv(
                                raportiointipalveluGetSummaryCsv$(userInfo!)(
                                    kysymysryhmaId!,
                                    koulutustoimijaOid!,
                                    alkupvm!,
                                ),
                                fileNameGenerator('csv'),
                            )
                        }
                        disabled={!selectedSummary?.id}
                    >
                        {t('lataa-csv')}
                    </button>

                    <label htmlFor="raport-navigation" className="label-for-inputfield">
                        {t('valitse-toimipaikka')}
                    </label>

                    <ul id="raport-navigation" className={styles['raport-navigation']}>
                        {summaryList.map((s) =>
                            selectedSummary?.id?.toString() !== s?.id?.toString() ? (
                                <li key={s.id}>
                                    {/* pitkät toimipakan nimet voivat rikkoa sivun asettelun jos käytetään
                      buttonia (se ei rivity), siksi span/onclick */}
                                    {/* eslint-disable-next-line max-len */}
                                    {/* eslint-disable-next-line jsx-a11y/no-static-element-interactions,jsx-a11y/click-events-have-key-events */}
                                    <span
                                        className="link-alike"
                                        onClick={() => {
                                            setSummary(
                                                summaryList.find(
                                                    (slitem) =>
                                                        slitem.id!.toString() ===
                                                        s?.id?.toString(),
                                                ),
                                            );
                                        }}
                                    >
                                        {s.group_info}
                                    </span>
                                </li>
                            ) : (
                                <li key={s.id}>
                                    <span className={styles['no-link']}>
                                        {s.group_info}
                                    </span>
                                </li>
                            ),
                        )}
                    </ul>
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
                            onClick={() =>
                                downloadPdf(
                                    raportiointipalveluGetSummaryPdf$(userInfo!)(
                                        selectedSummary!.id!,
                                        lang,
                                    ),
                                    fileNameGenerator('pdf'),
                                )
                            }
                            disabled={!selectedSummary?.id}
                        >
                            {t('lataa-pdf')}
                        </button>
                    </div>

                    <div className={styles['secondary-heading-wrapper']}>
                        {selectedSummary && (
                            <>
                                <h2>
                                    {selectedSummary?.taustatiedot?.kysymysryhma_name[
                                        langKey
                                    ] ?? ''}
                                </h2>

                                <ViewIndicators
                                    paaindikaattori={strToIndicator(
                                        selectedSummary?.taustatiedot?.paaindikaattori,
                                    )}
                                    muutIndikaattorit={strArrToindicatorArr(
                                        selectedSummary?.taustatiedot
                                            ?.sekondaariset_indikaattorit,
                                    )}
                                />

                                <h3>
                                    {selectedSummary?.koulutustoimija_name &&
                                        selectedSummary.koulutustoimija_name[
                                            lang as keyof TextType
                                        ]}
                                </h3>

                                <h3>{`${t('otsikko')}: ${
                                    formData().find((fd) => fd.name === 'group_info')
                                        ?.value ?? '-'
                                }`}</h3>
                            </>
                        )}
                    </div>

                    {selectedSummary && (
                        <div>
                            {formData()
                                .filter((fd) => fd.name !== 'group_info')
                                .map((field) => (
                                    <div key={field.name}>
                                        <h3>{field.title}</h3>
                                        <div
                                            className={styles['result-textfield-wrapper']}
                                        >
                                            {field.value &&
                                                field.value.split('\n').map((line) =>
                                                    line ? (
                                                        <p
                                                            key={`${field.name}_${uniqueNumber()}`}
                                                            className="plaintext"
                                                        >
                                                            {line}
                                                        </p>
                                                    ) : (
                                                        <br
                                                            key={`${field.name}_${uniqueNumber()}`}
                                                        />
                                                    ),
                                                )}
                                        </div>
                                    </div>
                                ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default YhteenvetoList;
