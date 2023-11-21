import {map} from 'rxjs/operators';
import {arvoHttp} from '../Http/Http-service';
import {arvoHostname} from '../Settings/Settings-service';
import {
    CheckBoxType,
    KyselyType,
    KysymysType,
    RadioButtonType,
    StatusType,
    TextType,
    QuestionAnswersType,
    MatrixQuestionScaleType,
} from '../Data/Data-service';
import InputTypes from '../../components/InputType/InputTypes';

enum ArvoInputTypes {
    monivalinta = 'monivalinta',
    string = 'string',
    matrix_root = 'matrix_root',
}

export default ArvoInputTypes;

export type ArvoMatriisikysymysId = {
    kysymysid: number;
};

export type ArvoKyselykerta = {
    aktiivisia_vastaajatunnuksia: number;
    aktiivisia_vastaajia: number;
    automaattinen?: string; // date
    kaytettavissa: boolean;
    kyselyid: number;
    kyselykertaid: number;
    lukittu: boolean;
    luotuaika: string; // date
    nimi: string;
    poistettavissa: boolean;
    vastaajatunnuksia: number;
    vastaajia: number;
    viimeisin_vastaus: string; // date
    voimassa_alkupvm: string; // date
    voimassa_loppupvm: string; // date
};

type ArvoKyselyMetatieto = {
    esikatselu_tunniste: string;
    valssi_saate: string;
    valssi_kysymysryhma: number;
};

export type ArvoKyselySijainti = 'suljettu';

export type ArvoKysely = {
    automatisoitu: boolean;
    kaytettavissa: boolean;
    koulutustoimija: string; // ytunnus
    kyselyid: number;
    kyselykerrat: Array<ArvoKyselykerta>;
    kysymysryhmien_lkm: number;
    metatiedot: ArvoKyselyMetatieto;
    kysymysryhmat: ArvoKysymysryhma[];
    nimi_en: string;
    nimi_fi: string;
    nimi_sv: string;
    selite_en: string;
    selite_fi: string;
    selite_sv: string;
    oppilaitos: string;
    poistettavissa: boolean;
    sijainti: ArvoKyselySijainti;
    sivutettu: boolean;
    tila: StatusType;
    tulevaisuudessa: boolean;
    uudelleenohjaus_url: string;
    vastaajatunnuksia: number;
    vastaajia: number;
    viimeisin_vastaus: string; // date
    voimassa_alkupvm: string; // date
    voimassa_loppupvm: string; // date
};

// aktiiviset oppilaitokset/toimipaikat
export type ArvoOppilaitos = {
    koulutustoimija: string;
    nimi_en: string;
    nimi_fi: string;
    nimi_sv: string;
    oid: string;
    oppilaitoskoodi?: string;
    oppilaitostyyppi?: string;
};

// login service
export type Oppilaitos = {
    oppilaitos_fi: string;
    oppilaitos_sv: string;
    oppilaitos_en: string;
    oppilaitos_oid: string;
};

export type ArvoRooli = {
    kayttooikeus: string;
    koulutustoimija_en?: string;
    koulutustoimija_fi: string;
    koulutustoimija_sv?: string;
    kyselytyypit: Array<string>;
    organisaatio: string;
    oppilaitokset: Array<Oppilaitos>;
    rooli: string;
    rooli_organisaatio_id: number;
};

export type ArvoKayttaja = {
    aktiivinen_rooli: ArvoRooli;
    roolit: Array<ArvoRooli>;
    etunimi: string;
    impersonoitu_kayttaja: string;
    laajennettu: boolean;
    luotuaika: string;
    muutettuaika: string;
    oid: string;
    sukunimi: string;
    uid: string;
    vaihdettu_organisaatio: string;
    voimassa: boolean;
};

type MetatiedotTypeString = {
    type: 'string';
    numeric: boolean;
    multiline: boolean;
    description?: TextType;
    hidden?: boolean;
};

type MetatiedotTypeCheckbox = {
    type: 'checkbox';
    vastausvaihtoehdot: CheckBoxType[];
    description?: TextType;
    hidden?: boolean;
};

type MetatiedotTypeRadio = {
    type: 'radiobutton';
    vastausvaihtoehdot: RadioButtonType[];
    description?: TextType;
    hidden?: boolean;
};

