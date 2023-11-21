import type {Locale} from 'date-fns';
import {fi, sv} from 'date-fns/locale';
import {pick, isEqual, omit} from 'lodash';
import {
    KyselyType,
    KysymysType,
    TextType,
} from '@cscfi/shared/services/Data/Data-service';
import {
    ArvoKysely,
    ArvoOppilaitos,
    Oppilaitos,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {format, parseISO} from 'date-fns';
import {isOid} from './validators';
import InputTypes from '../components/InputType/InputTypes';
import {GenericFormValueType} from '../services/Data/Data-service';

/**
 * Helps e.g., filtering empty values from an array and keeping array type as non-nillable
 * @param typescript object
 */
export function notEmpty<TValue>(value: TValue | null | undefined): value is TValue {
    return value !== null && value !== undefined;
}
export const round = (value, precision = 0) => {
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

export const formatDate = (input: string | undefined | null) => {
    if ([undefined, null].includes(input)) return null;
    const date = new Date(input);
    if (!Number.isNaN(date.getTime())) {
        return format(date, 'dd.MM.yyyy');
    }
    return null;
};

export const kyselyNameGenerator = (
    kysymysryhma: KyselyType,
    pvm: Date | null | undefined,
    toimipaikka: ArvoOppilaitos | null | undefined,
    nameExtender: number | null | undefined,
): TextType => {
    const pvmOrNull = pvm && `${pvm.getMonth() + 1}/${pvm.getFullYear()}`;
    const extendedName = nameExtender ? `${pvmOrNull}_${nameExtender}` : pvmOrNull;
    return {
        fi: [kysymysryhma.topic.fi, extendedName, toimipaikka?.nimi_fi]
            .filter(notEmpty)
            .join(' '),
        sv: [kysymysryhma.topic.sv, extendedName, toimipaikka?.nimi_sv]
            .filter(notEmpty)
            .join(' '),
    };
};

export const convertOppilaitos = (oppilaitos: Oppilaitos): ArvoOppilaitos => ({
    nimi_fi: oppilaitos.oppilaitos_fi,
    nimi_sv: oppilaitos.oppilaitos_sv,
    nimi_en: oppilaitos.oppilaitos_en,
    oid: oppilaitos.oppilaitos_oid,
    koulutustoimija: '',
});

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
            case InputTypes.checkbox: {
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
                console.log(`Error! Invalid kysymysType: ${kysymys.inputType}`);
                break;
        }
    }
    return formDefaultValues;
};
