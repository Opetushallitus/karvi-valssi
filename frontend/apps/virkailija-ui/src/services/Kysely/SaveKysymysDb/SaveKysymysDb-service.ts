import {
    arvoAddMatriisiKysymys$,
    ArvoJatkoKysymykset,
    ArvoKysymys,
    arvoPatchJsonHttp$,
    arvoPostJsonHttp$,
    MetatiedotType,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import ArvoInputTypes, {
    FollowupQuestionsType,
    KysymysType,
} from '@cscfi/shared/services/Data/Data-service';
import InputTypes, {
    KysymysMatrixTypes,
    KysymysStringTypes,
} from '@cscfi/shared/components/InputType/InputTypes';

// Change the kysymysid type to optional. Kysymysid is not to be sent with POST/PUT/PATCH
type ArvoKysymysCreateOrModify = Omit<ArvoKysymys, 'kysymysid'> & {kysymysid?: number};

const createNewKysymys$ = (kyselyId: number, body: ArvoKysymysCreateOrModify) =>
    arvoPostJsonHttp$(`kysymys/kysymysryhma/${kyselyId}`, body);

const updateKysymys$ = (
    kyselyId: number,
    kysymysId: number,
    body: ArvoKysymysCreateOrModify,
) => arvoPatchJsonHttp$(`kysymys/kysymysryhma/${kyselyId}/kysymys/${kysymysId}`, body);

export const saveMatriisiKysymysDb = (kysymys: KysymysType, inputType: InputTypes) => {
    type PostRequestBodyType = {
        poistettava: boolean;
        pakollinen: boolean;
        kysymys_fi: string;
        kysymys_sv: string;
        kysymys_en: string;
        metatiedot: MetatiedotType;
        vastaustyyppi?: ArvoInputTypes;
        eos_vastaus_sallittu?: boolean;
    };
    const postRequestBody: PostRequestBodyType = {
        poistettava: true,
        pakollinen: kysymys.required,
        kysymys_fi: kysymys.title.fi,
        kysymys_sv: kysymys.title.sv,
        kysymys_en: kysymys.title.en ? kysymys.title.en : '',
        metatiedot: {
            type: inputType as 'matrix_sliderscale' | 'matrix_radiobutton',
            description: kysymys.description,
        },
        ...(kysymys.answerType && {vastaustyyppi: kysymys.answerType}),
    } as PostRequestBodyType;
    return arvoAddMatriisiKysymys$(kysymys.matrixRootId!, postRequestBody);
};

const valssiJatkokysymysToArvo = (
    valssiJatkokysymykset: FollowupQuestionsType,
): ArvoJatkoKysymykset =>
    Object.keys(valssiJatkokysymykset).reduce((data, key) => {
        const jatkokysymys = valssiJatkokysymykset[key];
        data[key] = {
            max_vastaus: 5000,
            kysymysid: jatkokysymys.id,
            metatiedot: {
                numeric: jatkokysymys.inputType === InputTypes.numeric,
                type: 'string',
                multiline: false,
            } as MetatiedotType,
            kysymys_fi: 'monivalinta-mika-muu-generoitu',
            kysymys_sv: 'monivalinta-mika-muu-generoitu',
            kysymys_en: 'monivalinta-mika-muu-generoitu',
        } as ArvoKysymys;
        return data;
    }, {} as ArvoJatkoKysymykset);

const valssiKysmysToArvo = (kysymys: KysymysType, isNew: boolean) => {
    const arvoKysymys: ArvoKysymysCreateOrModify = {
        kysymys_fi: kysymys.title.fi,
        kysymys_sv: kysymys.title.sv,
        kysymys_en: kysymys.title.en ? kysymys.title.en : '',
        poistettava: true,
        pakollinen: kysymys.required,
        eos_vastaus_sallittu: kysymys.allowEos || false,
    };
    const metatiedotBoilerplate = {
        description: kysymys.description,
        hidden: kysymys.hidden || false,
        pagebreak: kysymys.pagebreak || false,
        is_hidden_on_report: kysymys.metatiedot?.is_hidden_on_report || false,
    };

    if (KysymysStringTypes.includes(kysymys.inputType)) {
        arvoKysymys.metatiedot = {
            type: 'string',
            numeric: kysymys.inputType === InputTypes.numeric,
            multiline: kysymys.inputType === InputTypes.multiline,
            ...metatiedotBoilerplate,
        };
        if (isNew) {
            arvoKysymys.vastaustyyppi = ArvoInputTypes.string;
        }
    } else if (kysymys.inputType === InputTypes.checkbox) {
        if (kysymys.followupQuestions) {
            arvoKysymys.jatkokysymykset = valssiJatkokysymysToArvo(
                kysymys.followupQuestions,
            );
        }
        arvoKysymys.metatiedot = {
            type: 'checkbox',
            vastausvaihtoehdot: kysymys.answerOptions,
            ...metatiedotBoilerplate,
        };
        if (isNew) {
            arvoKysymys.vastaustyyppi = ArvoInputTypes.monivalinta;
        }
    } else if (kysymys.inputType === InputTypes.radio) {
        if (kysymys.followupQuestions) {
            arvoKysymys.jatkokysymykset = valssiJatkokysymysToArvo(
                kysymys.followupQuestions,
            );
        }
        arvoKysymys.metatiedot = {
            type: 'radiobutton',
            vastausvaihtoehdot: kysymys.answerOptions,
            ...metatiedotBoilerplate,
        };
        if (isNew) {
            arvoKysymys.vastaustyyppi = ArvoInputTypes.monivalinta;
        }
    } else if (kysymys.inputType === InputTypes.dropdown) {
        arvoKysymys.metatiedot = {
            type: 'dropdown',
            vastausvaihtoehdot: kysymys.answerOptions,
            ...metatiedotBoilerplate,
        };
        if (isNew) {
            arvoKysymys.vastaustyyppi = ArvoInputTypes.monivalinta;
        }
    } else if (KysymysMatrixTypes.includes(kysymys.inputType)) {
        if (kysymys.inputType === InputTypes.matrix_slider) {
            arvoKysymys.metatiedot = {
                type: 'matrix_sliderscale',
                ...metatiedotBoilerplate,
            };
        } else {
            arvoKysymys.metatiedot = {
                type: 'matrix_radiobutton',
                ...metatiedotBoilerplate,
            };
        }

        if (isNew) {
            arvoKysymys.vastaustyyppi = ArvoInputTypes.matrix_root;
            arvoKysymys.matriisikysymykset = kysymys.matrixQuestions.map(
                (mk) =>
                    ({
                        poistettava: true,
                        pakollinen: kysymys.required,
                        eos_vastaus_sallittu: kysymys.allowEos,
                        metatiedot: {
                            type: kysymys.inputType,
                            description: mk.description,
                        },
                        vastaustyyppi: mk.answerType,
                        kysymys_fi: mk.title.fi,
                        kysymys_sv: mk.title.sv,
                        kysymys_en: mk.title.en ? mk.title.en : '',
                    }) as ArvoKysymys,
            );
        }
    } else {
        arvoKysymys.metatiedot = {
            type: 'statictext',
            ...metatiedotBoilerplate,
        };
        if (isNew) arvoKysymys.vastaustyyppi = ArvoInputTypes.string;
    }
    return arvoKysymys;
};

export const saveKysymysDb = (selectedKyselyId: number, kysymys: KysymysType) => {
    const isNew = kysymys.id < 0;
    const body = valssiKysmysToArvo(kysymys, isNew);
    if (isNew) {
        return createNewKysymys$(selectedKyselyId, body);
    }
    return updateKysymys$(selectedKyselyId, kysymys.id, body);
};

export default saveKysymysDb;
