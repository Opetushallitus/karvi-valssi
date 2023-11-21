import {
    ArvoKysymys,
    convertKysymyksetArvoToValssi,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {map} from 'rxjs/operators';
import {KysymysType, TextType} from '@cscfi/shared/services/Data/Data-service';
import {notEmpty} from '@cscfi/shared/utils/helpers';
import {UserInfoType} from '../Login/Login-service';
import {raportointipalveluHttpImpersonation} from '../Http/Http-service';
import {raportointipalveluHostname} from '../Settings/Settings-service';

const raportointipalveluApiBase = `${raportointipalveluHostname}api/v1/`;

export type KyselyStatisticsType = {
    answer_pct: number;
    answered_count: number;
    sent_count: number;
    in_use_count: number;
    extra_data: KyselyExtraDataType | undefined;
};
export type MainIndicatorType = {
    group: number;
    key: string;
};
export type IndicatorsType = {
    main_indicator: MainIndicatorType;
};
export type KyselyExtraDataType = {
    kysely_not_sent: Array<KyselyNotSentType> | any;
    answer_pct_lt_50: Array<Answer50Type> | any;
};
export type Answer50Type = {
    answer_pct: number;
    nimi_fi: string;
    nimi_sv: string;
};
export type KyselyNotSentType = {
    nimi_fi: string;
    nimi_sv: string;
};
export type VastaajaStatisticsType = {
    sent_count: number;
    answered_count: number;
    answer_pct: number;
};
export type KoulutustoimijaStatisticsType = {
    in_use_count: number;
    sent_count: number;
    extra_data: KysymysryhmaExtraDataType;
};

export type OppilaitosStatisticsType = {
    in_use_count: number;
    sent_count: number;
};

export type KysymysryhmaExtraDataType = {
    koulutustoimija_names: TextType;
};

export type ReportingTemplateHelpText = {
    id?: number;
    question_id: number;
    title_fi: string;
    title_sv: string;
    description_fi: string;
    description_sv: string;
};

export type ReportingTemplate = {
    id?: number;
    kysymysryhmaid: number;
    title_fi: string;
    title_sv: string;
    description_fi: string;
    description_sv: string;
    template_helptexts: Array<ReportingTemplateHelpText>;
};
export type JobTitles = {
    name: string;
    job_title_code: string;
};
export type ReportingBase = {
    kysymysryhmaid: number;
    kyselykertaid?: number;
    nimi_fi: string;
    nimi_sv: string;
    reporting_template: ReportingTemplate;
    questions: Array<KysymysType>;
    job_titles_fi: Array<JobTitles>;
    job_titles_sv: Array<JobTitles>;
};
export type KyselyCollectionType = {
    indicators: IndicatorsType;
    kyselyid: number;
    nimi_en?: string;
    nimi_fi?: string;
    nimi_sv?: string;
    statistics?: KyselyStatisticsType;
    voimassa_alkupvm: string;
    voimassa_loppupvm: string;
    is_closed: boolean;
    latest_answer_date?: null;
    toimipaikka_statistics?: KyselyStatisticsType;
    vastaaja_statistics?: VastaajaStatisticsType;
    lomaketyyppi: string;
};
export type KysymysryhmaCollectionType = {
    kysymysryhmaid: number;
    nimi_fi: string;
    nimi_sv?: string;
    nimi_en?: string;
    lomaketyyppi: string;
    released_date: string;
    earliest_usage_date: string;
    latest_ending_date: string;
    indicators: Indikaattori;
    koulutustoimija_statistics: KoulutustoimijaStatisticsType;
    oppilaitos_statistics: OppilaitosStatisticsType;
    vastaaja_statistics: VastaajaStatisticsType;
};

export type RaportitKyselyType = {
    kyselyid: number;
    metatiedot: {
        esikatselu_tunniste: string;
        valssi_kysymysryhma: number;
        valssi_saate: string;
    };
    nimi_fi: string;
    nimi_sv: string;
    voimassa_alkupvm: string;
    voimassa_loppupvm: string;
};

export type RaportitKyselykertaType = {
    display_report: boolean;
    kysely: RaportitKyselyType;
    kyselykertaid: number;
    nimi: string;
    voimassa_alkupvm: string;
    voimassa_loppupvm: string;
    show_summary: boolean;
};

export type AvailableKyselykertaType = {
    display_report: boolean;
    kyselykerta_alkupvm: string;
    nimi_fi: string;
    nimi_sv: string;
    show_summary: boolean;
    show_result: boolean;
};

export type RaportitType = {
    display_report: boolean;
    fill_summary: boolean;
    kysymysryhmaid: number;
    kysymysryhma_nimi_fi?: string;
    kysymysryhma_nimi_sv?: string;
    nimi_fi?: string;
    nimi_sv?: string;
    voimassa_alkupvm: string;
    voimassa_loppupvm: string;
    kyselykertas: RaportitKyselykertaType[];
    available_kyselykertas: AvailableKyselykertaType[];
    koulutustoimija_oid?: string;
};
export type AvailableKyselykertas = {
    kyselykerta_alkupvm: string;
    nimi_fi: string;
    nimi_sv: string;
    display_report: boolean;
    show_result: boolean;
    show_summary: boolean;
};

export type Indikaattori = {
    key: string;
    group?: number;
};

export type MetatiedotType = {
    lomaketyyppi: string;
    paaIndikaattori: Indikaattori;
    sekondaariset_indikaattorit: Array<Indikaattori>;
};
export type RaporttiType = {
    reporting_base?: ReportingBase;
    created_date?: string;
    job_titles_fi?: Array<JobTitles>;
    job_titles_sv?: Array<JobTitles>;
    koulutustoimija_nimi_fi: string;
    koulutustoimija_nimi_sv: string;
    kysymysryhmaid?: number;
    nimi_fi?: string;
    nimi_sv?: string;
    survey_participants_count: number;
    survey_sent_count: number;
    available_kyselykertas?: Array<AvailableKyselykertas>;
    metatiedot?: MetatiedotType;
};

export type SummaryType = {
    oppilaitos?: string;
    taustatiedot?: {
        koulutustoimija: string;
        paaindikaattori: string;
        sekondaariset_indikaattorit: string[];
        kysymysryhma_name: TextType;
    };
    /* form metadata */
    kyselyId: number;
    id?: number;
    is_locked?: boolean;
    koulutustoimija_name?: TextType;
    kysely_voimassa_alkupvm: string;
    /* form fields */
    group_info: string;
    kuvaus: string;
    aineisto: string;
    vahvuudet: string;
    kohteet: string;
    keh_toimenpiteet: string;
    seur_toimenpiteet: string;
};

/**
 * Summary Pdf
 * @param kyselyId
 * @param locale
 */
export const raportiointipalveluGetSummaryPdf$ =
    (user: UserInfoType) =>
    (kyselyId: number, language = 'fi') =>
        raportointipalveluHttpImpersonation(user).get<string>(
            `${raportointipalveluApiBase}summary/${kyselyId}/pdf/?language=${language}&base64=true`,
        );

/**
 * Summary CSV
 * @param kysymysryhmaId
 * @param koulutustoimijaOid
 * @param alkupvm
 */
export const raportiointipalveluGetSummaryCsv$ =
    (user: UserInfoType) =>
    (kysymysryhmaId: number, koulutustoimijaOid: string, alkupvm: string) =>
        raportointipalveluHttpImpersonation(user).get<string>(
            // eslint-disable-next-line max-len
            `${raportointipalveluApiBase}summary/csv/kysymysryhmaid=${kysymysryhmaId}/koulutustoimija=${koulutustoimijaOid}/alkupvm=${alkupvm}/?base64=false`,
        );

/**
 * Get Summary List
 * @param kysymysryhmaId
 * @param koulutustoimijaOid
 * @param alkupvm
 */
export const raportiointipalveluGetSummaryList$ =
    (user: UserInfoType) =>
    (kysymysryhmaId: number, koulutustoimijaOid: string, alkupvm: string) =>
        raportointipalveluHttpImpersonation(user).get<SummaryType[]>(
            // eslint-disable-next-line max-len
            `${raportointipalveluApiBase}summary/list/kysymysryhmaid=${kysymysryhmaId}/alkupvm=${alkupvm}/koulutustoimija=${koulutustoimijaOid}/`,
        );

/**
 * Get Summary
 * @param kyselyId
 */
export const raportiointipalveluGetSummary$ =
    (user: UserInfoType) => (kyselyId: number) =>
        raportointipalveluHttpImpersonation(user).get<SummaryType>(
            `${raportointipalveluApiBase}summary/kyselyid=${kyselyId}/`,
        );

/**
 * Create summary
 * @param body
 */
export const raportiointipalveluPostSummary$ =
    (user: UserInfoType) => (body: SummaryType) =>
        raportointipalveluHttpImpersonation(user).post<SummaryType>(
            `${raportointipalveluApiBase}summary/`,
            body,
        );

/**
 * Update Result
 * @param body
 * @param id
 */
export const raportiointipalveluPutResult$ =
    (user: UserInfoType) => (resultId: number, body: SummaryType) =>
        raportointipalveluHttpImpersonation(user).put<SummaryType>(
            `${raportointipalveluApiBase}result/${resultId}/`,
            body,
        );

/**
 * Result Pdf
 * @param kyselyId
 * @param locale
 */
export const raportiointipalveluGetResultPdf$ =
    (user: UserInfoType) =>
    (resultId: number, language = 'fi') =>
        raportointipalveluHttpImpersonation(user).get<string>(
            `${raportointipalveluApiBase}result/${resultId}/pdf/?language=${language}&base64=true`,
        );

/**
 * Get Result
 * @param kysymysryhmaId
 * @param koulutustoimijaOid
 * @param alkupvm
 */
export const raportiointipalveluGetResult$ =
    (user: UserInfoType) =>
    (kysymysryhmaId: number, koulutustoimijaOid: string, alkupvm: string) =>
        raportointipalveluHttpImpersonation(user).get<SummaryType>(
            `${raportointipalveluApiBase}result/kysymysryhmaid=${kysymysryhmaId}/koulutustoimija=${koulutustoimijaOid}/alkupvm=${alkupvm}/`,
        );

/**
 * Create Result
 * @param body
 */
export const raportiointipalveluPostResult$ =
    (user: UserInfoType) => (body: SummaryType) =>
        raportointipalveluHttpImpersonation(user).post<SummaryType>(
            `${raportointipalveluApiBase}result/`,
            body,
        );

/**
 * Update Result
 * @param body
 * @param id
 */
export const raportiointipalveluPutSummary$ =
    (user: UserInfoType) => (id: number, body: SummaryType) =>
        raportointipalveluHttpImpersonation(user).put<SummaryType>(
            `${raportointipalveluApiBase}summary/${id}/`,
            body,
        );

/**
 * Get existing reporting template
 * @param kysymysryhmaId
 */
export const raportiointipalveluGetReportingBase$ =
    (user: UserInfoType) => (kysymysryhmaId: number) =>
        raportointipalveluHttpImpersonation(user)
            .get<ReportingBase>(
                `${raportointipalveluApiBase}reporting-base/${kysymysryhmaId}/`,
            )
            .pipe(
                map(
                    (rb: ReportingBase) =>
                        ({
                            ...rb,
                            questions: convertKysymyksetArvoToValssi(
                                rb.questions as any as ArvoKysymys[],
                            ).sort((qa, qb) => (qa?.order || 0) - (qb?.order || 0)),
                        }) as ReportingBase,
                ),
            );

/**
 * Put update existing reporting template
 * @param kysymysryhmaId
 * @param body
 */
export const raportiointipalveluPutReportingTemplate$ =
    (user: UserInfoType) => (reportingTemplateId: number, body: ReportingTemplate) =>
        raportointipalveluHttpImpersonation(user).put<ReportingTemplate>(
            `${raportointipalveluApiBase}reporting-template/${reportingTemplateId}/`,
            body,
        );

/**
 * Post new reporting template
 * @param body
 */
export const raportiointipalveluPostReportingTemplate$ =
    (user: UserInfoType) => (body: ReportingTemplate) =>
        raportointipalveluHttpImpersonation(user).post<ReportingTemplate>(
            `${raportointipalveluApiBase}reporting-template/`,
            body,
        );

const queryParameters = (
    jobTitle: string | null,
    eligibility: boolean | null,
    alkupvm: string | null,
    language: string | null,
    base64: boolean | null,
    koulutustoimija: string | null,
    rooli: string | null,
) =>
    [
        jobTitle !== '0' && jobTitle ? `job_title_code=${jobTitle}` : null,
        eligibility ? `eligibility=${eligibility}` : null,
        alkupvm ? `kyselykerta_alkupvm=${alkupvm}` : null,
        language ? `language=${language}` : null,
        base64 ? `base64=true` : null,
        koulutustoimija ? `koulutustoimija=${koulutustoimija}` : null,
        rooli ? `role=${rooli}` : null,
    ]
        .filter(notEmpty)
        .join('&');

/**
 * Get kyselykertas
 */
export const raportiointipalveluGetKyselykerrat =
    (user: UserInfoType) =>
    (kysymysryhmaid: number, koulutustoimija: string, alkupvm: string) =>
        raportointipalveluHttpImpersonation(user).get<Array<AvailableKyselykertas>>(
            // eslint-disable-next-line max-len
            `${raportointipalveluApiBase}available-kyselykertas/kysymysryhmaid=${kysymysryhmaid}/koulutustoimija=${koulutustoimija}/?${queryParameters(
                null,
                null,
                alkupvm,
                null,
                null,
                null,
                null,
            )}`,
        );

/**
 * Get Raportit
 * @param koulutustoimija (organisaatio)
 * @param role (rooli)
 */
export const raportiointipalveluGetRaportit$ =
    (user: UserInfoType) => (koulutustoimija: string, rooli: string) =>
        raportointipalveluHttpImpersonation(user).get<Array<RaportitType>>(
            `${raportointipalveluApiBase}closed-surveys/koulutustoimija=${koulutustoimija}/?${queryParameters(
                null,
                null,
                null,
                null,
                null,
                null,
                rooli,
            )}`,
        );

/**
 * Get Data collection
 * @param role (rooli)
 */
export const raportiointipalveluGetKyselyDataCollection$ =
    (user: UserInfoType) =>
    (rooli: string, koulutustoimija: string | null = null) =>
        raportointipalveluHttpImpersonation(user).get<Array<KyselyCollectionType>>(
            `${raportointipalveluApiBase}data-collection/?${queryParameters(
                null,
                null,
                null,
                null,
                null,
                koulutustoimija,
                rooli,
            )}`,
        );

export const raportiointipalveluGetKysymysryhmaDataCollection$ =
    (user: UserInfoType) =>
    (rooli: string, koulutustoimija: string | null = null) =>
        raportointipalveluHttpImpersonation(user).get<Array<KysymysryhmaCollectionType>>(
            `${raportointipalveluApiBase}data-collection/?${queryParameters(
                null,
                null,
                null,
                null,
                null,
                koulutustoimija,
                rooli,
            )}`,
        );

export const raportiointipalveluGetRaportti$ =
    (user: UserInfoType) =>
    (
        kysymysryhmaId: number,
        koulutustoimija: string,
        jobTitle: string,
        eligibility: boolean,
        alkupvm: string,
        rooli: string,
    ) =>
        raportointipalveluHttpImpersonation(user)
            .get<RaporttiType>(
                // eslint-disable-next-line max-len
                `${raportointipalveluApiBase}view-kysymysryhma-report/kysymysryhmaid=${kysymysryhmaId}/koulutustoimija=${koulutustoimija}/?${queryParameters(
                    jobTitle,
                    eligibility,
                    alkupvm,
                    null,
                    null,
                    null,
                    rooli,
                )}`,
            )
            .pipe(
                map(
                    (rb: RaporttiType) =>
                        ({
                            ...rb,
                            reporting_base: {
                                ...rb.reporting_base,
                                questions: convertKysymyksetArvoToValssi(
                                    rb.reporting_base.questions as any as ArvoKysymys[],
                                ).sort((qa, qb) => (qa?.order || 0) - (qb?.order || 0)),
                            },
                        }) as RaporttiType,
                ),
            );

export const raportiointipalveluGetRaporttiPdf$ =
    (user: UserInfoType) =>
    (
        kysymysryhmaId: number | null,
        koulutustoimija: string,
        jobTitle: string,
        eligibility: boolean,
        alkupvm: string,
        rooli: string,
        language = 'fi',
    ) =>
        raportointipalveluHttpImpersonation(user).get<string>(
            // eslint-disable-next-line max-len
            `${raportointipalveluApiBase}download-kysymysryhma-report/kysymysryhmaid=${kysymysryhmaId}/koulutustoimija=${koulutustoimija}/?${queryParameters(
                jobTitle,
                eligibility,
                alkupvm,
                language,
                true,
                null,
                rooli,
            )}`,
        );