type MetatiedotTypeStatictext = {
    type: 'statictext';
    description?: TextType;
    hidden?: boolean;
};

type MetatiedotTypeMatrixRoot = {
    type: 'matrix_root';
    description?: TextType;
    hidden?: boolean;
};

type MetatiedotTypeMatrixRadio = {
    type: 'matrix_radiobutton';
    description?: TextType;
    hidden?: boolean;
};

type MetatiedotTypeMatrixSlider = {
    type: 'matrix_sliderscale';
    description?: TextType;
    hidden?: boolean;
};

// metatiedot.type -> https://stackoverflow.com/a/64270199
export type MetatiedotType =
    | MetatiedotTypeString
    | MetatiedotTypeCheckbox
    | MetatiedotTypeRadio
    | MetatiedotTypeStatictext
    | MetatiedotTypeMatrixRadio
    | MetatiedotTypeMatrixSlider
    | MetatiedotTypeMatrixRoot;

export type ArvoKysymys = {
    muutettu_kayttaja?: string;
    eos_vastaus_sallittu?: boolean;
    kysymys_en?: string;
    kysymysryhma_sv?: string;
    kysymys_metatiedot?: object;
    jarjestys?: number;
    poistettava?: boolean;
    jatkokysymys?: boolean;
    kysymysryhma_fi?: string;
    selite_fi?: string;
    jatkokysymys_kysymysid?: number;
    kysymysryhmaid?: number;
    selite_sv?: string;
    max_vastaus?: number;
    monivalinta_max?: number;
    metatiedot?: MetatiedotType;
    taustakysymys?: boolean;
    selite_en?: string;
    luotuaika?: string; // date
    kysymysryhma_sn?: any;
    pakollinen: boolean;
    jatkokysymys_vastaus?: any;
    luotu_kayttaja?: string;
    kysymysid: number;
    rajoite?: number;
    raportoitava?: boolean;
    vastaustyyppi?: ArvoInputTypes;
    muutettuaika?: string; // date
    kysymys_sv: string;
    kysymys_fi: string;
    matriisi_jarjestys?: number;
    matriisi_kysymysid?: number;
    matriisikysymykset?: ArvoKysymys[];
    question_answers?: QuestionAnswersType;
    matrix_question_scale?: Array<MatrixQuestionScaleType>;
};

export type PaaIndikaattoriType = {
    group: number;
    key: string;
};

type ArvoKysymysryhmaMetatiedotType = {
    paaIndikaattori: PaaIndikaattoriType;
    sekondaariset_indikaattorit: PaaIndikaattoriType;
    lomaketyyppi: string;
};

export type ArvoKysymysryhma = {
    tila: StatusType;
    nimi_fi: string;
    kuvaus_sv?: string;
    nimi_sv?: string;
    selite_fi?: string;
    kysymysryhmaid: number;
    selite_sv?: string;
    selite_en?: string;
    kysymykset: Array<ArvoKysymys>;
    kuvaus_fi?: string;
    taustakysymykset: boolean;
    valtakunnallinen: boolean;
    kuvaus_en?: string;
    nimi_en?: string;
    metatiedot: ArvoKysymysryhmaMetatiedotType;
    muutettuaika: string; // date
    last_kyselysend?: any;
};

export type ArvoKysymysryhmaPatch = {
    nimi_fi?: string;
    kuvaus_sv?: string;
    nimi_sv?: string;
    selite_fi?: string;
    selite_sv?: string;
    selite_en?: string;
    kuvaus_fi?: string;
    valtakunnallinen?: boolean;
    kuvaus_en?: string;
    nimi_en?: string;
    metatiedot?: any;
};

export type ArvoKyselyKertaPost = {
    kyselyid: number;
    kyselykerta: {
        voimassa_alkupvm: string;
        voimassa_loppupvm: string;
        nimi: string;
    };
};

export type ArvoKyselyPost = {
    tila?: string;
    tyyppi?: string;
    nimi_fi: string;
    nimi_sv?: string;
    voimassa_loppupvm: string;
    voimassa_alkupvm: string;
    kysymysryhmat: [{kysymysryhmaid: number}];
    oppilaitos?: string;
    metatiedot: {
        valssi_saate?: string;
        valssi_kysymysryhma: number;
    };
    kyselykerrat?: [
        {
            nimi: string;
            voimassa_alkupvm: string;
            voimassa_loppupvm: string;
        },
    ];
};

