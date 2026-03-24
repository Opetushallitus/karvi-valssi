import type {Locale} from 'date-fns';
import {format, parseISO} from 'date-fns';
import {fi, sv} from 'date-fns/locale';
import {isEqual, omit, pick} from 'lodash';
import {
    KyselyType,
    KysymysType,
    GenericFormValueType,
} from '@cscfi/shared/services/Data/Data-service';
import {
    ArvoKysely,
    ArvoOppilaitos,
    Oppilaitos,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {Observable} from 'rxjs';
import {OppilaitosType} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {styled} from '@mui/material/styles';
import {isOid} from './validators';
import InputTypes from '../components/InputType/InputTypes';

/**
 * Helps e.g., filtering empty values from an array and keeping array type as non-nillable.
 * @param value
 */
export function notEmpty<TValue>(value: TValue | null | undefined): value is TValue {
    return value !== null && value !== undefined;
}
export const round = (value: number, precision = 0) => {
    const multiplier = 10 ** precision;
    return Math.round(value * multiplier) / multiplier;
};

export const isNumeric = (num: any) =>
    (typeof num === 'number' || (typeof num === 'string' && num.trim() !== '')) &&
    !Number.isNaN(num as number);

/**
 * Removes running number from indicator translation
 * @param indic
 */
export const fixIndicatorTranslation = (indic: string) => {
    const arr = indic.split(' ');
    arr.shift();
    return arr.join(' ');
};

/**
 * fi, sv
 * @param locale
 */
export function getDateFnsLocale(locale: string): Locale {
    switch (locale) {
        case 'fi':
            return fi;
        case 'sv':
            return sv;
        default:
            return fi;
    }
}

export function getQueryParam(location: any, param: string) {
    const queryParams = new URLSearchParams(location.search);
    const queryParam = queryParams.get(param);
    return queryParam || null;
}

export function getQueryParamAsNumber(location: any, param: string) {
    const queryParam = getQueryParam(location, param);
    return queryParam && isNumeric(queryParam)
        ? parseInt(queryParam as string, 10)
        : null;
}

export const deepCopy = (inputObject: object) => JSON.parse(JSON.stringify(inputObject));

export function capitalize(word: string) {
    return word.charAt(0).toUpperCase() + word.slice(1);
}

export const uniqueNumber = () => Math.floor((Date.now() / 1000) * Math.random());

export const objectsEqual = (obj1: any, obj2: any) => isEqual(obj1, obj2);

export const objectsEqualExclude = (obj1: any, obj2: any, keys: string[]) =>
    objectsEqual(omit(obj1, keys), omit(obj2, keys));

export const objectsEqualIncludeOnly = (obj1: any, obj2: any, keys: string[]) =>
    objectsEqual(pick(obj1, keys), pick(obj2, keys));

export const validOidOrNull = (oid: string | null) =>
    oid && isOid.test(oid) ? oid : null;

export const kysymysRyhmaArvoKyselyMatch = (
    arvoKysely: ArvoKysely,
    kysymysryhmaId: number,
) => {
    const loppu = parseISO(arvoKysely.voimassa_loppupvm);
    const nyt = new Date(new Date().setHours(2, 0, 0, 0)); // gets right timzone

    return arvoKysely.metatiedot.valssi_kysymysryhma === kysymysryhmaId && nyt <= loppu;
};

export const formatDate = (input: Date | string | undefined | null) => {
    if (input === null || input === undefined) return null;
    const date = new Date(input as string);
    if (!Number.isNaN(date.getTime())) {
        return format(date, 'dd.MM.yyyy');
    }
    return null;
};

export function kyselyNameGenerator(
    kysymysryhma: KyselyType,
    pvm: Date | null | undefined,
    toimipaikka: (ArvoOppilaitos | OppilaitosType) | null | undefined,
    nameExtender: number | null | undefined,
) {
    const pvmOrNull = pvm && `${pvm.getMonth() + 1}/${pvm.getFullYear()}`;
    const extendedName = nameExtender ? `${pvmOrNull}_${nameExtender}` : pvmOrNull;
    let nimiFi: string | undefined;
    let nimiSv: string | undefined;
    if (toimipaikka && 'nimi_fi' in toimipaikka && 'nimi_sv' in toimipaikka) {
        nimiFi = toimipaikka?.nimi_fi;
        nimiSv = toimipaikka?.nimi_sv;
    } else if (toimipaikka && 'name' in toimipaikka) {
        nimiFi = toimipaikka?.name?.fi;
        nimiSv = toimipaikka?.name?.sv;
    }
    return {
        fi: [kysymysryhma.topic.fi, extendedName, nimiFi].filter(notEmpty).join(' '),
        sv: [kysymysryhma.topic.sv, extendedName, nimiSv].filter(notEmpty).join(' '),
    };
}

export const convertOppilaitos = (oppilaitos: Oppilaitos): ArvoOppilaitos => ({
    nimi_fi: oppilaitos.oppilaitos_fi,
    nimi_sv: oppilaitos.oppilaitos_sv,
    nimi_en: oppilaitos.oppilaitos_en,
    oid: oppilaitos.oppilaitos_oid,
    koulutustoimija: '',
});

export const base64ToArrayBuffer = (base64: string): ArrayBuffer => {
    const binaryString = window.atob(base64);
    const len = binaryString.length;
    const byteArray = new Uint8Array(len);
    for (let i = 0; i < len; i++) byteArray[i] = binaryString.charCodeAt(i);
    return byteArray.buffer;
};

const downloadApiFile = (blob: Blob, filename: string) => {
    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    link.click();
};

export const downloadPdf = (observable: Observable<any>, filename: string) => {
    observable.subscribe((resp: string) => {
        const arrBuff = base64ToArrayBuffer(resp);
        const blob = new Blob([arrBuff], {type: 'application/pdf'});
        downloadApiFile(blob, filename);
    });
};

export const downloadCsv = (observable: Observable<string>, filename: string) => {
    observable.subscribe((resp: string) => {
        /*  TODO: Back-end sends (?) UTF-8 with appropriate BOM
         *   In theory, the next line should not be needed for scandic characters to work
         */
        const csvData = `\uFEFF${resp}`; // Add BOM for UTF-8 encoding
        const blob = new Blob([csvData], {type: 'text/csv'});
        downloadApiFile(blob, filename);
    });
};

export const defaultFormValues = (kyselyId: number, kysymykset: KysymysType[] = []) => {
    const formDefaultValues: GenericFormValueType = {};
    for (let i = 0; i < kysymykset.length; i += 1) {
        const kysymys = kysymykset[i];
        const kyselyKysymysId = `${kyselyId}_${kysymys.id}`;
        switch (kysymys.inputType) {
            case InputTypes.singletext:
            case InputTypes.multiline:
            case InputTypes.numeric:
                formDefaultValues[kyselyKysymysId] = '';
                break;
            case InputTypes.radio:
            case InputTypes.checkbox:
            case InputTypes.dropdown: {
                const checkboxOptions: any = {};
                for (let j = 0; j < kysymykset[i].answerOptions.length; j += 1) {
                    const checkboxOptionId = kysymykset[i].answerOptions[j].id;
                    checkboxOptions[checkboxOptionId] =
                        kysymykset[i].answerOptions[j].checked;
                }
                formDefaultValues[kyselyKysymysId] = checkboxOptions;
                break;
            }
            case InputTypes.matrix_slider:
            case InputTypes.matrix_radio:
            case InputTypes.statictext:
                // default value is undefined
                break;
            default:
                console.warn(`Error! Invalid kysymysType: ${kysymys.inputType}`);
                break;
        }
    }
    return formDefaultValues;
};

export const getFollowupNotSatisfied = (
    kyselyid: number | string,
    kysymys: KysymysType,
    exclusiveFalse: boolean,
    watchValues: {[p: string]: any}, // from useWatch
) => {
    const value =
        watchValues[`${kyselyid}_${kysymys?.followupTo?.questionId}`]?.[
            `${kysymys.followupTo?.questionAnswer}`
        ];
    return exclusiveFalse ? value === false : value !== true;
};

const langCodeOrder = ['FI', 'SV', 'EN', 'XX'];
export function sortedLangs(langArr: Array<string>): Array<string> {
    return langArr.sort((a, b) => {
        const indexA = langCodeOrder.indexOf(a.toUpperCase());
        const indexB = langCodeOrder.indexOf(b.toUpperCase());
        // If element is not in langCodeOrder, place it in the end of the list.
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        return indexA - indexB;
    });
}

export const BoxStyleOverrides = styled('div')({
    '& .MuiGrid-root': {
        'align-content': 'flex-start',
    },
});
