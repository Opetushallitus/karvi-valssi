import {tap} from 'rxjs/operators';
import AlertService, {AlertType} from '../Alert/Alert-service';
import {UserInfoType} from '../Login/Login-service';
import {
    virkailijapalveluHttp,
    virkailijapalveluHttpImpersonation,
} from '../Http/Http-service';
import {MatrixType} from '../Data/Data-service';
import {virkailijapalveluHostname} from '../Settings/Settings-service';

export type VastaajaTiedotType = {
    email: string;
    vastaajatunnus: string;
};
export type ResponseType = {
    created: number;
};
export type FormType = {
    message: string;
    tyontekijat: string;
    startDate: Date | null | number | undefined;
    endDate: Date | null | number;
    generatedEmails?: Array<PeopleType>;
    generatedEmailsString?: string;
};
export type CheckedElemType = {
    checked: boolean;
    id: number;
};
export type NimikkeetType = {
    fi?: Array<string>;
    sv?: Array<string>;
};
export type TehtavanimikkeetType = {
    tehtavanimike_koodi: string;
    tehtavanimike_values: any;
};
type KoodistoType = {
    koodistoUri: string;
    koodistoVersios: Array<number>;
    organisaatioOid: string;
};
export type MetadataType = {
    eiSisallaMerkitysta: string;
    huomioitavaKoodi: string;
    kasite: string;
    kayttoohje: string;
    kieli: string;
    kuvaus: string;
    lyhytNimi: string;
    nimi: string;
    sisaltaaKoodiston: string;
    sisaltaaMerkityksen: string;
};

export type PeopleType = {
    checkedElem: CheckedElemType;
    kokoNimi?: string;
    kutsumanimi: string;
    nimikkeet: NimikkeetType;
    sukunimi: string;
    tehtavanimikkeet: Array<TehtavanimikkeetType>;
    email: string;
    message: string;
    tyontekija_id?: number;
};
export type OpintopolkuTehtavanimikkeetType = {
    koodiArvo: string;
    koodiUri: string;
    koodisto: KoodistoType;
    metadata: Array<MetadataType>;
    paivittajaOid: string;
    paivitysPvm: string;
    resourceUri: string;
    tila: string;
    versio: number;
    version: number;
    voimassaAlkuPvm: string;
    voimassaLoppuPvm: string | null;
};
export type TyontekijatType = {
    email: string;
    tyontekija_id?: number;
};
export type VastaajatunnusType = {
    voimassa_alkupvm: Date | number; // date
    voimassa_loppupvm: Date | number; // date
};
export type LastKyselysendType = {
    message?: string | undefined;
    vastaajatunnus: VastaajatunnusType;
};

export type IndikaattoriType = {
    group_id: number;
    key: string;
    laatutekija: string;
};

export type IndikaattoriGroupType = {
    group_id: number;
    indicators: IndikaattoriType[];
};

// simple type for request (see TyontekijaType below)
export type TyontekijaSendType = {
    email: string;
    tyontekija_id?: number;
};

// more info coming back from response (see TyontekijaSendType above)
export type TyontekijaType = {
    tyontekija_id?: number;
    email: string;
    kyselykerta: number;
    vastaajatunnus: string;
    msg_id: number;
    msg_status: string;
};

enum IsUsedType {
    used = 'used',
    not_used = 'not_used',
    active = 'active',
}

export default IsUsedType;

export type KyselykertaIsUsedType = {
    is_used: IsUsedType;
};

export type UpdatedNumberType = {
    updated: number;
};

export type KyselykertaType = {
    kyselyid: number;
    kyselykertaid: number;
    voimassa_alkupvm: string;
    voimassa_loppupvm: string;
    last_kyselysend?: any;
};

export type VirkailijapalveluKyselyResponseType = {
    created: number;
};

export type VirkailijapalveluKyselySendObject = {
    kyselykerta: number;
    voimassa_alkupvm: string;
    voimassa_loppupvm: string;
    tyontekijat: Array<TyontekijaSendType>;
    message: string;
};

export type VirkailijapalveluKyselySendUpdateObject = [
    {
        id: number;
        email: string;
    },
];

export type HasBeenSentToPeopleType = {
    id: number;
    email: string;
    msg_status: string;
    tyontekija_id: number;
};

export type ToimipaikanTyontekijaType = {
    email: string;
    kutsumanimi: string;
    sukunimi: string;
    tehtavanimikkeet: Array<TehtavanimikkeetType>;
};

export type MessageType = {
    message: string;
};

const virkailijapalveluApiBase = `${virkailijapalveluHostname}api/v1/`;
const kyselysendApi = `${virkailijapalveluApiBase}kyselysend/`;
const kyselykertaApi = `${virkailijapalveluApiBase}kyselykerta/`;
const kysymysryhmaApi = `${virkailijapalveluApiBase}kysymysryhma/`;
const indikaattoriApi = `${virkailijapalveluApiBase}indikaattori/grouped/`;
const tyontekijaApi = `${virkailijapalveluApiBase}tyontekija/`;
const matrixApi = `${virkailijapalveluApiBase}scale/`;
const messageApi = `${virkailijapalveluApiBase}malfunction-message/`;

/**
 * Send request for backend to send email to recipients about the questionnaire.
 * body params
 * - kyselykertaid
 * - voimassa_alkupvm
 * - voimassa_loppupvm
 * - array of tyontekija objects. The object consists at least of email address and of
 * tyontekija_id (if the user can be found from Varda).
 */