export type ArvoKyselyMassPost = {
    kyselyt: ArvoKyselyPost[];
};

export type ArvoKyselyMassId = {
    kyselyid: number[];
};

export type ArvoKoulutustoimija = {
    kunta: string;
    lakkautuspaiva: string;
    luotuaika: string;
    metatiedot: any;
    muutettuaika: string;
    nimi_en: string;
    nimi_fi: string;
    nimi_sv: string;
    oid: string;
    oppilaitoskoodi: any;
    oppilaitostyyppi: any;
    osoite: string;
    parent_oid: string;
    postinumero: string;
    postitoimipaikka: string;
    puhelin: string;
    sahkoposti: string;
    toimipistekoodi: string;
    tyypit: string[];
    voimassa: boolean;
    www_osoite: string;
    ytunnus: string;
};

export type ArvoImpersonoitava = {
    nimi: string;
    oid: string;
};

export const convertKysymyksetArvoToValssi = (kysymykset: Array<ArvoKysymys>) => {
    const temporaryKysymykset: KysymysType[] = [];
    kysymykset.forEach((arvoKysymys) => {
        const kysymys: KysymysType = {
            id: arvoKysymys.kysymysid,
            inputType: InputTypes.singletext,
            title: {
                fi: arvoKysymys.kysymys_fi,
                sv: arvoKysymys.kysymys_sv,
            },
            description: arvoKysymys.metatiedot?.description,
            hidden: arvoKysymys.metatiedot?.hidden,
            required: arvoKysymys.pakollinen,
            allowEos: arvoKysymys.eos_vastaus_sallittu || false,
            answerOptions: [],
            matrixQuestions: [],
            // answerType: arvoKysymys.vastaustyyppi,
            isMatrixQuestionRoot:
                arvoKysymys.kysymysid === arvoKysymys.matriisi_kysymysid,
            order: arvoKysymys.jarjestys,
        };

        if (
            arvoKysymys.vastaustyyppi === ArvoInputTypes.string &&
            arvoKysymys.metatiedot?.type === 'string'
        ) {
            if (arvoKysymys.metatiedot?.numeric) {
                kysymys.inputType = InputTypes.numeric;
            } else if (arvoKysymys.metatiedot?.multiline) {
                kysymys.inputType = InputTypes.multiline;
            }
        } else if (
            arvoKysymys.vastaustyyppi === ArvoInputTypes.monivalinta &&
            Object.prototype.hasOwnProperty.call(arvoKysymys, 'metatiedot') &&
            Object.prototype.hasOwnProperty.call(
                arvoKysymys.metatiedot,
                'vastausvaihtoehdot',
            ) &&
            (arvoKysymys.metatiedot?.type === 'checkbox' ||
                arvoKysymys.metatiedot?.type === 'radiobutton')
        ) {
            if (arvoKysymys.metatiedot?.type === 'checkbox') {
                kysymys.inputType = InputTypes.checkbox;
            } else if (arvoKysymys.metatiedot?.type === 'radiobutton') {
                kysymys.inputType = InputTypes.radio;
            }
            kysymys.answerOptions = arvoKysymys.metatiedot?.vastausvaihtoehdot;
        } else if (
            arvoKysymys.vastaustyyppi === ArvoInputTypes.string &&
            arvoKysymys.metatiedot?.type === 'statictext'
        ) {
            kysymys.inputType = InputTypes.statictext;
        } else if (
            arvoKysymys.vastaustyyppi === ArvoInputTypes.matrix_root ||
            arvoKysymys.metatiedot?.type === InputTypes.matrix_radio ||
            arvoKysymys.metatiedot?.type === InputTypes.matrix_slider
        ) {
            kysymys.matrixRootId = arvoKysymys.matriisi_kysymysid;
            kysymys.inputType = arvoKysymys.metatiedot?.type as InputTypes;
            kysymys.answerType = arvoKysymys.vastaustyyppi;
            if (arvoKysymys?.matriisikysymykset) {
                kysymys.matrixQuestions = convertKysymyksetArvoToValssi(
                    arvoKysymys.matriisikysymykset,
                );
            }
            if (arvoKysymys?.question_answers) {
                kysymys.question_answers = arvoKysymys.question_answers;
            }
            if (arvoKysymys?.matrix_question_scale) {
                kysymys.matrix_question_scale = arvoKysymys.matrix_question_scale;
            }
        }
        temporaryKysymykset.push(kysymys);
    });
    return temporaryKysymykset;
};

