import {map} from 'rxjs/operators';
import {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {arvoHttp} from '../Http/Http-service';
import {arvoHostname} from '../Settings/Settings-service';
import ArvoInputTypes, {
    CheckBoxType,
    DropdownType,
    FollowupQuestionsType,
    KyselyType,
    KysymysType,
    MatrixQuestionScaleType,
    PaaindikaattoriType,
    QuestionAnswersType,
    RadioButtonType,
    SekondaarinenIndikaattoriType,
    StatusType,
    TextType,
} from '../Data/Data-service';
import InputTypes from '../../components/InputType/InputTypes';

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
    description?: TextType;
    hidden?: boolean;
    pagebreak?: boolean;
    is_hidden_on_report?: boolean;
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

export type ArvoKysymysMetatiedotBase = {
    description?: TextType;
    hidden?: boolean;
    pagebreak?: boolean;
    is_hidden_on_report?: boolean;
};

type MetatiedotTypeString = ArvoKysymysMetatiedotBase & {
    type: 'string';
    numeric: boolean;
    multiline: boolean;
};

type MetatiedotTypeCheckbox = ArvoKysymysMetatiedotBase & {
    type: 'checkbox';
    vastausvaihtoehdot: CheckBoxType[];
};

type MetatiedotTypeRadio = ArvoKysymysMetatiedotBase & {
    type: 'radiobutton';
    vastausvaihtoehdot: RadioButtonType[];
};

type MetatiedotTypeDropdown = ArvoKysymysMetatiedotBase & {
    type: 'dropdown';
    vastausvaihtoehdot: DropdownType[];
};

type MetatiedotTypeStatictext = ArvoKysymysMetatiedotBase & {
    type: 'statictext';
};

type MetatiedotTypeMatrixRoot = ArvoKysymysMetatiedotBase & {
    type: 'matrix_root';
};

type MetatiedotTypeMatrixRadio = ArvoKysymysMetatiedotBase & {
    type: 'matrix_radiobutton';
};

type MetatiedotTypeMatrixSlider = ArvoKysymysMetatiedotBase & {
    type: 'matrix_sliderscale';
};

// metatiedot.type -> https://stackoverflow.com/a/64270199
export type MetatiedotType =
    | MetatiedotTypeString
    | MetatiedotTypeCheckbox
    | MetatiedotTypeRadio
    | MetatiedotTypeStatictext
    | MetatiedotTypeMatrixRadio
    | MetatiedotTypeMatrixSlider
    | MetatiedotTypeMatrixRoot
    | MetatiedotTypeDropdown;

export type ArvoJatkoKysymykset = {
    [index: number | string]: ArvoKysymys;
};

export type ArvoKysymys = {
    kysymysid: number;
    kysymys_fi: string;
    kysymys_sv: string;
    kysymys_en?: string;
    kysymysryhmaid?: number;
    selite_fi?: string;
    selite_sv?: string;
    selite_en?: string;
    kysymysryhma_fi?: string;
    kysymysryhma_sv?: string;
    muutettu_kayttaja?: string;
    eos_vastaus_sallittu?: boolean;
    kysymys_metatiedot?: object;
    jarjestys?: number;
    poistettava?: boolean;
    jatkokysymys?: boolean;
    jatkokysymys_kysymysid?: number;
    max_vastaus?: number;
    monivalinta_max?: number;
    metatiedot?: MetatiedotType;
    taustakysymys?: boolean;
    luotuaika?: string; // date
    kysymysryhma_sn?: any;
    pakollinen: boolean;
    jatkokysymys_vastaus?: any;
    luotu_kayttaja?: string;
    rajoite?: number;
    raportoitava?: boolean;
    vastaustyyppi?: ArvoInputTypes;
    muutettuaika?: string; // date
    matriisi_jarjestys?: number;
    matriisi_kysymysid?: number;
    matriisikysymykset?: ArvoKysymys[];
    jatkokysymykset?: ArvoJatkoKysymykset;
    question_answers?: QuestionAnswersType;
    matrix_question_scale?: Array<MatrixQuestionScaleType>;
    string_answer?: {
        fi: string;
        sv: string;
    };
};

type ArvoKysymysryhmaMetatiedotType = {
    paaIndikaattori: PaaindikaattoriType;
    sekondaariset_indikaattorit: SekondaarinenIndikaattoriType[];
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

export type Kayttoraja = {
    kysymysryhmaid: number;
    raja_ylitetty: boolean;
    vanhin_pvm: string | null;
};

export const convertKysymysRyhmaToValssi = (akr: ArvoKysymysryhma): KyselyType => ({
    id: akr.kysymysryhmaid,
    topic: {fi: akr.nimi_fi, sv: akr.nimi_sv, en: akr.nimi_en},
    kysymykset: akr.kysymykset ? convertKysymyksetArvoToValssi(akr.kysymykset) : [],
    status: akr.tila,
    lomaketyyppi: akr.metatiedot?.lomaketyyppi,
    paaIndikaattori: akr.metatiedot?.paaIndikaattori,
    sekondaariset_indikaattorit: akr.metatiedot?.sekondaariset_indikaattorit,
    muutettuaika: akr.muutettuaika,
});

export const convertJatkokysymyksetArvoToValssi = (
    arvoJatkokysymykset: ArvoJatkoKysymykset,
    page: number,
): FollowupQuestionsType =>
    Object.keys(arvoJatkokysymykset).reduce((data, key) => {
        data[key] = convertKysymysArvoToValssi(arvoJatkokysymykset[key], page);
        return data;
    }, {} as FollowupQuestionsType);

export const convertKysymysArvoToValssi = (
    arvoKysymys: ArvoKysymys,
    page: number,
): KysymysType => {
    const kysymys = {
        id: arvoKysymys.kysymysid,
        inputType: InputTypes.singletext,
        title: {
            fi: arvoKysymys.kysymys_fi,
            sv: arvoKysymys.kysymys_sv,
            en: arvoKysymys.kysymys_en,
        },
        description: arvoKysymys.metatiedot?.description,
        hidden: arvoKysymys.metatiedot?.hidden,
        required: arvoKysymys.pakollinen,
        allowEos: arvoKysymys.eos_vastaus_sallittu || false,
        answerOptions: [],
        matrixQuestions: [],
        followupQuestions: {},
        followupTo: {},
        pagebreak: false,
        answerType: arvoKysymys.vastaustyyppi,
        isMatrixQuestionRoot: arvoKysymys.kysymysid === arvoKysymys.matriisi_kysymysid,
        order: arvoKysymys.jarjestys,
        insta: arvoKysymys.jatkokysymys,
        metatiedot: {
            description: arvoKysymys.metatiedot?.description,
            hidden: arvoKysymys.metatiedot?.hidden,
            is_hidden_on_report: arvoKysymys.metatiedot?.is_hidden_on_report,
            pagebreak: arvoKysymys.metatiedot?.pagebreak,
        },
        page,
        string_answer: {
            fi: arvoKysymys.string_answer?.fi,
            sv: arvoKysymys.string_answer?.sv,
        },
    } as KysymysType;

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
            arvoKysymys.metatiedot?.type === 'radiobutton' ||
            arvoKysymys.metatiedot?.type === 'dropdown')
    ) {
        if (arvoKysymys.metatiedot?.type === 'checkbox') {
            kysymys.inputType = InputTypes.checkbox;
        } else if (arvoKysymys.metatiedot?.type === 'radiobutton') {
            kysymys.inputType = InputTypes.radio;
        } else if (arvoKysymys.metatiedot?.type === 'dropdown') {
            kysymys.inputType = InputTypes.dropdown;
        }
        kysymys.answerOptions = arvoKysymys.metatiedot?.vastausvaihtoehdot;

        if (arvoKysymys?.question_answers) {
            kysymys.question_answers = arvoKysymys.question_answers;
        }

        if (arvoKysymys?.jatkokysymykset) {
            kysymys.followupQuestions = convertJatkokysymyksetArvoToValssi(
                arvoKysymys.jatkokysymykset,
                page,
            );
        }
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

    if (arvoKysymys.metatiedot?.pagebreak) kysymys.pagebreak = true;

    if (arvoKysymys.jatkokysymys_kysymysid && arvoKysymys.jatkokysymys_vastaus) {
        kysymys.followupTo = {
            questionId: arvoKysymys.jatkokysymys_kysymysid,
            questionAnswer: arvoKysymys.jatkokysymys_vastaus,
        };
    }

    return kysymys as KysymysType;
};

export const convertKysymyksetArvoToValssi = (
    kysymykset: ArvoKysymys[],
): KysymysType[] => {
    let pagenum: number = 0;
    return kysymykset.map((arvoKysymys): KysymysType => {
        if (arvoKysymys.metatiedot.pagebreak) {
            pagenum += 1;
            return {...convertKysymysArvoToValssi(arvoKysymys, pagenum - 1)};
        }
        return {...convertKysymysArvoToValssi(arvoKysymys, pagenum)};
    });
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
 * Fails if kyselykerta with the name already exists
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
    .get<ArvoKysymysryhma[]>(`${arvoApiBase}${kysymysryhmaApi}`)
    .pipe(
        map((kysymysryhmat) =>
            kysymysryhmat.sort(
                (a: ArvoKysymysryhma, b: ArvoKysymysryhma) =>
                    b.kysymysryhmaid - a.kysymysryhmaid,
            ),
        ),
        map((sortedKysymysryhmat) =>
            sortedKysymysryhmat.map((skr) => convertKysymysRyhmaToValssi(skr)),
        ),
    );

export const arvoGetKysymysryhma$ = (kysymysryhmaId: number) =>
    arvoHttp
        .get<ArvoKysymysryhma>(`${arvoApiBase}${kysymysryhmaApi}${kysymysryhmaId}`)
        .pipe(map((kr) => convertKysymysRyhmaToValssi(kr)));

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

/**
 * Gets kysymysryhma kayttoraja list
 * Returns all kyselyt based on aktiivinen koulutustoimija
 */
export const arvoGetKysymysryhmaKayttoraja$ = (id?: number[] | number) => {
    /* doing query params here because of the same key, params can't be formed when passed as queryParams. */
    const idList: number[] = id && (Array.isArray(id) ? id : [id]);

    const urlQuery =
        idList && idList.length > 0
            ? idList.map((kid) => `kysymysryhmaid=${kid}`).join('&')
            : null;

    return arvoHttp.get<Kayttoraja[]>(
        `${arvoApiBase}${kysymysryhmaApi}kayttoraja${urlQuery ? `?${urlQuery}` : ''}`,
        null,
    );
};

/*
 kysymysryhma
 ENDS
 */

/*
 kysely
 STARTS
 */

/**
 * Posts array of kysely and creates kyselykerta for them each. Optionally already in tila 'julkaistu'
 * There's validation for the name, cannot create two kysely with same name.
 * @param body
 */
export const arvoMassAddKysely$ = (body: ArvoKyselyMassPost) =>
    arvoHttp.post<ArvoKyselyMassId>(`${arvoApiBase}${kyselyApi}massasyotto`, body, {
        /* in this case 400 is returned only if there are validation errors, those are handeld in frontend. */
        400: {disabled: true} as AlertType,
        404: {disabled: true} as AlertType,
    });

/**
 * Posts kysely
 * There's validation for a name, cannot create two kysely with same name.
 * @param body
 */
export const arvoAddKysely$ = (body: ArvoKyselyPost) =>
    arvoHttp.post<ArvoKysely>(`${arvoApiBase}${kyselyApi}`, body, {
        /* in this case 400 is returned only if there are validation errors, those are handeld in frontend. */
        400: {disabled: true} as AlertType,
        404: {disabled: true} as AlertType,
    });

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
 * Will fail if related kyselykerrat count gt 0.
 * @param kyselyId
 */
export const arvoUnPublishKysely$ = (kyselyId: number) =>
    arvoHttp.put<ArvoKysely>(
        `${arvoApiBase}${kyselyApi}palauta-luonnokseksi/${kyselyId}`,
        {},
    );

/**
 * Sets kysely state to julkaistu
 * Will fail if related kysymysryhmat count 0.
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