export const virkailijapalveluSendKysely$ =
    (user: UserInfoType) => (body: VirkailijapalveluKyselySendObject) =>
        virkailijapalveluHttpImpersonation(
            user,
        ).post<VirkailijapalveluKyselyResponseType>(kyselysendApi, body);

/**
 * Re-send emails for recipients
 * body params
 * - id
 * - email
 */
export const virkailijapalveluSendUpdateKysely$ =
    (user: UserInfoType) => (body: VirkailijapalveluKyselySendUpdateObject) =>
        virkailijapalveluHttpImpersonation(user).put<VirkailijapalveluKyselyResponseType>(
            `${kyselysendApi}update/`,
            body,
        );

/**
 * get active kyselykerta by kysymyryhmaId
 */
export const virkailijapalveluGetActiveKyselykerta$ =
    (user: UserInfoType) => (kysymysryhmaId: number, org: string | undefined) =>
        virkailijapalveluHttpImpersonation(user).get<Array<KyselykertaType>>(
            `${kyselykertaApi}active/kysymysryhma=${kysymysryhmaId}/organisaatio=${org}/`,
        );

export const base64ToArrayBuffer = (base64: string): Uint8Array => {
    const binaryString = window.atob(base64);
    const bytes = [...Array(binaryString.length)].map((_, i) =>
        binaryString.charCodeAt(i),
    );
    return new Uint8Array(bytes);
};

/**
 * get kysymysryhma as file (PDF)
 * @param kysymysryhmaId
 * @param language
 */
export const virkailijapalveluGetPdfKysymysryhma$ =
    (user: UserInfoType) =>
    (kysymysryhmaId: number, language = 'fi') =>
        virkailijapalveluHttpImpersonation(user).get<string>(
            `${kysymysryhmaApi}${kysymysryhmaId}/pdf/?language=${language}&base64=true`,
        );

export const virkailijapalveluSetKysymysryhmaArchived$ =
    (user: UserInfoType) => (kysymysryhmaId: number) =>
        virkailijapalveluHttpImpersonation(user).patch<UpdatedNumberType>(
            `${kysymysryhmaApi}${kysymysryhmaId}/set-archived/`,
        );

/**
 * get info on whether kysymysryhma has been used in a kysely and if it is active.
 */

export const virkailijapalveluGetIsKysymysryhmaUsed$ = (kysymysryhmaId: number) =>
    virkailijapalveluHttp.get<KyselykertaIsUsedType>(
        `${kysymysryhmaApi}${kysymysryhmaId}/used/`,
    );

/**
 * get all prosessitekijä indicators
 */
export const virkailijapalveluGetProsessitekijaIndikaattorit$ =
    (user: UserInfoType) => () =>
        virkailijapalveluHttpImpersonation(user).get<Array<IndikaattoriGroupType>>(
            `${indikaattoriApi}?laatutekija=prosessi`,
        );

/**
 * get all rakennetekijä indicators
 */
export const virkailijapalveluGetRakennetekijaIndikaattorit$ =
    (user: UserInfoType) => () =>
        virkailijapalveluHttpImpersonation(user).get<Array<IndikaattoriGroupType>>(
            `${indikaattoriApi}?laatutekija=rakenne`,
        );

/**
 * get indicators per indicator group
 */
export const virkailijapalveluGetIndikaattoriRyhma$ =
    (user: UserInfoType) => (id: number) =>
        virkailijapalveluHttpImpersonation(user).get<Array<IndikaattoriGroupType>>(
            `${indikaattoriApi}?group_id=${id}`,
        );

/* get tyontekija list */
export const virkailijapalveluGetTyontekijaList$ =
    (user: UserInfoType) => (toimipaikka: string) =>
        virkailijapalveluHttpImpersonation(user).get<Array<ToimipaikanTyontekijaType>>(
            `${tyontekijaApi}list/toimipaikka=${toimipaikka}/`,
        );

export const virkailijapalveluPostSendKyselyList$ =
    (user: UserInfoType) => (id: number) =>
        virkailijapalveluHttpImpersonation(user).post<Array<HasBeenSentToPeopleType>>(
            `${kyselysendApi}list/?kyselykerta=${id}`,
        );

export const virkailijapalveluPostMultiKyselykerta$ =
    (user: UserInfoType) => (body: any) =>
        virkailijapalveluHttpImpersonation(user).post<any>(
            `${kyselykertaApi}active/multi/`,
            body,
        );

/**
 * move Kyselys' end dates forward (Pääkäyttäjä)
 */
export const virkailijapalveluPatchEnddateMassUpdate$ =
    (user: UserInfoType) =>
    (kysymysryhmaid: number, koulutustoimija: string, alkupvm: string, body: any) =>
        virkailijapalveluHttpImpersonation(user).patch<any>(
            `${kyselykertaApi}extend-enddate/kysymysryhmaid=${kysymysryhmaid}/koulutustoimija=${koulutustoimija}/alkupvm=${alkupvm}/`,
            body,
        );

export const virkailijapalveluGetMatrixScales$ = () =>
    virkailijapalveluHttp.getWithCache<Array<MatrixType>>(`${matrixApi}`);

export const virkailijapalveluGetMessages$ = () =>
    virkailijapalveluHttp.getWithCache<MessageType>(`${messageApi}get-active/`).pipe(
        tap((msg) => {
            const alert = {
                sticky: true,
                titlePlain: msg.message,
                severity: 'warning',
                highlight: true,
            } as AlertType;
            if (msg.message !== null && msg.message !== '') AlertService.showAlert(alert);
        }),
    );