const arvoApiBase = `${arvoHostname}api/`;
const kayttajaApi = 'kayttaja/';
const kyselyApi = 'kysely/';
const kysymysApi = 'kysymys/';
const kysymysryhmaApi = 'kysymysryhma/';
const kyselykertaApi = 'kyselykerta/';
const oppilaitosApi = 'oppilaitos/';

/*
  session
  STARTS
 */

export const arvoKayttaja$ = arvoHttp.getWithCache<ArvoKayttaja>(
    `${arvoApiBase}${kayttajaApi}`,
);

export const arvoImpersonoi$ = (oid: string) =>
    arvoHttp.post<ArvoKayttaja>(`${arvoApiBase}${kayttajaApi}impersonoi`, {
        oid,
    });

export const arvoVaihdaOrganisaatio$ = (oid: string) =>
    arvoHttp.post<ArvoKayttaja>(`${arvoApiBase}${kayttajaApi}vaihda-organisaatio`, {
        oid,
    });

export const arvoVaihdaRooli$ = (roid: number) =>
    arvoHttp.post<ArvoKayttaja>(`${arvoApiBase}${kayttajaApi}rooli`, {
        rooli_organisaatio_id: roid,
    });

export const arvoLopetaImpersonointi$ = arvoHttp.post<any>(
    `${arvoApiBase}${kayttajaApi}lopeta-impersonointi`,
    {
        oid: null,
    },
);

/*
  session
  ENDS
 */

/*
  oppilaitos
  STARTS
 */

/**
 *
 * -
 */
export const arvoGetImpersonoitavaByName$ = (keyword: string) => {
    const getFunc = arvoHttp.get;
    const encoded = encodeURIComponent(keyword);
    return getFunc<ArvoImpersonoitava[]>(
        `${arvoApiBase}kayttaja/impersonoitava?termi=${encoded}`,
    );
};

/**
 *
 * -
 */
export const arvoGetKoulutustoimijaByName$ = (keyword: string) => {
    const getFunc = arvoHttp.get;
    const encoded = encodeURIComponent(keyword);
    return getFunc<ArvoKoulutustoimija[]>(
        `${arvoApiBase}koulutustoimija/hae-nimella?termi=${encoded}`,
    );
};

/**
 * Get oppilaitos
 * -
 */
export const arvoGetOppilaitos$ = (useCache = true) => {
    const getFunc = useCache ? arvoHttp.getWithCache : arvoHttp.get;
    return getFunc<ArvoOppilaitos[]>(
        `${arvoApiBase}${oppilaitosApi}aktiivisen-koulutustoimijan`,
    );
};

/*
 oppilaitos
 ENDS
 */

/*
 kyselykerta
 STARTS
 */

/**
 * Get kyselykerta
 * -
 * @param kyselykertaId
 */
export const arvoGetKyselykerta$ = (kyselykertaId: number) =>
    arvoHttp.get<ArvoKyselykerta>(`${arvoApiBase}${kyselykertaApi}${kyselykertaId}`, {});

/**
 * Add kyselykerta
 * Fails if kyselykerta with name already exists
 * body params
 * - kyselyid
 * - kyselykerta
 */
export const arvoAddKyselykerta$ = (body: ArvoKyselyKertaPost) =>
    arvoHttp.post<ArvoKyselykerta>(`${arvoApiBase}${kyselykertaApi}`, body);

/**
 * Update kyselykerta
 * Fails if kyselykerta with name already exists
 * @param kyselykertaId
 * @param body
 */
export const arvoUpdateKyselykerta$ = (kyselykertaId: number, body: any) =>
    arvoHttp.post<ArvoKyselykerta>(
        `${arvoApiBase}${kyselykertaApi}${kyselykertaId}`,
        body,
    );

