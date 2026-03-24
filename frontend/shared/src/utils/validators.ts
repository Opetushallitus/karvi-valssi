export const isNumeric: RegExp = /^((0?|[1-9]\d*)[.,][0-9]+)$|^(0?|[1-9]\d*)$/i;

// https://github.com/Opetushallitus/varda/blob/oph-public-branch/webapps/varda/validators.py#L16
export const isValidEmail: RegExp =
    /^[_A-Za-z0-9-+!#$%&'*/=?^`{|}~]+(\.[_A-Za-z0-9-+!#$%&'*/=?^`{|}~]+)*@[A-Za-z0-9][A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*(\.[A-Za-z]{2,})$/i; // eslint-disable-line
export const isValidEmailList: RegExp =
    /^([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})([,;\r\n\s]+[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})*[\r\n\s]?$/;

export const isOid: RegExp = /^([0-2])((\.0)|(\.[1-9][0-9]*))*$/gm;

export enum MaxLengths {
    email = 80,
    vastausString = 20000,
    vastausJatkokysymys = 5000,
    lahetysFormMessage = 5000,
    resultField = 20000,
    summaryField = 20000,
    default = 100000,
}
