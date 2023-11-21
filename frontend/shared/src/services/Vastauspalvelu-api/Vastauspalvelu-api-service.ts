import {tap} from 'rxjs/operators';
import {MessageType} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {vastauspalveluHttp} from '../Http/Http-service';
import {vastauspalveluHostname} from '../Settings/Settings-service';
import {MatrixType, StatusType} from '../Data/Data-service';
import {ArvoKysymysryhma} from '../Arvo-api/Arvo-api-service';
import AlertService, {AlertTable, AlertType} from '../Alert/Alert-service';

type VastauspalveluKysymysryhmaDouble = {
    jarjestys: number;
    kysymysryhma: ArvoKysymysryhma;
};

type VastauspalveluKysely = {
    koulutustoimija: string; // organisaatio-oid
    oppilaitos: string;
    kyselyid: number;
    nimi_en: string;
    nimi_fi: string;
    nimi_sv: string;
    tila: StatusType;
    uudelleenohjaus_url: string;
    voimassa_alkupvm: string; // date
    voimassa_loppupvm: string; // date
    sivutettu: boolean;
    tyyppi: string;
    kysymysryhmat: Array<VastauspalveluKysymysryhmaDouble>;
};

type VastauspalveluTyontekija = {
    tehtavanimike: string;
    kelpoisuus: string;
    tutkinto: string;
};

type VastauspalveluKyselykerta = {
    kyselykertaid: number;
    nimi: string;
    voimassa_alkupvm: string; // date
    voimassa_loppupvm: string; // date
    kysely: VastauspalveluKysely;
    tyontekija: VastauspalveluTyontekija;
    tempvastaus_allowed?: boolean;
};

export type TempVastaus = {
    en_osaa_sanoa: boolean | null;
    kysymysid: string;
    numerovalinta: string | null;
    string: string | null;
};

const vastauspalveluApiBase = `${vastauspalveluHostname}api/v1/`;
const kyselykertaApi = 'kyselykerta/';
const vastaa = 'vastaa/';
const tempVastaus = 'tempvastaus/';
const matrixApi = `${vastauspalveluApiBase}scale/`;
const messageApi = `${vastauspalveluApiBase}malfunction-message/`;

export const vastauspalveluPostTempAnswers$ = (formData: any) =>
    vastauspalveluHttp.post<string>(`${vastauspalveluApiBase}${tempVastaus}`, formData);

export const vastauspalveluGetTempAnswers$ = (vastaajatunnus: string) =>
    vastauspalveluHttp.get<Array<TempVastaus>>(
        `${vastauspalveluApiBase}${tempVastaus}${vastaajatunnus}/`,
        {},
    );

/**
 * Get kyselykerta
 * -
 * @param vastaajatunnus
 */
const vastauspalveluGetKyselykerta$ = (vastaajatunnus: string) =>
    vastauspalveluHttp.get<VastauspalveluKyselykerta>(
        `${vastauspalveluApiBase}${kyselykertaApi}${vastaajatunnus}/`,
        {},
        {
            404: {
                severity: 'warning',
                disabled: true,
            },
            403: {
                severity: 'warning',
                disabled: true,
            },
        } as AlertTable,
    );

export const vastauspalveluPostAnswers$ = (data: object, language = 'fi') =>
    vastauspalveluHttp.post<string>(
        `${vastauspalveluApiBase}${vastaa}?language=${language}`,
        data,
    );

export const vastauspalveluGetMatrixScales$ = () =>
    vastauspalveluHttp.getWithCache<Array<MatrixType>>(`${matrixApi}`);

export default vastauspalveluGetKyselykerta$;

export const vastauspalveluGetMessages$ = () =>
    vastauspalveluHttp.getWithCache<MessageType>(`${messageApi}get-active/`).pipe(
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