/*
 kyselykerta
 ENDS
 */

/*
 kysymys
 STARTS
 */

export const arvoRemoveKysymys$ = (kysymysId: number) =>
    arvoHttp.delete(`${arvoApiBase}${kysymysApi}${kysymysId}`);

export const arvoAddMatriisiKysymys$ = (kysymysId: number, body: any) =>
    arvoHttp.post<ArvoMatriisikysymysId>(
        `${arvoApiBase}${kysymysApi}${kysymysId}/matriisikysymys`,
        body,
    );

/**
 * Swaps order of two questions
 * @param kysymysryhmaId
 * @param kysymysId1
 * @param kysymysId2
 */
export const arvoSwapKysymysOrder$ = (
    kysymysryhmaId: number,
    kysymysId1: number,
    kysymysId2: number,
) =>
    arvoHttp.put<string>(
        `${arvoApiBase}${kysymysApi}vaihda-kysymysten-jarjestys/${kysymysryhmaId}`,
        {
            kysymysid1: kysymysId1,
            kysymysid2: kysymysId2,
        },
    );
/*
 kysymys
 ENDS
 */

/*
 kysymysryhma
 STARTS
 */

export const arvoGetKysymysRyhmat$ = arvoHttp
    .get<Array<ArvoKysymysryhma>>(`${arvoApiBase}${kysymysryhmaApi}`)
    .pipe(
        map((kysymysryhmat) =>
            kysymysryhmat.sort(
                (a: ArvoKysymysryhma, b: ArvoKysymysryhma) =>
                    b.kysymysryhmaid - a.kysymysryhmaid,
            ),
        ),
        map((sortedKysymysryhmat) =>
            sortedKysymysryhmat.map(
                (kysymysryhma) =>
                    ({
                        id: kysymysryhma.kysymysryhmaid,
                        topic: {fi: kysymysryhma.nimi_fi, sv: kysymysryhma.nimi_sv},
                        kysymykset: [],
                        status: kysymysryhma.tila,
                        lomaketyyppi: kysymysryhma.metatiedot?.lomaketyyppi,
                        paaIndikaattori: kysymysryhma.metatiedot?.paaIndikaattori,
                        muutettuaika: kysymysryhma.muutettuaika,
                    }) as KyselyType,
            ),
        ),
    );

export const arvoGetKysymysryhma$ = (kysymysryhmaId: number) =>
    arvoHttp.get<ArvoKysymysryhma>(`${arvoApiBase}${kysymysryhmaApi}${kysymysryhmaId}`);

/**
 * Sets kysymysryhma state to suljettu
 * Without conditions?
 * @param kysymysryhmaId
 */
export const arvoCloseKysymysryhma$ = (kysymysryhmaId: number) =>
    arvoHttp.put<ArvoKysymysryhma>(
        `${arvoApiBase}${kysymysryhmaApi}${kysymysryhmaId}/sulje`,
        {},
    );

/**
 * Disabled per VAL-760, as this functionality is not in scope.
 * Back-end is left as it is, and if needed, this functionality may
 * be reimplemented.
 *
 * Sets kysymysryhma state to luonnos
 * Will fail if related kyselyt count or kyselypohjat count gt than 0.
 * @param kysymysryhmaId
 */
// export const arvoUnPublishKysymysryhma$ = (kysymysryhmaId: number) =>
//     arvoHttp.put<ArvoKysymysryhma>(
//         `${arvoApiBase}${kysymysryhmaApi}${kysymysryhmaId}/palauta`,
//         {},
//     );

/**
 * Sets kysymysryhma state to julkaistu
 * Will fail if related kysymykset count 0
 * @param kysymysryhmaId
 */
export const arvoPublishKysymysryhma$ = (kysymysryhmaId: number) =>
    arvoHttp.put<ArvoKysymysryhma>(
        `${arvoApiBase}${kysymysryhmaApi}${kysymysryhmaId}/julkaise`,
        {},
    );

/**
 * Updates kysymysryhma
 * @param kysymysryhmaId
 * @param body
 */
export const arvoUpdateKysymysryhma$ = (
    kysymysryhmaId: number,
    body: ArvoKysymysryhmaPatch,
) =>
    arvoHttp.patch<ArvoKysymysryhma>(
        `${arvoApiBase}${kysymysryhmaApi}${kysymysryhmaId}`,
        body,
    );

