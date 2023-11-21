import ArvoInputTypes, {
    arvoAddMatriisiKysymys$,
    ArvoKysymys,
    arvoPatchJsonHttp$,
    arvoPostJsonHttp$,
    MetatiedotType,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {KysymysType} from '@cscfi/shared/services/Data/Data-service';
import InputTypes, {
    KysymysMatrixTypes,
    KysymysStringTypes,
} from '@cscfi/shared/components/InputType/InputTypes';

// Change the kysymysid type to optional. Kysymysid is not to be sent with POST/PUT/PATCH
type ArvoKysymysCreateOrModify = Omit<ArvoKysymys, 'kysymysid'> & {kysymysid?: number};

const createNewKysymys$ = (kyselyId: number, body: ArvoKysymysCreateOrModify) =>
    arvoPostJsonHttp$(`kysymys/kysymysryhma/${kyselyId}`, body);

const updateKysymys$ = (kysymysId: number, body: ArvoKysymysCreateOrModify) =>
    arvoPatchJsonHttp$(`kysymys/${kysymysId}`, body);

export const saveMatriisiKysymysDb = (kysymys: KysymysType, inputType: InputTypes) => {
    type PostRequestBodyType = {
        poistettava: boolean;
        pakollinen: boolean;
        kysymys_fi: string;
        kysymys_sv: string;
        metatiedot: MetatiedotType;
        vastaustyyppi?: ArvoInputTypes;
        eos_vastaus_sallittu?: boolean;
    };
    const postRequestBody: PostRequestBodyType = {
        poistettava: true,
        pakollinen: kysymys.required,
        kysymys_fi: kysymys.title.fi,
        kysymys_sv: kysymys.title.sv,
        metatiedot: {
            type: inputType as 'matrix_sliderscale' | 'matrix_radiobutton',
            description: kysymys.description,
        },
        ...(kysymys.answerType && {vastaustyyppi: kysymys.answerType}),
    };
    return arvoAddMatriisiKysymys$(kysymys.matrixRootId!, postRequestBody);
};

export const saveKysymysDb = (selectedKyselyId: number, kysymys: KysymysType) => {
    if (kysymys.id < 0) {
        // Create a new kysymys in the DB
        let metatiedot: MetatiedotType;
        let vastaustyyppi: ArvoInputTypes;
        let matriisikysymykset: ArvoKysymys[] = [];
        if (KysymysStringTypes.includes(kysymys.inputType)) {
            metatiedot = {
                type: 'string',
                numeric: kysymys.inputType === InputTypes.numeric,
                multiline: kysymys.inputType === InputTypes.multiline,
                description: kysymys.description,
            };
            vastaustyyppi = ArvoInputTypes.string;
        } else if (kysymys.inputType === InputTypes.checkbox) {
            metatiedot = {
                type: 'checkbox',
                vastausvaihtoehdot: kysymys.answerOptions,
                description: kysymys.description,
            };
            vastaustyyppi = ArvoInputTypes.monivalinta;
        } else if (kysymys.inputType === InputTypes.radio) {
            metatiedot = {
                type: 'radiobutton',
                vastausvaihtoehdot: kysymys.answerOptions,
                description: kysymys.description,
            };
            vastaustyyppi = ArvoInputTypes.monivalinta;
        } else if (KysymysMatrixTypes.includes(kysymys.inputType)) {
            metatiedot = {
                type:
                    kysymys.inputType === InputTypes.matrix_slider
                        ? 'matrix_sliderscale'
                        : 'matrix_radiobutton',
                description: kysymys.description,
            };
            vastaustyyppi = ArvoInputTypes.matrix_root;
            matriisikysymykset = kysymys.matrixQuestions.map(
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
                    }) as ArvoKysymys,
            );
        } else {
            /*
            kysymys.inputType === InputTypes.statictext
            */
            metatiedot = {
                type: 'statictext',
                description: kysymys.description,
            };
            vastaustyyppi = ArvoInputTypes.string;
        }
        const postRequestBody = {
            poistettava: true,
            metatiedot,
            pakollinen: kysymys.required,
            eos_vastaus_sallittu: kysymys.allowEos || false,
            vastaustyyppi,
            kysymys_fi: kysymys.title.fi,
            kysymys_sv: kysymys.title.sv,
            matriisikysymykset,
        };
        return createNewKysymys$(selectedKyselyId, postRequestBody);
    }
    // Update an existing kysymys in the DB
    type PatchRequestBodyType = {
        pakollinen: boolean;
        kysymys_fi: string;
        kysymys_sv: string;
        metatiedot?: MetatiedotType;
        matriisi_kysymysid?: number;
        vastaustyyppi?: ArvoInputTypes;
        eos_vastaus_sallittu?: boolean;
    };
    const patchRequestBody: PatchRequestBodyType = {
        pakollinen: kysymys.required,
        kysymys_fi: kysymys.title.fi,
        kysymys_sv: kysymys.title.sv,
        eos_vastaus_sallittu: kysymys.allowEos || false,
    };
    if (KysymysStringTypes.includes(kysymys.inputType)) {
        patchRequestBody.metatiedot = {
            type: 'string',
            numeric: kysymys.inputType === InputTypes.numeric,
            multiline: kysymys.inputType === InputTypes.multiline,
            description: kysymys.description,
            hidden: kysymys.hidden,
        };
    } else if (kysymys.inputType === InputTypes.checkbox) {
        patchRequestBody.metatiedot = {
            type: 'checkbox',
            vastausvaihtoehdot: kysymys.answerOptions,
            description: kysymys.description,
            hidden: kysymys.hidden,
        };
    } else if (kysymys.inputType === InputTypes.radio) {
        patchRequestBody.metatiedot = {
            type: 'radiobutton',
            vastausvaihtoehdot: kysymys.answerOptions,
            description: kysymys.description,
            hidden: kysymys.hidden,
        };
    } else if (
        kysymys.inputType === InputTypes.matrix_slider ||
        kysymys.inputType === InputTypes.matrix_radio
    ) {
        patchRequestBody.metatiedot = {
            type: kysymys.inputType,
            description: kysymys.description,
            hidden: kysymys.hidden,
        };
        // TODO: vastaustyypin vaihto estetty toistaiseksi
        /* if (kysymys.answerType) {
            patchRequestBody.vastaustyyppi = kysymys.answerType;
        } */
    } else {
        /*
        kysymys.inputType === InputTypes.statictext
        */
        patchRequestBody.metatiedot = {
            type: 'statictext',
            description: kysymys.description,
            hidden: kysymys.hidden,
        };
    }
    return updateKysymys$(kysymys.id, patchRequestBody);
};

export default saveKysymysDb;