/*
 kysymysryhma
 ENDS
 */

/*
 kysely
 STARTS
 */

/**
 * Posts array of kysely and creates kyselykerta for each of them. Optionally already in tila 'julkaistu'
 * Theres validation for name, cannot create two kysely with same name
 * @param body
 */
export const arvoMassAddKysely$ = (body: ArvoKyselyMassPost) =>
    arvoHttp.post<ArvoKyselyMassId>(`${arvoApiBase}${kyselyApi}massasyotto`, body);

/**
 * Posts kysely
 * Theres validation for name, cannot create two kysely with same name
 * @param body
 */
export const arvoAddKysely$ = (body: ArvoKyselyPost) =>
    arvoHttp.post<ArvoKysely>(`${arvoApiBase}${kyselyApi}`, body);

/**
 * Gets kyselyt
 * Returns all kyselyt based on aktiivinen koulutustoimija
 */
export const arvoGetAllKyselyt$ = () =>
    arvoHttp.get<ArvoKysely[]>(`${arvoApiBase}${kyselyApi}`, {});

/* TODO get all kyselyt which have enddate in the future (in queryParams).
    Use this query in Etusivu and Arviointityökalut pages.

export const arvoGetAllActiveKyselyt$ = () =>
    arvoHttp.get<ArvoKysely[]>(`${arvoApiBase}${activeKyselyApi}`, {});
*/

/**
 * Get kysely
 * @param kyselyId
 */
export const arvoGetKysely$ = (kyselyId: number) =>
    arvoHttp.get<ArvoKysely>(`${arvoApiBase}${kyselyApi}${kyselyId}`, {});

/**
 * Sets kysely state to suljettu
 * Without conditions?
 * @param kyselyId
 */
export const arvoCloseKysely$ = (kyselyId: number) =>
    arvoHttp.put<ArvoKysely>(`${arvoApiBase}${kyselyApi}sulje/${kyselyId}`, {});

/**
 * Sets kysely state to julkaistu
 * Without conditions?
 * @param kyselyId
 */
export const arvoRevertKysely$ = (kyselyId: number) =>
    arvoHttp.put<ArvoKysely>(`${arvoApiBase}${kyselyApi}palauta/${kyselyId}`, {});

/**
 * Sets kysely state to luonnos
 * Will fail if related kyselykerrat count gt 0
 * @param kyselyId
 */
export const arvoUnPublishKysely$ = (kyselyId: number) =>
    arvoHttp.put<ArvoKysely>(
        `${arvoApiBase}${kyselyApi}palauta-luonnokseksi/${kyselyId}`,
        {},
    );

/**
 * Sets kysely state to julkaistu
 * Will fail if related kysymysryhmat count 0
 * @param kyselyId
 */
export const arvoPublishKysely$ = (kyselyId: number) =>
    arvoHttp.put<ArvoKysely>(`${arvoApiBase}${kyselyApi}julkaise/${kyselyId}`, {});

/**
 * Deletes kysely
 * @param kyselyId
 */
export const arvoDeleteKysely$ = (kyselyId: number) =>
    arvoHttp.delete<ArvoKysely>(`${arvoApiBase}${kyselyApi}${kyselyId}`);

/*
 kysely
 ENDS
 */

export const arvoGet$ = (apiEndpoint: string) =>
    arvoHttp.get<ArvoKysymysryhma>(`${arvoApiBase}${apiEndpoint}`);

export const arvoPostJsonHttp$ = (apiEndpoint: string, body: object) =>
    arvoHttp.post<any>(`${arvoApiBase}${apiEndpoint}`, body);

export const arvoPutJsonHttp$ = (apiEndpoint: string, body: object) =>
    arvoHttp.put<any>(`${arvoApiBase}${apiEndpoint}`, body);

export const arvoPatchJsonHttp$ = (apiEndpoint: string, body: object) =>
    arvoHttp.patch<any>(`${arvoApiBase}${apiEndpoint}`, body);

export const arvoDeleteHttp$ = (apiEndpoint: string) =>
    arvoHttp.delete<any>(`${arvoApiBase}${apiEndpoint}`);
